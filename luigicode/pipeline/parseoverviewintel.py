# Parses the overview section of an errata document.
# Outputs a dict of arrays: dict[errata_name] = row_as_array.

from collections import defaultdict
from common import cpu_prefixes
import camelot
import luigi
import os
import json
import pprint
import re
import unicodedata

from pipeline.convertpdf import ConvertPDF

overview_pages = {
    "intel_core_1_desktop": "10-16",
    "intel_core_1_mobile":  "10-15",
    "intel_core_2_desktop": "10-14",
    "intel_core_2_mobile":  "10-14",
    "intel_core_3_desktop": "9-13",
    "intel_core_3_mobile":  "9-13",
    "intel_core_4_desktop": "10-15",
    "intel_core_4_mobile":  "10-16",
    "intel_core_5_desktop": "8-11",
    "intel_core_5_mobile":  "9-12",
    "intel_core_6":         "9-20",
    "intel_core_7_8":       "16-25",
    "intel_core_8_9":       "12-19",
    "intel_core_10":        "12-19",
    "intel_core_11":        "9-10",
    "intel_core_12":        "10-12",
}

#####
# Luigi task
#####

class ParseOverviewIntel(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseOverviewIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if self.cpu_name not in overview_pages:
            raise ValueError("Unexpected CPU name `{}` absent from the `overview_pages` dictionary keys.".format(self.cpu_name))

        self.experiment_name = "{}".format(self.cpu_name)
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_overview.json'.format(os.environ["ERRATA_BUILDDIR"], self.experiment_name), format=luigi.format.Nop)

    def requires(self):
        return [ConvertPDF(cpu_name=self.cpu_name)]

    def run(self):
        curr_pdf_path = self.input()[0].path
        errata_overview_tables = camelot.read_pdf(curr_pdf_path, pages=overview_pages[self.cpu_name])

        errata_overview_dict = dict()
        
        for table in errata_overview_tables:
            # Remark: some tables may be completely unrelated.
            table_df = table.df

            for _, row in table_df.iterrows():
                # intel_core_8_9 is special because it does not have a design prefix. But it has always 3-digit errata names.
                if self.cpu_name == "intel_core_8_9":
                    is_row_interesting = re.match("\d{3}", row[0]) is not None
                else:
                    is_row_interesting = cpu_prefixes[self.cpu_name] in row[0]
                if is_row_interesting:
                    errata_overview_dict[unicodedata.normalize("NFKD", row[0])] = list(map(lambda s: unicodedata.normalize("NFKD", s.replace("\n", "").strip()), row[1:]))

        # Check that all rows have the same size.
        with self.output().temporary_path() as outfile_path:
            with open(outfile_path, "w") as outfile:
                json.dump(errata_overview_dict, outfile, indent=4)
