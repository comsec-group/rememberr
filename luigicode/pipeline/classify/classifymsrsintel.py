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

from pipeline.uniqueintel import UniqueIntel
from common import plainify_str

INTEL_MSR_REGEX = r'\bMSRs?[A-Z0-9_]*\s*\(?(?:[0-9A-F]+H\s*[\u2013,-]?\s*?)+'

INTEL_MSR_NAMES = {
    r'BR_INST_RETIRED': 'C4',
    r'(?:IA32_)?APERF': 'E8',
    r'(?:IA32_)?A_PMC(?:\d+|\{[\d -]+\}|[a-z])?': '4C4',
    r'(?:IA32_)?BIOS_UPDT_TRIG': '79',
    r'(?:IA32_)?CLOCK_MODULATION': '19A',
    r'(?:IA32_)?CR_MC2_STATUS': '409',
    r'(?:IA32_)?CR_PAT': '277',
    r'(?:IA32_)?DEBUGCTL': '1D9',
    r'(?:IA32_)?EFER': 'C0000080',
    r'(?:IA32_)?ENERGY_PERF_BIAS': '1B0',
    r'(?:IA32_)?EXT_XAPIC_TPR': '808',
    r'(?:IA32_)?FIXED_CTR0': '309',
    r'(?:IA32_)?FIXED_CTR1': '30A',
    r'(?:IA32_)?FIXED_CTR2': '30B',
    r'(?:IA32_)?FIXED_CTR_CTRL': '38D',
    r'(?:IA32_)?HWP_CAPABILITIES': '771',
    r'(?:IA32_)?HWP_STATUS': '777',
    r'(?:IA32_)?MC(?:\d+|\{[\d -]+\}|[a-z])?_STATUS': '401',
    r'(?:IA32_)?MC(?:\d+|\{[\d -]+\}|[a-z])?_ADDR': '402',
    r'(?:IA32_)?MC(?:\d+|\{[\d -]+\}|[a-z])?_CTL\d+': '402',
    r'(?:IA32_)?MCG_STATUS': '17A',
    r'(?:IA32_)?MISC_ENABLE': '1A0',
    r'(?:IA32_)?MPERF': 'E7',
    r'(?:IA32_)?PEBS_ENABLE': '3F1',
    r'(?:IA32_)?PERF_CTL': '199',
    r'(?:IA32_)?PERF_FIXED_CTR_CTRL': '38D',
    r'(?:IA32_)?PERF_GLOBAL_CTRL': '38F',
    r'(?:IA32_)?PERF_GLOBAL_STATUS': '38E',
    r'(?:IA32_)?PERF_GLOBAL_STATUS_SET': '391',
    r'(?:IA32_)?PMC\d+': 'C1',
    r'(?:IA32_)?PREFEVTSEL\d+': '186',
    r'(?:IA32_)?RTIT_CR3_MATCH': '572',
    r'(?:IA32_)?RTIT_CTL': '570',
    r'(?:IA32_)?RTIT_OUTPUT_MASK_PTRS': '561',
    r'(?:IA32_)?RTIT_STATUS': '571',
    r'(?:IA32_)?THERM_STATUS': '19C',
    r'(?:IA32_)?TSC_ADJUST': '3B',
    r'(?:IA32_)?TSC_DEADLINE': '6E0',
    r'(?:IA32_)?VMX_ENTRY_CTLS': '484',
    r'(?:IA32_)?VMX_PROCBASED_CTLS2': '48B',
    r'(?:IA32_)?VMX_VMCS_ENUM': '48A',
    r'MSR_LASTBRANCH_?(?:\d+|\{[\d -]+\}|[a-z])?_FROM_IP': '1DB',
    r'MSR_LASTBRANCH_?(?:\d+|\{[\d -]+\}|[a-z])?_TO_IP': '1DC',
    r'MSR_LASTBRANCH': '680', # Manually inserted
    r'MSR_LASTINT_FROM_IP': '1DD',
    r'MSR_LASTINT_TO_IP': '1DE',
    r'MSR_LER_FROM_LIP': '1DD',
    r'MSR_LER_TO_LIP': '1DE',
    r'MSR_OFFCORE_RSP_0': '1A6',
    r'MSR_OFFCORE_RSP_1': '1A7',
    r'MSR_PERF_GLOBAL_STATUS': '38E',
    r'MSR_PERF_STATUS': '198',
    r'MSR_PP1_ENERGY_STATUS': '641',
    r'MSR_TURBO_RATIO_LIMIT': '1AD',
    r'MSR_UNC_CBO_CONFIG': '396',
    r'MSR_UNC_PERF_FIXED_CTR': '395',
    r'MSR_UNC_PERF_FIXED_CTRL': '394',
    r'MSR_UNC_PERF_GLOBAL_CTRL': '391',
    r'MSR_UNC_PERF_GLOBAL_STATUS': '392',
    r'OFFCORE_RSP_0': '1A6',
    r'PLATFORM_POWER_LIMIT': '615',
    r'RING_PERF_LIMIT_REASONS': '6B1',
    r'TSX_FORCE_ABORT': '10F',
    r'VLW_CAPABILITY': '1F0',
    r'CR\d': 'C00',
    r'\bCS\b': 'C01',
    r'\bDS\b': 'C02',
    r'\bES\b': 'C03',
    r'\bFS\b': 'C04',
    r'\bGS\b': 'C05',
    r'\bSS\b': 'C06',
    r'\bLSL\b': 'C07',
    r'\bTSS\b': 'C08',
    r'\bDR\d\b': 'C09',

}

regexes_to_highlight = ('when', 'if', 'incorrectly', 'erroneously', 'instead')

