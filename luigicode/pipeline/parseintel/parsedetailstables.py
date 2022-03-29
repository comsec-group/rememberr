# Converts the PDFs to TXT.

from collections import defaultdict
import camelot
import itertools
import json
import luigi
import os
import pprint
import re
import shutil

from pipeline.convertpdf import ConvertPDF
from common import details_pages, cpu_prefixes, is_erratum_removed

#####
# Luigi task
#####

class ParseDetailsTables(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsTables, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_details.json'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        return [ConvertPDF(cpu_name=self.cpu_name)]

    def run(self):
        # These documents are typically manually parsed to treat small table parts that are split across 2 pages.
        candidate_path = os.path.join(os.environ["ERRATA_BUILDDIR"], 'manual_parsefix', "{}_details.json".format(self.cpu_name))
        if os.path.exists(candidate_path):
            with self.output().temporary_path() as outfile_path:
                shutil.copyfile(candidate_path, outfile_path)
                return
        print("[{}] Warning: errata document may require manual parsing. It was not found here: `{}`.".format(self.cpu_name, candidate_path))

        tables = camelot.read_pdf(self.input()[0].path, pages="{}-{}".format(details_pages[self.cpu_name][0], details_pages[self.cpu_name][1]))

        ################
        # Convert tables to lists of pairs (type e.g workaround, text)
        ################

        table_data = map(lambda t: list(t.data), tables)
        table_pairs = list(itertools.chain.from_iterable(table_data))

        ################
        # Treat each erratum independently.
        ################
        # Warn and overwrite if two errata have the same name.
        # Check that all pairs have a left string that is in (prefix+"\d\d\d", "problem", "implication", "workaround", "status")

        # errata_details["AAJ001"]["workaround"] = <workaround>
        errata_details = defaultdict(lambda : defaultdict(str))
        curr_datatype = None # can be None, "title", "problem", "implication", "workaround" or "status".
        curr_erratumkey = None # For example AAJ001
        for left_elem, right_elem in table_pairs:
            left_elem = left_elem.strip()
            right_elem = right_elem.strip()
            # Check if the line starts a new erratum
            eratumname_match = re.match(cpu_prefixes[self.cpu_name]+r"(\d{3})", left_elem)
            if eratumname_match is not None:
                curr_datatype = "title"
                curr_erratumnum = int(eratumname_match.group(1))
                curr_erratumkey = cpu_prefixes[self.cpu_name]+f"{curr_erratumnum:03}"
                # Sanity check: we check that the erratum name was not already used. If it was, then we first clear it (because AAJ143 for example).
                if curr_erratumkey in errata_details:
                    print("Warning: Erratum already exists and will be overwritten: {}".format(curr_erratumkey))
                    errata_details[curr_erratumkey] = defaultdict(str)
                errata_details[curr_erratumkey][curr_datatype] += right_elem
            elif "problem" in left_elem.lower():
                if curr_datatype == "problem":
                    print("Warning: erratum {} has two `problem` rows.".format(curr_erratumkey))
                elif curr_datatype != "title":
                    raise ValueError("`Problem` should come after `title` or `problem`. In erratum {}, it came afted `{}`.".format(curr_erratumkey, curr_datatype))
                curr_datatype = 'problem'
                errata_details[curr_erratumkey][curr_datatype] += right_elem
            elif "implication" in left_elem.lower():
                if curr_datatype == "implication":
                    print("Warning: erratum {} has two `implication` rows.".format(curr_erratumkey))
                elif curr_datatype != "problem":
                    raise ValueError("`Implication` should come after `problem` or `implication`. In erratum {}, it came afted `{}`.".format(curr_erratumkey, curr_datatype))
                curr_datatype = "implication"
                errata_details[curr_erratumkey][curr_datatype] += right_elem
            elif "workaround" in left_elem.lower():
                if curr_datatype == "workaround":
                    print("Warning: erratum {} has two `workaround` rows.".format(curr_erratumkey))
                elif curr_datatype != "implication":
                    raise ValueError("`Workaround` should come after `implication` or `workaround`. In erratum {}, it came afted `{}`.".format(curr_erratumkey, curr_datatype))
                curr_datatype = "workaround"
                errata_details[curr_erratumkey][curr_datatype] += right_elem
            elif "status" in left_elem.lower():
                if curr_datatype == "status":
                    print("Warning: erratum {} has two `status` rows.".format(curr_erratumkey))
                elif curr_datatype != "workaround":
                    raise ValueError("`Status` should come after `workaround` or `status`. In erratum {}, it came afted `{}`.".format(curr_erratumkey, curr_datatype))
                curr_datatype = "status"
                errata_details[curr_erratumkey][curr_datatype] += right_elem
            else:
                print("Warning: erratum {} has a row without left hand label. I will treat it as `{}`.".format(curr_erratumkey, curr_datatype))
                errata_details[curr_erratumkey][curr_datatype] += " "+right_elem

        ################
        # Remove removed errata from errata details.
        ################

        errata_details = {k: v for k, v in errata_details.items() if not is_erratum_removed(k, v["title"])}

        ################
        # Sanity checks: check that each erratum has exactly the required fields.
        ################

        errata_fields = ("title", "problem", "implication", "workaround", "status")
        # For example, errata_without_some_field["title"] = ["AAJ002", "AAJ108"]
        errata_without_some_field = defaultdict(list)
        # Gather the errata without some fields.
        for erratumkey in errata_details:
            for errata_field in errata_fields:
                if errata_field not in errata_details[erratumkey]:
                    errata_without_some_field[errata_field].append(erratumkey)
        # Print the lists of errata with missing fields.
        for errata_field in errata_without_some_field:
            print("Errata without field `{}`:\n\t".format(errata_field), end="")
            self.pp.pprint(errata_without_some_field[errata_field])

        with self.output().temporary_path() as outfile_path:
            with open(outfile_path, "w") as outfile:
                json.dump(errata_details, outfile, indent=4)
