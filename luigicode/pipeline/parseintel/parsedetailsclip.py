# Parses Intel documents for a certain type of document. 

from collections import defaultdict
from common import cpu_prefixes
import luigi
import os
import json
import pprint
import re

from common import details_pages, cpu_prefixes, is_erratum_removed

def cpuname_to_cliptxtpath(cpu_name: str) -> str:
    return os.path.join('..', 'errata_documents', 'clip', "{}.txt".format(cpu_name))

#####
# Luigi task
#####

class ParseDetailsClip(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsClip, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if self.cpu_name not in details_pages:
            raise ValueError("Unexpected CPU name `{}` absent from the `overview_pages` dictionary keys.".format(self.cpu_name))
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_details.json'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        return []

    def run(self):

        ################
        # Get the clip text
        ################
    
        curr_cliptxt_path = cpuname_to_cliptxtpath(self.cpu_name)
        with open(curr_cliptxt_path, "r") as f:
            cliptxt = f.read()

        ################
        # Remove meta-text (such as page numbers)
        ################

        cliptxt = re.sub(r"Specification[\s\n]+Update[\s\n]*\d\d[^\d]", '', cliptxt, flags=re.MULTILINE)
        cliptxt = re.sub(r"[^\d]\d\d[\s\n]*Specification[\s\n]+Update", '', cliptxt, flags=re.MULTILINE)
        cliptxt = re.sub(r"Errata Details", '', cliptxt, flags=re.MULTILINE)
        cliptxt = re.sub(r"3BErrata", '', cliptxt, flags=re.MULTILINE)

        ################
        # Extract, filter and strip the lines
        ################

        all_lines = cliptxt.split('\n')

        # Filter out the lines that are not useful
        filtered_lines = map(lambda s: s.strip(), all_lines)

        ################
        # Treat each erratum independently.
        ################
        # Warn and overwrite if two errata have the same name.
        # We expect the order title->problem->implication->workaround->status

        # errata_details["AAJ001"]["workaround"] = <workaround>
        errata_details = defaultdict(lambda : defaultdict(str))
        curr_datatype = None # can be None, "title", "problem", "implication", "workaround" or "status".
        curr_erratumkey = None # For example AAJ001
        for line_id, line in enumerate(filtered_lines):
            # Check if the line starts a new erratum
            eratumname_match = re.match(cpu_prefixes[self.cpu_name]+r"(\d{3})", line)
            if eratumname_match is not None:
                curr_datatype = "title"
                curr_erratumnum = int(eratumname_match.group(1))
                curr_erratumkey = cpu_prefixes[self.cpu_name]+f"{curr_erratumnum:03}"
                # Sanity check: we check that the erratum name was not already used. If it was, then we first clear it (because AAJ143 for example).
                if curr_erratumkey in errata_details:
                    print("Warning: Erratum already exists and will be overwritten: {}".format(curr_erratumkey))
                    errata_details[curr_erratumkey] = defaultdict(str)
                errata_details[curr_erratumkey][curr_datatype] += line[len(eratumname_match.group(0)):].strip()
            elif curr_datatype == "title" and len(line) >= 7 and line[:7] == "Problem":
                curr_datatype = "problem"
                errata_details[curr_erratumkey][curr_datatype] += line[7:].strip()
            elif curr_datatype == "problem" and len(line) >= 11 and line[:11] == "Implication":
                curr_datatype = "implication"
                errata_details[curr_erratumkey][curr_datatype] += line[11:].strip()
            elif curr_datatype == "implication" and len(line) >= 10 and line[:10] == "Workaround":
                curr_datatype = "workaround"
                errata_details[curr_erratumkey][curr_datatype] += line[10:].strip()
            elif len(line) >= 6 and line[:6] == "Status":
                curr_datatype = "status"
                errata_details[curr_erratumkey][curr_datatype] += line[6:].strip()
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line.strip()

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
