# Counts the errata and unique errata for Intel and AMD.

import json
import luigi
import os
import pprint

from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD

intel_errata_docnames = {
    "intel_core_1_desktop",
    "intel_core_1_mobile",
    "intel_core_2_desktop",
    "intel_core_2_mobile",
    "intel_core_3_desktop",
    "intel_core_3_mobile",
    "intel_core_4_desktop",
    "intel_core_4_mobile",
    "intel_core_5_desktop",
    "intel_core_5_mobile",
    "intel_core_6",
    "intel_core_7_8",
    "intel_core_8_9",
    "intel_core_10",
    "intel_core_11",
    "intel_core_12",
}
amd_errata_docnames = [
    "amd_10h",
    "amd_11h",
    "amd_12h",
    "amd_14h",
    "amd_15h_00",
    "amd_15h_10",
    "amd_15h_30",
    "amd_15h_70",
    "amd_16h_00",
    "amd_16h_30",
    "amd_17h_00",
    "amd_17h_30",
    "amd_19h",
]
if "ERRATA_BUILDDIR" not in os.environ:
    raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
intel_errata_docpaths = list(map(lambda docname: os.path.join(os.environ['ERRATA_BUILDDIR'], 'parsed', f"{docname}_details.json"), intel_errata_docnames))
amd_errata_docpaths   = list(map(lambda docname: os.path.join(os.environ['ERRATA_BUILDDIR'], 'parsed', f"{docname}_details.json"), amd_errata_docnames))

#####
# Luigi task
#####

class CountErrata(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(CountErrata, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/workarounds_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel(), UniqueAMD()]

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            num_unique_errata_intel = len(json.load(infile))
        with open(self.input()[1].path, "r") as infile:
            num_unique_errata_amd = len(json.load(infile))

        ########################################
        # Get all the parsed errata.
        ########################################
        num_errata_intel = 0
        num_errata_amd = 0

        for intel_errata_docpath in intel_errata_docpaths:
            with open(intel_errata_docpath, "r") as infile:
                num_errata_intel += len(json.load(infile))
        for amd_errata_docpath in amd_errata_docpaths:
            with open(amd_errata_docpath, "r") as infile:
                num_errata_amd += len(json.load(infile))

        print("Number of Intel errata: {}, unique: {}".format(num_errata_intel, num_unique_errata_intel))
        print("Number of AMD   errata: {}, unique: {}".format(num_errata_amd, num_unique_errata_amd))