# done: prompt has been completed successfully, and the other return values should be considered valid.
# quit: quit the application, save the current progress but do not take the other return values into account.
# back: return to the previous prompt and do not take the other return values into accoun.
prompt_retstatuses = ('done', 'quit', 'back')

#####
# Luigi task
#####

class ClassifyMSRsIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(ClassifyMSRsIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)
        self.outpath = '{}/classification/msrs/observable_intel.json'.format(os.environ["ERRATA_ROOTDIR"])

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget(self.outpath+'.dummy', format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel()]

    # @brief highlights some predefined words (can be regexes).
    # Will dim the rest of the string.
    def highlight_words(self, strin: str) -> str:
        highlighted_str = strin
        for word in regexes_to_highlight:
            highlighted_str = re.sub(r'\b'+word+r'\b', Style.RESET_ALL + Fore.YELLOW + r'\g<0>' + Fore.RESET + Style.DIM, highlighted_str, flags=re.IGNORECASE)
        return highlighted_str

    # This is a bit more complex than AMD because Intel specifies MSRs in a slightly messier way.
    # @brief For each occurrence, it prompts the user whether the MSR is corrupted.
    # Strategy: occurrence by occurrence, prompt one at a time, then decapitalize it to see only the next (case-sensitive) occurrence.
    # @param erratum_in that may contain some occurrence of MSRs.
    # @return a tuple containting:
    # - a string describing what is status of the return. Is an element of prompt_retstatuses.
    # - a list of observable MSRs (does not have duplicates), or None.
    # - a boolean indicating whether some decision has been made by a human, or None.
    def prompt_msrs_intel(self, erratum_in: dict):
        ret = []
        is_human = False
        curr_erratum = erratum_in.copy()
        for field_type, field_str in curr_erratum.items():
            if field_type in ('title', 'workaround', 'status'):
                continue
            # Find the next MSR match.
            for curr_msr_re in INTEL_MSR_NAMES:
                # Iterate in the string until all the MSR occurrences are treated.
                while True:
                    msr_match = re.search(curr_msr_re, field_str)
                    if not msr_match:
                        break
                    msr_name = msr_match.group(0)
                    # Skip if the MSR has already been marked as observable.
                    if not curr_msr_re in ret:
                        # Color the string nicely and print it.
                        os.system('clear')
                        field_str_colored = Style.DIM + field_str
                        field_str_colored = re.sub(curr_msr_re, Style.RESET_ALL + r"\g<0>" + Style.DIM, field_str_colored, 1)
                        field_str_colored = self.highlight_words(field_str_colored)
                        print('\n\nIf I observe this MSR, may I see that the bug happened? (y/n/q/z/d)')
                        while True:
                            gotchar = readchar.readchar()
                            if gotchar in ('y, n'):
                                break
                            if gotchar in ('d'):
                                # Print more details
                                os.system('clear')
                                for detail_field_type, detail_field_str in curr_erratum.items():
                                    field_str_colored = Style.DIM + detail_field_str
                                    field_str_colored = re.sub(curr_msr_re, Style.RESET_ALL + r"\g<0>" + Style.DIM, field_str_colored, 1)
                                    field_str_colored = self.highlight_words(field_str_colored)
                                    print("{}:\n\n{}\n\n".format(detail_field_type, field_str_colored))
                                print('\n\nIf I observe this MSR, may I see that the bug happened? (y/n/q/z/d)')
                            if gotchar in ('q'):
                                return 'quit', None, None
                            if gotchar in ('z'):
                                return 'back', None, None
                        if gotchar == 'y':
                            # Regroup MSRs by regex, but do not accumulate (if STATUS_0-7 are touched, then only count once).
                            ret.append(curr_msr_re)
                        is_human = True
                    field_str = field_str.replace(msr_name, msr_name.lower(), 1)
            return 'done', ret, is_human

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            intel_all_unique_errata = json.load(infile)

        ########################################
        # Classify all the errata.
        ########################################

        intel_chosen_classif = defaultdict(dict)

        # Only prompt the errata that were not already evaluated.
        if os.path.exists(self.outpath):
            pass
            with open(self.outpath, "r") as outfile:
                content = outfile.read()
                if content:
                    intel_chosen_classif = defaultdict(dict, json.loads(content))
        else:
            target_dir = os.path.join(os.path.dirname(self.outpath))
            Path(target_dir).mkdir(parents=True, exist_ok=True)

        # This stack is used to go to the previous prompt.
        stack_last_prompts = []

        do_exit = False
        # The external loop serves to go back to the previous prompt.
        while True:
            for erratum in intel_all_unique_errata:
                erratum_plaintitle = plainify_str(erratum['title'])
                # If the erratum was already classified (and read from the json file initially), then skip.
                if erratum_plaintitle in intel_chosen_classif:
                    continue
                prompt_status, ret_list, is_human = self.prompt_msrs_intel(erratum)
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
                        assert last_prompt_name in intel_chosen_classif
                        del intel_chosen_classif[last_prompt_name]
                    break
                elif prompt_status == 'done':
                    intel_chosen_classif[erratum_plaintitle]['chosen'] = ret_list
                    intel_chosen_classif[erratum_plaintitle]['human'] = is_human
                    if is_human:
                        stack_last_prompts.append(erratum_plaintitle)
                else:
                    print("Error: Unimplemented prompt return status: `{}`. Exiting.".format(prompt_status))
                    do_exit = True
                    break

            if len(intel_all_unique_errata) == len(intel_chosen_classif):
                do_exit = True

            with open(self.outpath, "w") as outfile:
                json.dump(intel_chosen_classif, outfile, indent=4)
            if do_exit:
                break
