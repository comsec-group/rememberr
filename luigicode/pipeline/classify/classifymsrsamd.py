# Identifies the MSRs affected by observable effects.
# This may ask for manual assistance.

from collections import defaultdict
from colorama import Fore, Style
import json

import luigi
import numpy as np
import os
from pathlib import Path
import pprint
import re
import readchar

from pipeline.uniqueamd import UniqueAMD
from common import plainify_str

MSR_EQUIV_CLASSES = [
    ['MSR0000_0401', 'MSR0000_0405', 'MSR0000_0409', 'MSR0000_040D', 'MSR0000_0411', 'MSR0000_0415'], # MC status
    ['MSR0000_0402', 'MSR0000_0406', 'MSR0000_040A', 'MSR0000_040E', 'MSR0000_0412', 'MSR0000_0416'], # MC addr
    ['MSR0000_0403', 'MSR0000_0407', 'MSR0000_040B', 'MSR0000_040F', 'MSR0000_0415', 'MSR0000_0417'], # MC misc
]

AMD_MSR_REGEX = r'MSR[0-9A-F]+_?[0-9A-F]+(?:\[[0-9A-F:,]+\])?'
regexes_to_highlight = ('when', 'if', 'incorrectly', 'erroneously', 'instead')

# done: prompt has been completed successfully, and the other return values should be considered valid.
# quit: quit the application, save the current progress but do not take the other return values into account.
# back: return to the previous prompt and do not take the other return values into accoun.
prompt_retstatuses = ('done', 'quit', 'back')

# @brief Some MSRs are packed in, for example in notation MSRC001_020[B,9,7,5,3,1].
# This function takes MSRs and outputs potentially multiple unpacked MSRs if the input was a packed MSR notation.
# @return a list of MSR names.
def unpack_msrs_amd(msr_name: str) -> list:
    if '[' not in msr_name:
        return [msr_name]
    prefix, suffixes = msr_name.split('[')
    if len(prefix) == 12: # == len('MSRXXXX_XXXX'):
        return [prefix]
    suffixes = re.split(r'[,:]', suffixes.split(']')[0])
    return list(map(lambda s: prefix+s, suffixes))

#####
# Luigi task
#####

