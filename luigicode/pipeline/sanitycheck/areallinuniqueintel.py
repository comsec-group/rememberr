# Used by do_arealluniqueintel.py.
# Checks whether all errata are in the file regrouping unique Intel errata.

import json
import luigi
import os
import pprint

from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_names, plainify_str
from pipeline.uniqueintel import UniqueIntel

#####
# Luigi task
#####

class AreAllIUniqueIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(AreAllIUniqueIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/areallunique.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        for cpu_name in intel_cpu_names:
            ret.append(ParseDetailsIntel(cpu_name=cpu_name))
        return ret + [UniqueIntel()]

    def run(self):
        ########################################
        # Get all the manufacturer's errata.
        ########################################

        errata_details_allgens = dict()
        for cpuid, cpuname in enumerate(intel_cpu_names):
            with open(self.input()[cpuid].path, "r") as infile:
                errata_details_allgens[cpuname] = json.load(infile)

        unique_titles_intel = []
        with open(self.input()[-1].path, "r") as infile:
            unique_titles_intel = list(map(lambda x: plainify_str(x['title']), json.load(infile)))
        
        ########################################
        # For each CPU, look that all titles are in unique_intel.
        ########################################

        for cpuname in intel_cpu_names:
            for errnum, errdict in errata_details_allgens[cpuname].items():
                if not plainify_str(errdict['title']) in unique_titles_intel:
                    print(f"{cpuname} ({errnum}): title not in unique: {errdict['title']}.")
