# Prompts based on regexes and asks for manual decisions for the rest.
# This may ask for manual assistance.

from collections import defaultdict
from colorama import Fore, Style
import json

import luigi
import os
from pathlib import Path
import pprint
import re
import readchar

from pipeline.uniqueamd import UniqueAMD
from pipeline.uniqueintel import UniqueIntel

# Remove some artifacts in highlighted texts
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# categories is a dict[str] = dict{
#    - question
#    - regexes_and_flags_require
#    - regexes_and_flags_exclude
#    - regexes_and_flags_certain
#    - regexes_and_flags_prompt
#    - regexes_to_highlight
#
from classifytce.categories import categories
categorieslist = list(categories.items())
categoriesnames = list(map(lambda c: c[0], categorieslist))

from common import plainify_str

# done: prompt has been completed successfully, and the other return values should be considered valid.
# quit: quit the application, save the current progress but do not take the other return values into account.
# back: return to the previous prompt and do not take the other return values into accoun.
prompt_retstatuses = ('done', 'quit', 'back')

#####
# Luigi task
#####

class ClassifyGenericBinaryByErrata(luigi.Task):
    is_intel                    = luigi.BoolParameter() # True: Intel, False: AMDs.
    do_dim                      = luigi.BoolParameter(default=True)

    def __init__(self, *args, **kwargs):
        super(ClassifyGenericBinaryByErrata, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        if "ERRATA_USERNAME" not in os.environ:
            raise ValueError("Environment variable ERRATA_USERNAME must be defined. Who are you?")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)
        if self.is_intel:
            self.outpath = '{}/classification/generic/{}/classified_intel.json'.format(os.environ["ERRATA_ROOTDIR"], os.environ["ERRATA_USERNAME"])
        else:
            self.outpath = '{}/classification/generic/{}/classified_amd.json'.format(os.environ["ERRATA_ROOTDIR"], os.environ["ERRATA_USERNAME"])
        if self.do_dim:
            self.dim_str = Style.DIM # self.dim_str must be in (Style.DIM, "")
        else:
            self.dim_str = ""

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget(self.outpath+'.dummy', format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel(), UniqueAMD()]

    # @brief highlights some predefined words (can be regexes).
    # Will dim the rest of the string.
    def highlight_words(self, strin: str, regexes_to_highlight: list) -> str:
        highlighted_str = strin
        for word in regexes_to_highlight:
            highlighted_str = re.sub(word, ansi_escape.sub('', Style.RESET_ALL) + r'\g<0>' + Fore.RESET + self.dim_str, highlighted_str, flags=re.IGNORECASE)
        return highlighted_str

    # @param classif[erratum_plaintitle]['chosen' or 'human'] = Bool
    def num_autochosen(self, classif):
        ret = 0
        for elem in classif.values():
            ret += int(not elem['human'])
        return ret

    # @brief For each occurrence, it prompts the user whether the erratum falls into the category.
    # Strategy: occurrence by occurrence, prompt one at a time, then decapitalize it to see only the next (case-sensitive) occurrence.
    # @param erratum_in that may contain some occurrence of some regex.
    # @param curr_progress: an empry, partial or complete dict that represents work in progress for the return dict.
    # @param num_already_done  for debug printing only.
    # @param num_total_uniques for debug printing only.
    # @return a pair(str, dict keyed by categories). The string describes what is status of the return. Is an element of prompt_retstatuses.
    # The return dict contains:
    # - a boolean determining whether the erratum falls into the given category, or None.
    # - a boolean indicating whether some decision has been made by a human, or None.
    def check_generic(self, erratum_in: dict, curr_progress: dict, num_already_done: int, num_total_uniques: int):
        curr_erratum = erratum_in.copy()
        ret = curr_progress

        curr_categoryid = len(ret)

        while curr_categoryid < len(categorieslist):
            categoryname, categorycontent = categorieslist[curr_categoryid]
            curr_categoryid += 1

            question                  = categorycontent['question']
            regexes_and_flags_require = categorycontent['regexes_and_flags_require']
            regexes_and_flags_exclude = categorycontent['regexes_and_flags_exclude']
            regexes_and_flags_certain = categorycontent['regexes_and_flags_certain']
            regexes_and_flags_prompt  = categorycontent['regexes_and_flags_prompt']
            regexes_to_highlight      = categorycontent['regexes_to_highlight']

            # Check whether an `exclude` regex matches. In this case, no need to prompt.
            for field_type, field_str in curr_erratum.items():
                if field_type != 'status':
                    for exclude_regex, curr_reflags in regexes_and_flags_exclude:
                        curr_match = re.search(exclude_regex, field_str, flags=curr_reflags)
                        if curr_match:
                            ret[categoryname] = {
                                'chosen': False,
                                'human': False
                            }
                            break
            if categoryname in ret: # If done with this category.
                continue

            # Check whether a `certain` regex matches. In this case, no need to prompt.
            for field_type, field_str in curr_erratum.items():
                if field_type != 'status':
                    for certain_regex, curr_reflags in regexes_and_flags_certain:
                        curr_match = re.search(certain_regex, field_str, flags=curr_reflags)
                        if curr_match:
                            ret[categoryname] = {
                                'chosen': True,
                                'human': False
                            }
                            break
            if categoryname in ret: # If done with this category.
                continue

            # Check whether a `require` regex matches. In none matches, then decide False.
            if regexes_and_flags_require:
                require_matched = False
                for field_type, field_str in curr_erratum.items():
                    if field_type != 'status':
                        for require_regex, curr_reflags in regexes_and_flags_require:
                            curr_match = re.search(require_regex, field_str, flags=curr_reflags)
                            if curr_match:
                                require_matched = True
                                break
                    if require_matched:
                        break
                if not require_matched:
                    ret[categoryname] = {
                        'chosen': False,
                        'human': False
                    }
            if categoryname in ret: # If done with this category.
                continue

            # Check whether there is some match with the regexes_prompt. In this case, prompt the human.
            matches_with_prompt_regexes = defaultdict(list) # dict[field_type] = list of strings
            for field_type, field_str in curr_erratum.items():
                # matches_with_prompt_regexes = <list_of_matching_substrings>
                for curr_regex, curr_reflags in regexes_and_flags_prompt:
                    curr_matches = re.findall(curr_regex, field_str, flags=curr_reflags)
                    matches_with_prompt_regexes[field_type] += curr_matches

            # If there is nothing to prompt for, then move on to the next category.
            has_prompt_match = False
            for field_type in curr_erratum.keys():
                if matches_with_prompt_regexes[field_type]:
                    has_prompt_match = True
                    break
            if not has_prompt_match:
                ret[categoryname] = {
                    'chosen': False,
                    'human': False
                }
                continue

            os.system('clear')

            for field_type, field_str in curr_erratum.items():
                # Color the string nicely and print it.
                field_str_colored = self.dim_str + field_str
                for curr_matchstr in matches_with_prompt_regexes[field_type]:
                    field_str_colored = field_str_colored.replace(curr_matchstr, Style.RESET_ALL + curr_matchstr + self.dim_str)
                field_str_colored = self.highlight_words(field_str_colored, regexes_to_highlight)
                print(Style.RESET_ALL + Fore.GREEN + field_type.capitalize() + Style.RESET_ALL)
                print(field_str_colored)
                print()
            print(Style.RESET_ALL + "\n\n {}[{}]{} {} (y/n/q/z)".format(Fore.GREEN, categoryname, Style.RESET_ALL, question))
            if 'ERRATA_PRINTPROGESS' in os.environ and os.environ['ERRATA_PRINTPROGESS'] == '1':
                print("\n\n\n\n\n\n\n -- Erratum {}/{}".format(num_already_done, num_total_uniques, num_already_done))
            while True:
                gotchar = readchar.readchar()
                if gotchar in ('y, n'):
                    break
                if gotchar in ('q'):
                    return 'quit', None
                if gotchar in ('z'):
                    # Check if this is the first human category.
                    is_curr_first_human = True
                    for tmp_categoryid in range(curr_categoryid-1):
                        if ret[categoriesnames[tmp_categoryid]]['human']:
                            is_curr_first_human = False
                            break
                    # If we want to go back to the previous erratum (because this is the first human category of this erratum).
                    if is_curr_first_human:
                        return 'back', None
                    # Else, we go back in this erratum until we find the previous human category.
                    tmp_categoryid = curr_categoryid - 2
                    # Backtrack until we find a human category for this erratum.
                    while not ret[categoriesnames[tmp_categoryid]]['human']:
                        del ret[categoriesnames[tmp_categoryid]]
                        tmp_categoryid -= 1
                    del ret[categoriesnames[tmp_categoryid]]
                    curr_categoryid = tmp_categoryid
                    break
            if gotchar == 'y':
                ret[categoryname] = {
                    'chosen': True,
                    'human': True
                }
            elif gotchar == 'n':
                ret[categoryname] = {
                    'chosen': False,
                    'human': True
                }
        return 'done', ret

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[1-int(self.is_intel)].path, "r") as infile:
            # all_unique_errata: list of dicts, each representing one erratum.
            all_unique_errata = json.load(infile)
        if self.is_intel:
            plaintitle_list = list(map(lambda erratum: plainify_str(erratum['title']), all_unique_errata))
        else:
            plaintitle_list = list(map(lambda erratum: erratum['errnum'], all_unique_errata))

        ########################################
        # Classify all the errata.
        ########################################

        classif = defaultdict(dict) # dict[erratum_plaintitle][categoryname] = (chosen, human)

        # Only prompt the errata that were not already evaluated.
        if os.path.exists(self.outpath):
            with open(self.outpath, "r") as outfile:
                content = outfile.read()
                if content:
                    classif = defaultdict(dict, json.loads(content))
        else:
            target_dir = os.path.dirname(self.outpath)
            Path(target_dir).mkdir(parents=True, exist_ok=True)

        do_exit = False
        # The external loop serves to go back to the previous prompt.
        while True:

            at_least_one_treated = False
            if not all_unique_errata:
                break

            for erratum_id, erratum in enumerate(all_unique_errata):

                if self.is_intel:
                    erratum_plaintitle = plainify_str(erratum['title'])
                else:
                    erratum_plaintitle = erratum['errnum']

                # If the erratum was already classified (and read from the json file initially), then skip.
                all_categories_present = True
                for categoryname in categoriesnames:
                    if categoryname not in classif[erratum_plaintitle]:
                        all_categories_present = False
                        break
                if all_categories_present:
                    continue

                at_least_one_treated = True

                prompt_status, ret_dict = self.check_generic(erratum, classif[erratum_plaintitle], len(classif), len(all_unique_errata))
                if prompt_status not in prompt_retstatuses:
                    print("Error: Unexpected prompt return status: `{}`. Exiting.".format(prompt_status))
                    do_exit = True
                    break
                elif prompt_status == 'quit':
                    if ret_dict is not None:
                        classif[erratum_plaintitle] = ret_dict
                    print("Exiting.")
                    do_exit = True
                    break
                elif prompt_status == 'back':
                    # Find the last human-treated erratum and delete its last human category.
                    human = False
                    for tmp_erratumid in range(erratum_id-1, -1, -1):
                        for curr_categoryid in range(len(categoriesnames)-1, -1, -1):
                            human = classif[plaintitle_list[tmp_erratumid]][categoriesnames[curr_categoryid]]['human']
                            del classif[plaintitle_list[tmp_erratumid]][categoriesnames[curr_categoryid]]
                            if human:
                                break
                        if human:
                            break
                    break

                elif prompt_status == 'done':
                    classif[erratum_plaintitle] = ret_dict
                else:
                    print("Error: Unimplemented prompt return status: `{}`. Exiting.".format(prompt_status))
                    do_exit = True
                    break

            # Check whether all the entries are classified.
            if len(all_unique_errata) == len(classif):
                are_all_full = True
                for errataname in plaintitle_list:
                    if len(classif[errataname]) == len(categorieslist):
                        are_all_full = False
                        break
                if are_all_full:
                    do_exit = True

            with open(self.outpath, "w") as outfile:
                json.dump(classif, outfile, indent=4)
            if do_exit or not at_least_one_treated:
                break
