# Lists and counts unique errata.
# After this step, manual involvement is required to filter out more seemingly distinct errata.

from collections import defaultdict
import json
import luigi
import os
import pprint

from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_names, plainify_str

# For debug purposes to see whether 2 errata entries with same title differ.
PRINT_EQUIV_CLASSES = False
# Autoregen. The True value is deprecated, because some errata are uniqueness-checked by hand
DO_REGEN = False

#####
# Luigi task
#####

class UniqueIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(UniqueIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/catalog/unique_intel.json'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        if DO_REGEN:
            for cpu_name in intel_cpu_names:
                ret.append(ParseDetailsIntel(cpu_name=cpu_name))
        return ret

    def run(self):
        if DO_REGEN:
            num_cpus = len(intel_cpu_names)
            ########################################
            # Get all the manufacturer's errata.
            ########################################

            errata_details_allgens = []
            for cpu_id in range(num_cpus):
                with open(self.input()[cpu_id].path, "r") as infile:
                    errata_details_allgens.append(json.load(infile))

            ########################################
            # Build a set of errata.
            ########################################

            already_seen_titles = set()
            unique_errata = []
            tot_num_errata = 0

            # Output equivalence classes, to make sure that the same title is not used for unrelated issues.
            # dict[plaintitle] = [all_equiv_errata], where all_equiv_errata have the same plain title.
            equivalence_classes = defaultdict(list)

            # Create a title set for each cpu.
            for errata_dict in errata_details_allgens:
                for erratum_name, erratum in errata_dict.items():
                    tot_num_errata += 1
                    curr_plain_title = plainify_str(erratum['title'])

                    # equivalence classes (for debug of this script only)
                    if PRINT_EQUIV_CLASSES:
                        if not (equivalence_classes[curr_plain_title] and plainify_str(equivalence_classes[curr_plain_title][0][1]) == plainify_str(erratum['problem'])):
                            print(erratum_name)
                            print(list(erratum.keys()))
                            equivalence_classes[curr_plain_title].append((erratum_name, plainify_str(erratum['problem'])))

                    if curr_plain_title in already_seen_titles:
                        continue
                    already_seen_titles.add(curr_plain_title)
                    unique_errata.append(erratum)

            # equivalence classes (for debug of this script only)
            if PRINT_EQUIV_CLASSES:
                for title, equiv_class in equivalence_classes.items():
                    if len(equiv_class) == 1:
                        continue
                    print ("Equivalence class for plaintitle: `{}`".format(title))
                    for errnum, erratum in equiv_class:
                        print('Errnum:', errnum)
                        print(erratum)
                        print ('---------------------------')
                    print ('\n\n\n\n\n')

            print("Num Intel errata, unique: {}, total: {}".format(len(unique_errata), tot_num_errata))

            with self.output().temporary_path() as outfile_path:
                with open(outfile_path, "w") as outfile:
                    json.dump(unique_errata, outfile, indent=4)