class ClassifyMSRsAMD(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(ClassifyMSRsAMD, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)
        self.outpath = '{}/classification/msrs/observable_amd.json'.format(os.environ["ERRATA_ROOTDIR"])

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget(self.outpath+'.dummy', format=luigi.format.Nop)

    def requires(self):
        return [UniqueAMD()]
    
    # @brief highlights some predefined words (can be regexes).
    # Will dim the rest of the string.
    def highlight_words(self, strin: str) -> str:
        highlighted_str = strin
        for word in regexes_to_highlight:
            highlighted_str = re.sub(r'\b'+word+r'\b', Style.RESET_ALL + Fore.YELLOW + r'\g<0>' + Fore.RESET + Style.DIM, highlighted_str, flags=re.IGNORECASE)
        return highlighted_str

    # @brief For each occurrence, it prompts the user whether the MSR is corrupted.
    # Strategy: occurrence by occurrence, prompt one at a time, then decapitalize it to see only the next (case-sensitive) occurrence.
    # @param erratum_in that may contain some occurrence of MSRs.
    # @return a tuple containting:
    # - a string describing what is status of the return. Is an element of prompt_retstatuses.
    # - a list of observable MSRs (does not have duplicates), or None.
    # - a boolean indicating whether some decision has been made by a human, or None.
    def prompt_msrs_amd(self, erratum_in: dict):
        ret = []
        is_human = False
        curr_erratum = erratum_in.copy()
        for field_type, field_str in curr_erratum.items():
            if field_type in ('title', 'workaround', 'status'):
                continue
            # Iterate in the string until all the MSR occurrences are treated.
            while True:
                # Find the next MSR match.
                curr_msr_match = re.search(AMD_MSR_REGEX, field_str)
                if curr_msr_match is None:
                    break
                curr_msr = curr_msr_match.group(0)
                # Skip if the MSR has already been marked as observable.
                if not curr_msr in ret:
                    # Color the string nicely and print it.
                    os.system('clear')
                    field_str_colored = Style.DIM + field_str
                    field_str_colored = re.sub(AMD_MSR_REGEX, Style.RESET_ALL + r'\g<0>' + Style.DIM, field_str_colored, count=1)
                    field_str_colored = self.highlight_words(field_str_colored)
                    print(field_str_colored)
                    print('\n\nIf I observe this MSR, may I see that the bug happened? (y/n/q/z)')
                    while True:
                        gotchar = readchar.readchar()
                        if gotchar in ('y, n'):
                            break
                        if gotchar in ('d'):
                            # Print more details
                            os.system('clear')
                            for detail_field_type, detail_field_str in curr_erratum.items():
                                field_str_colored = Style.DIM + detail_field_str
                                field_str_colored = re.sub(AMD_MSR_REGEX, Style.RESET_ALL + r'\g<0>' + Style.DIM, field_str_colored, count=1)
                                field_str_colored = self.highlight_words(field_str_colored)
                                print("{}:\n\n{}\n\n".format(detail_field_type, field_str_colored))
                            print('\n\nIf I observe this MSR, may I see that the bug happened? (y/n/q/z/d)')
                        if gotchar in ('q'):
                            return 'quit', None, None
                        if gotchar in ('z'):
                            return 'back', None, None
                    if gotchar == 'y':
                        ret += unpack_msrs_amd(curr_msr)
                    is_human = True
                field_str = re.sub(AMD_MSR_REGEX, curr_msr.lower(), field_str, count=1)
        return 'done', ret, is_human

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            amd_all_unique_errata = json.load(infile)
        
        ########################################
        # Classify all the errata.
        ########################################

        amd_chosen_classif = defaultdict(dict)

        # Only prompt the errata that were not already evaluated.
        if os.path.exists(self.outpath):
            pass
            with open(self.outpath, "r") as outfile:
                content = outfile.read()
                if content:
                    amd_chosen_classif = defaultdict(dict, json.loads(content))
        else:
            target_dir = os.path.join(os.path.dirname(self.outpath))
            Path(target_dir).mkdir(parents=True, exist_ok=True)

        # This stack is used to go to the previous prompt.
        stack_last_prompts = []

        do_exit = False
        # The external loop serves to go back to the previous prompt.
        while True:
            for erratum in amd_all_unique_errata:
                erratum_plaintitle = plainify_str(erratum['title'])
                # If the erratum was already classified (and read from the json file initially), then skip.
                if erratum_plaintitle in amd_chosen_classif:
                    continue
                prompt_status, ret_list, is_human = self.prompt_msrs_amd(erratum)
                # Replace by representative of the equivalence class.
                for elem_id, elem in enumerate(ret_list):
                    for equiv_class in MSR_EQUIV_CLASSES:
                        if elem in equiv_class:
                            ret_list[elem_id] = equiv_class[0]

                if prompt_status not in prompt_retstatuses:
                    print("Error: Unexpected prompt return status: `{}`. Exiting.".format(prompt_status))
                    do_exit = True
                    break
                elif prompt_status == 'quit':
                    print("Exiting.")
                    do_exit = True
                    break
                elif prompt_status == 'back':
                    # If there are some prompts in stack_last_prompts.
                    if stack_last_prompts:
                        last_prompt_name = stack_last_prompts.pop()
                        assert last_prompt_name in amd_chosen_classif
                        del amd_chosen_classif[last_prompt_name]
                    break
                elif prompt_status == 'done':
                    amd_chosen_classif[erratum_plaintitle]['chosen'] = ret_list
                    amd_chosen_classif[erratum_plaintitle]['human'] = is_human
                    if is_human:
                        stack_last_prompts.append(erratum_plaintitle)
                else:
                    print("Error: Unimplemented prompt return status: `{}`. Exiting.".format(prompt_status))
                    do_exit = True
                    break

            if len(amd_all_unique_errata) == len(amd_chosen_classif):
                do_exit = True

            with open(self.outpath, "w") as outfile:
                json.dump(amd_chosen_classif, outfile, indent=4)
            if do_exit:
                break
