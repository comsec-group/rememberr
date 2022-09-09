# Determines the percentage of decisions that are made automatically by filtering in or out.

import json

import luigi
import os
import pprint
import re

from pipeline.uniqueamd import UniqueAMD
from pipeline.uniqueintel import UniqueIntel

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

#####
# Luigi task
#####

class FilterPercentages(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(FilterPercentages, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('dummy.dummy', format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel(), UniqueAMD()]

    def count_num_filtered_in_out(self, errata):
        num_filtered_in = 0
        num_filtered_out = 0
        tot_num_decisions = 0

        for erratum in errata:
            for _, categorycontent in categorieslist:
                tot_num_decisions += 1

                regexes_and_flags_require = categorycontent['regexes_and_flags_require']
                regexes_and_flags_exclude = categorycontent['regexes_and_flags_exclude']
                regexes_and_flags_certain = categorycontent['regexes_and_flags_certain']
                regexes_and_flags_prompt  = categorycontent['regexes_and_flags_prompt']

                go_to_next_cat = False
                # Case of exclusion
                for field_type, field_str in erratum.items():
                    if field_type != 'status':
                        for exclude_regex, curr_reflags in regexes_and_flags_exclude:
                            curr_match = re.search(exclude_regex, field_str, flags=curr_reflags)
                            if curr_match:
                                go_to_next_cat = True
                                num_filtered_out += 1
                                break
                    if go_to_next_cat:
                        break
                if go_to_next_cat:
                    continue

                # Case of certitude
                for field_type, field_str in erratum.items():
                    if field_type != 'status':
                        for exclude_regex, curr_reflags in regexes_and_flags_certain:
                            curr_match = re.search(exclude_regex, field_str, flags=curr_reflags)
                            if curr_match:
                                go_to_next_cat = True
                                num_filtered_in += 1
                                break
                    if go_to_next_cat:
                        break
                if go_to_next_cat:
                    continue

                # Case of no required
                if regexes_and_flags_require:
                    has_required_appeared = False
                    for field_type, field_str in erratum.items():
                        if field_type != 'status':
                            for exclude_regex, curr_reflags in regexes_and_flags_require:
                                curr_match = re.search(exclude_regex, field_str, flags=curr_reflags)
                                if curr_match:
                                    has_required_appeared = True
                                    break
                        if has_required_appeared:
                            break
                    if not has_required_appeared:
                        num_filtered_out += 1
                        continue

                # Case of no prompt
                has_prompt_appeared = False
                for field_type, field_str in erratum.items():
                    if field_type != 'status':
                        for exclude_regex, curr_reflags in regexes_and_flags_prompt:
                            curr_match = re.search(exclude_regex, field_str, flags=curr_reflags)
                            if curr_match:
                                has_prompt_appeared = True
                                break
                    if has_prompt_appeared:
                        break
                if not has_prompt_appeared:
                    num_filtered_out += 1
                    continue
        return num_filtered_in, num_filtered_out, tot_num_decisions

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            # amd_unique_errata: list of dicts, each representing one erratum.
            intel_unique_errata = json.load(infile)
        with open(self.input()[1].path, "r") as infile:
            # intel_unique_errata: list of dicts, each representing one erratum.
            amd_unique_errata = json.load(infile)

        ########################################
        # Classify all the errata.
        ########################################

        intel_num_filtered_in, intel_num_filtered_out, intel_tot_num_decisions = self.count_num_filtered_in_out(intel_unique_errata)
        amd_num_filtered_in, amd_num_filtered_out, amd_tot_num_decisions = self.count_num_filtered_in_out(amd_unique_errata)

        num_filtered_in = amd_num_filtered_in + intel_num_filtered_in
        num_filtered_out = amd_num_filtered_out + intel_num_filtered_out
        tot_num_decisions = amd_tot_num_decisions + intel_tot_num_decisions
        num_manual = tot_num_decisions - num_filtered_out - num_filtered_in

        print(f"tot_num_decisions: {tot_num_decisions}")
        print(f"num_filtered_out:  {num_filtered_out} ({100*num_filtered_out/tot_num_decisions:.1f}%)")
        print(f"num_filtered_in:   {num_filtered_in} ({100*num_filtered_in/tot_num_decisions:.1f}%)")
        print(f"num_manual:        {num_manual} ({100*num_manual/tot_num_decisions:.1f}%)")

