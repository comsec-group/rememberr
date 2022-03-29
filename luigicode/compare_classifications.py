# This script permits to compare the classifications made by the two users.

from collections import defaultdict
from colorama import Fore, Style
import json
import os
import re
import readchar
from pathlib import Path
import pprint

from common import plainify_str

pp = pprint.PrettyPrinter(indent=4, width=200)

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

# Remove some artifacts in highlighted texts
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

DIM_STR = Style.DIM

HUMAN1 = 'human1'
HUMAN2 = 'human2'

# Do not specify who made the choice if IS_ANONYMOUS is 1
IS_ANONYMOUS = 0
IS_INTEL = os.environ['IS_INTEL'] == '1'

# @brief highlights some predefined words (can be regexes).
# Will dim the rest of the string.
def highlight_words(strin: str, regexes_to_highlight: list) -> str:
    highlighted_str = strin
    for word in regexes_to_highlight:
        highlighted_str = re.sub(word, ansi_escape.sub('', Style.RESET_ALL) + r'\g<0>' + Fore.RESET + DIM_STR, highlighted_str, flags=re.IGNORECASE)
    return highlighted_str


def get_individualclassification_path(is_intel: bool, username: str) -> str:
    if "ERRATA_ROOTDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', username, 'classified_intel.json' if is_intel else 'classified_amd.json')

def get_out_path(is_intel: bool) -> str:
    if "ERRATA_ROOTDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json' if is_intel else 'postagreement_amd.json')

def get_unique_errata_path(is_intel: bool) -> str:
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_BUILDDIR'], 'catalog', "unique_{}.json".format('intel' if is_intel else 'amd'))

# @param erratumid for intel: the plainified title. For AMD: the erratum number.
# @return erratum dict.
def get_unique_erratum(is_intel: bool, erratumid: str, unique_errata_dict: dict) -> dict:
    if is_intel:
        for erratum in unique_errata_dict:
            if plainify_str(erratum['title']) == erratumid:
                return erratum
        raise ValueError("Could not find any match for (Intel) erratum id `{}`.".format(erratumid))
    else:
        for erratum in unique_errata_dict:
            if plainify_str(erratum['errnum']) == erratumid:
                return erratum
        raise ValueError("Could not find any match for (AMD) erratum id `{}`.".format(erratumid))

path1 = get_individualclassification_path(IS_INTEL, HUMAN1)
path2 = get_individualclassification_path(IS_INTEL, HUMAN2)

assert os.path.exists(path1), "Path not found: `{}`.".format(path1)
assert os.path.exists(path2), "Path not found: `{}`.".format(path2)

# Read the decisions of both users.
with open(path1, 'r') as f:
    dict1 = json.load(f)
with open(path2, 'r') as f:
    dict2 = json.load(f)

# Only consider the errata that are completely treated.
dict1_filtered = dict()
for errata_name, categoriesdicts in dict1.items():
    if len(categoriesdicts) == len(categorieslist):
        dict1_filtered[errata_name] = categoriesdicts
dict2_filtered = dict()
for errata_name, categoriesdicts in dict2.items():
    if len(categoriesdicts) == len(categorieslist):
        dict2_filtered[errata_name] = categoriesdicts

# Only consider the intersection of errata.
common_erratanames_list = list()
for erratumname in dict1_filtered:
    if erratumname in dict2_filtered:
        common_erratanames_list.append(erratumname)

# Read the original errata (to display them).
unique_errata_path = get_unique_errata_path(IS_INTEL)
with open(unique_errata_path, 'r') as f:
    unique_errata_dict = json.load(f)

# Pre-compute the number of mismatches.
num_mismatches = 0 # Only for printing purposes.
num_human = 0 # Only for printing purposes.
for curr_erratumname in common_erratanames_list:
    for categoryname in categoriesnames:
        # Check if the response is distinct.
        if dict1[curr_erratumname][categoryname]['chosen'] != dict2[curr_erratumname][categoryname]['chosen']:
            num_mismatches += 1
        if dict1[curr_erratumname][categoryname]['human'] or dict2[curr_erratumname][categoryname]['human']:
            num_human += 1

print(f"Mismatches: {num_mismatches}/{num_human} (over {len(common_erratanames_list)} common errata)")

# Create the outfile if necessary.
outpath = get_out_path(IS_INTEL)
target_dir = os.path.dirname(outpath)
Path(target_dir).mkdir(parents=True, exist_ok=True)

# Check if there was already some work done.
classif = defaultdict(lambda: defaultdict(dict))
if os.path.exists(outpath):
    with open(outpath, "r") as outfile:
        content = outfile.read()
        if content:
            classif = defaultdict(lambda: defaultdict(dict), json.loads(content))

