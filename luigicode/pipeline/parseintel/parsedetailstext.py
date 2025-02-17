# Parses Intel documents for a certain type of document.

from collections import defaultdict
from common import cpu_prefixes
import luigi
import os
import json
import pprint
import re

from common import details_pages, cpu_prefixes, is_erratum_removed

def cpuname_to_textpath(cpu_name: str) -> str:
    if 'ntel' in cpu_name:
        return os.path.join('..', 'errata_documents', 'intel', "{}.txt".format(cpu_name))
    else:
        return os.path.join('..', 'errata_documents', 'amd', "{}.txt".format(cpu_name))

#####
# Luigi task
#####

class ParseDetailsText(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsText, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_details.json'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        return []

    def run(self):

        ################
        # Get the clip text
        ################

        curr_cliptxt_path = cpuname_to_textpath(self.cpu_name)
        with open(curr_cliptxt_path, "r") as f:
            cliptxt = f.read()

        ################
        # Extract, filter and strip the lines
        ################

        print(f"Lines in cpu {self.cpu_name}: {len(cliptxt.split('\n'))}")
        all_lines = cliptxt.split('\n')

        print(f"Lines in cpu {self.cpu_name} after filtering: {len(all_lines)}")

        errata_details = defaultdict(lambda : defaultdict(str))

        states = ["NAME", "TITLE", "PROBLEM", "IMPLICATION", "WORKAROUND", "STATUS"]
        state_transition_table = {"NAME": "TITLE", "TITLE": "PROBLEM", "PROBLEM": "IMPLICATION", "IMPLICATION": "WORKAROUND", "WORKAROUND": "STATUS", "STATUS": "NAME"}

        next_state = "NAME"
        erratumkey = None
        for line in all_lines:
            if not line:
                continue
            print(f"Line in cpu {self.cpu_name}: {line}")
            assert line.startswith(f"{next_state}:"), f"Expected line to start with {next_state}, but it is {line}"
            line = line[len(next_state)+1:].strip()

            if next_state == "NAME":
                erratumkey = line
            else:
                assert erratumkey is not None, f"Expected erratumkey to be set, but it is None"
                next_state_lowercase = next_state.lower()
                assert next_state_lowercase not in errata_details[erratumkey], f"Expected {next_state_lowercase} to not be in errata_details[{erratumkey}] yet."
                errata_details[erratumkey][next_state_lowercase] = line

            next_state = state_transition_table[next_state]

        assert next_state == "NAME", f"Expected final next state to be NAME, but it is {next_state}. It looks like the state machine did not terminate in the expected state."

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

