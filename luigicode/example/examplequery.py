# This Luigi task is provided as an example query.
# Prints the titles of all errata that are triggered by power level changes.

import json
import luigi
import os

from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD
from common import plainify_str

#####
# Luigi task
#####

class ExampleQuery(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(ExampleQuery, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/workarounds_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        # This ensures that the unique Intel and AMD errata are present (under flag conditions in the corresponding tasks), and provides a path to their output JSON files.
        return [UniqueIntel(), UniqueAMD()]

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        # Open the unique errata, which contain the parsed errata fields such as title, problem and workaround, for instance.
        with open(self.input()[0].path, "r") as infile:
            unique_errata_intel = json.load(infile)
        with open(self.input()[1].path, "r") as infile:
            unique_errata_amd = json.load(infile)

        ########################################
        # Get all the classifications.
        ########################################

        # The classification decisions.
        # intel_data and amd_data are represented as: dict[erratum id][category]['chosen'(bool)]
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json')) as f:
            intel_data = json.load(f)
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_amd.json')) as f:
            amd_data = json.load(f)

        # Will contain the titles
        query_titles = []

        # Intel
        # errid is a plain version of the title for Intel, and uniquely identifies the erratum.
        for errid in intel_data:
            # If this data has been classified as triggered by power state changes...
            if intel_data[errid]['trg_POW_pwc']['chosen']:
                # Find the erratum's title in the unique errata.
                for unique_erratum in unique_errata_intel:
                    # Intel errata are identified by plaintitle.
                    if plainify_str(unique_erratum['title']) == errid:
                        query_titles.append(unique_erratum['title'])
        # AMD
        # errid is an explicit number for AMD, and uniquely identifies the erratum.
        for errid in amd_data:
            # If this data has been classified as triggered by power state changes...
            if amd_data[errid]['trg_POW_pwc']['chosen']:
                # Find the erratum's title in the unique errata.
                for unique_erratum in unique_errata_amd:
                    # AMD errata are identified by errnum.
                    if unique_erratum['errnum'] == errid:
                        query_titles.append(unique_erratum['title'])

        # Finally, print all the collected titles.
        for title in query_titles:
            print(title)