# Do the actual loop work.
curr_mismatch_id = 0 # Only for printing purposes.

for elem in classif:
    for cat in classif[elem]:
        if classif[elem][cat]['human'] and classif[elem][cat]['wasmismatch']:
            curr_mismatch_id += 1

for curr_erratumname in dict1.keys():
    curr_erratum = get_unique_erratum(IS_INTEL, curr_erratumname, unique_errata_dict)
    for categoryname in categoriesnames:

        if (curr_erratumname in classif and categoryname in classif[curr_erratumname]) or curr_erratumname not in common_erratanames_list:
            continue

        if categoryname not in classif[curr_erratumname]:
            classif[curr_erratumname][categoryname] = dict()
        classif[curr_erratumname][categoryname]['human'] = dict1[curr_erratumname][categoryname]['human'] or dict2[curr_erratumname][categoryname]['human']

        # Check if the response is distinct.
        if dict1[curr_erratumname][categoryname]['chosen'] != dict2[curr_erratumname][categoryname]['chosen']:
            classif[curr_erratumname][categoryname]['wasmismatch'] = True
            curr_mismatch_id += 1

            categorycontent = categories[categoryname]

            question                  = categorycontent['question']
            regexes_and_flags_require = categorycontent['regexes_and_flags_require']
            regexes_and_flags_exclude = categorycontent['regexes_and_flags_exclude']
            regexes_and_flags_certain = categorycontent['regexes_and_flags_certain']
            regexes_and_flags_prompt  = categorycontent['regexes_and_flags_prompt']
            regexes_to_highlight      = categorycontent['regexes_to_highlight']

            # Check whether there is some match with the regexes_prompt. In this case, prompt the human.
            matches_with_prompt_regexes = defaultdict(list) # dict[field_type] = list of strings
            for field_type, field_str in curr_erratum.items():
                # matches_with_prompt_regexes = <list_of_matching_substrings>
                for curr_regex, curr_reflags in regexes_and_flags_prompt:
                    curr_matches = re.findall(curr_regex, field_str, flags=curr_reflags)
                    matches_with_prompt_regexes[field_type] += curr_matches

            os.system('clear')
            # highlight_list = curr_import.regexes_and_flags_prompt
            for field_type, field_str in curr_erratum.items():
                # Color the string nicely and print it.
                field_str_colored = DIM_STR + field_str
                for curr_matchstr in matches_with_prompt_regexes[field_type]:
                    field_str_colored = field_str_colored.replace(curr_matchstr, Style.RESET_ALL + curr_matchstr + DIM_STR)
                field_str_colored = highlight_words(field_str_colored, regexes_to_highlight)
                print(Style.RESET_ALL + Fore.GREEN + field_type.capitalize() + Style.RESET_ALL)
                print(field_str_colored)
                print()

            print(" ---- Mismatch {}/{}\n".format(curr_mismatch_id, num_mismatches))

            if not IS_ANONYMOUS:
                print("{}: {}{}".format(Style.RESET_ALL + HUMAN1, (Fore.GREEN + 'yes' + Style.RESET_ALL) if dict1[curr_erratumname][categoryname]['chosen'] else (Fore.RED + 'no' + Style.RESET_ALL), ' (automatically)' if not dict1[curr_erratumname][categoryname]['human'] else ''))
                print("{}: {}{}".format(Style.RESET_ALL + HUMAN2, (Fore.GREEN + 'yes' + Style.RESET_ALL) if dict2[curr_erratumname][categoryname]['chosen'] else (Fore.RED + 'no' + Style.RESET_ALL), ' (automatically)' if not dict2[curr_erratumname][categoryname]['human'] else ''))

            print(Style.RESET_ALL + "\n\n{}[{}]{} {} (y/n/q)".format(Fore.GREEN, categoryname, Style.RESET_ALL, categories[categoryname]['question']))
            while True:
                gotchar = readchar.readchar()
                if gotchar in ('y, n'):
                    classif[curr_erratumname][categoryname]['chosen'] = gotchar == 'y'
                    break
                if gotchar in ('q'):
                    exit(0)

            with open(outpath, "w") as outfile:
                json.dump(classif, outfile, indent=4)

        else:
            classif[curr_erratumname][categoryname]['wasmismatch'] = False
            classif[curr_erratumname][categoryname]['chosen'] = dict1[curr_erratumname][categoryname]['chosen']

with open(outpath, "w") as outfile:
    json.dump(classif, outfile, indent=4)
