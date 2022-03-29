# Multiplexes the parsing of Intel documents.

import luigi
import os
import pprint

from pipeline.parseintel.parsedetailsnotables import ParseDetailsNoTables
from pipeline.parseintel.parsedetailstables import ParseDetailsTables
from pipeline.parseintel.parsedetailsclip import ParseDetailsClip

cpu_names_notables = [
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
]
cpu_names_tables = [
    "intel_core_8_9",
    "intel_core_11",
    "intel_core_12",
]
cpu_names_clip = [
    "intel_core_6",
    "intel_core_7_8",
    "intel_core_10",
]

#####
# Luigi task
#####

class ParseDetailsIntel(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_details.json'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        if self.cpu_name in cpu_names_notables:
            return [ParseDetailsNoTables(cpu_name=self.cpu_name)]
        elif self.cpu_name in cpu_names_tables:
            return [ParseDetailsTables(cpu_name=self.cpu_name)]
        elif self.cpu_name in cpu_names_clip:
            return [ParseDetailsClip(cpu_name=self.cpu_name)]
        else:
            raise ValueError("I do not know how to parse the Intel CPU `{}`.".format(self.cpu_name))

    def run(self):
        # Only multiplexes tasks to its children. Does not produce anything itself.
        pass
