# Lists and counts unique errata.

import json
import luigi
import os
import pprint

from pipeline.parsedetailsamd import ParseDetailsAMD
from common import amd_cpu_names, plainify_str

# Autoregen. The True value is deprecated, because some errata are uniqueness-checked by hand
DO_REGEN = False

#####
# Luigi task
#####

class UniqueAMD(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(UniqueAMD, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/catalog/unique_amd.json'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        if DO_REGEN:
            for cpu_name in amd_cpu_names:
                ret.append(ParseDetailsAMD(cpu_name=cpu_name))
        return ret

    def run(self):
        if DO_REGEN:
            num_cpus = len(amd_cpu_names)
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

            already_seen_errnums = set()
            unique_errata = []
            tot_num_errata = 0

            # Create a title set for each cpu.
            for errata_dict in errata_details_allgens:
                for erratum_name, erratum in errata_dict.items():
                    tot_num_errata += 1
                    curr_errnum = plainify_str(erratum_name)

                    if curr_errnum in already_seen_errnums:
                        continue
                    already_seen_errnums.add(curr_errnum)
                    erratum['errnum'] = erratum_name
                    unique_errata.append(erratum)

            print("Num AMD errata, unique: {}, total: {}".format(len(unique_errata), tot_num_errata))

            with self.output().temporary_path() as outfile_path:
                with open(outfile_path, "w") as outfile:
                    json.dump(unique_errata, outfile, indent=4)
