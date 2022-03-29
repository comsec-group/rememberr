# Converts the PDFs to TXT.

from collections import defaultdict
from operator import index
import json
import luigi
import os
import pdftotext
import pprint
import re

from pipeline.convertpdf import ConvertPDF
from common import details_pages, cpu_prefixes, is_erratum_removed

strings_to_filter_out = {
    "intel_core_1_desktop": [
        "Intel\s*® Core\s*™ i7-900 Desktop Processor Extreme Edition Series",
        "and Intel\s*® Core\s*™ i7-900 Desktop Processor Series",
        "January 2017",
    ],
    "intel_core_1_mobile":  [
        "Intel\s*® Core\s*™ i7-600, i5-500, i5-400, and i3-300 Mobile",
        "Processor Series",
        "September 2015",
    ],
    "intel_core_2_desktop": [
        "2\s*nd Generation Intel\s*® Core\s*™ Processor Family Desktop,",
        "Intel\s*® Pentium\s*® Processor Family Desktop, and Intel\s*®",
        "Celeron\s*® Processor Family Desktop",
        "April 2016",
    ],
    "intel_core_2_mobile":  [
        "2\s*nd Generation Intel\s*® Core\s*™ Processor Family Mobile and",
        "Intel\s*® Celeron\s*® Processor Family Mobile",
        "April 2016",
    ],
    "intel_core_3_desktop": [
        "Desktop 3\s*rd Generation Intel\s*® Core\s*™Processor Family",
        "April 2016",
    ],
    "intel_core_3_mobile":  [
        "Mobile 3\s*rd Generation Intel\s*® Core\s*™Processor Family",
        "April 2016",
    ],
    "intel_core_4_desktop": [
        "Desktop 4\s*th Generation Intel\s*® Core\s*™ Processor Family,",
        "Desktop Intel\s*® Pentium\s*® Processor Family, and Desktop Intel\s*® Celeron\s*® Processor Family",
        "April 2020",
    ],
    "intel_core_4_mobile":  [
        "Mobile 4\s*th Generation Intel\s*® Core\s*™ Processor Family,",
        "Mobile Intel\s*® Pentium\s*® Processor Family, and Mobile Intel\s*® Celeron\s*® Processor Family",
        "April 2020",
    ],
    "intel_core_5_desktop": [
        "Mobile/Desktop 5\s*th Generation Intel\s*® Core\s*™ Processor Family",
        "November 2020",
    ],
    "intel_core_5_mobile":  [
        "5\s*th Generation Intel\s*® Core and M- Processor Families, Mobile Intel\s*® Pentium\s*® and Celeron\s*® Processor Families",
        "May 2020",
    ],

}

# @return True iff keep the line.
def filter_line(cpu_name, line):
    assert cpu_name in strings_to_filter_out, "Unknown CPU name: {}".format(cpu_name)
    line = line.strip()
    if not line:
        return False
    if "Errata" in line or "Document Number" in line:
        return False
    for elem in strings_to_filter_out[cpu_name]:
        if re.search(elem, line) is not None:
            return False
    if re.match(r"^\d\d$", line) is not None:
        return False
    return True

#####
# Luigi task
#####

class ParseDetailsNoTables(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsNoTables, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        return luigi.LocalTarget('{}/parsed/{}_details.json'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        return [ConvertPDF(cpu_name=self.cpu_name)]

    def run(self):
        with open(self.input()[0].path, "rb") as infile:
            pdf = pdftotext.PDF(infile)

        ################
        # Extract, filter and strip the lines
        ################

        all_lines = []
        for page_id in range(details_pages[self.cpu_name][0], details_pages[self.cpu_name][1]+1):
            all_lines += pdf[page_id-1].split('\n')

        # Filter out the lines that are not useful
        filtered_lines = map(lambda s: s.strip(), all_lines)
        filtered_lines = list(filter(lambda l: filter_line(self.cpu_name, l), filtered_lines))
        # Remove the lines after the occurrence of `§§` or `Specification Changes`
        last_index = -1
        for line_id, line in enumerate(filtered_lines):
            if line.strip() in ('§', '§§', 'Specification Changes'):
                last_index = line_id
                break
        if last_index != -1:
            filtered_lines = filtered_lines[:last_index]

        ################
        # Fix the double-status problem, and empty workarounds or statuses.
        ################

        # Fix the double-status problem, if both have non-empty content.
        for line_id in range(len(filtered_lines)-1):
            if len(filtered_lines[line_id]) >= 7 and len(filtered_lines[line_id+1]) >= 7 and filtered_lines[line_id][:7] == "Status:" and filtered_lines[line_id+1][:7] == "Status:": # len("Status:") = 7
                # Check that both status are non-empty.
                # if re.match("\s*$", filtered_lines[line_id][:7]) is None and re.match("\s*$", filtered_lines[line_id+1][:7]) is None:
                if filtered_lines[line_id][7:].strip() and filtered_lines[line_id+1][7:].strip():
                    filtered_lines[line_id] = filtered_lines[line_id].replace("Status", "Workaround", 1)
                    print("Fixed double status for line", line_id)
                    print("\t", filtered_lines[line_id])

        # Remove empty workarounds and statuses.
        filtered_lines = list(filter(lambda x: x.strip() != "Workaround:" and x.strip() != "Status:", filtered_lines))
        # Remove duplicate statuses or workarounds. (a) check that the workaround or status is not empty, and then check if the next is the same
        indices_to_remove = []
        for line_id in range(len(filtered_lines)-1):
            if (
                (len(filtered_lines[line_id]) >= 7 and filtered_lines[line_id][:7] == "Status:" and filtered_lines[line_id] == filtered_lines[line_id+1])
                or (len(filtered_lines[line_id]) >= 11 and filtered_lines[line_id][:11] == "Workaround:" and filtered_lines[line_id] == filtered_lines[line_id+1])
            ):
                indices_to_remove.append(line_id)
        # From https://stackoverflow.com/questions/11303225/how-to-remove-multiple-indexes-from-a-list-at-the-same-time
        for index_to_remove in sorted(indices_to_remove, reverse=True):
            del filtered_lines[index_to_remove]

        ################
        # Treat each erratum independently.
        ################
        # Warn and overwrite if two errata have the same name.

        # errata_details["AAJ001"]["workaround"] = <workaround>
        errata_details = defaultdict(lambda : defaultdict(str))
        curr_datatype = None # can be None, "title", "problem", "implication", "workaround" or "status".
        curr_erratumkey = None # For example AAJ001
        for line_id, line in enumerate(filtered_lines):
            line = line.strip()
            # Check if the line starts a new erratum
            eratumname_match = re.match(cpu_prefixes[self.cpu_name]+r"(\d+)\.", line)
            if eratumname_match is not None:
                curr_datatype = "title"
                curr_erratumnum = int(eratumname_match.group(1))
                curr_erratumkey = cpu_prefixes[self.cpu_name]+f"{curr_erratumnum:03}"
                # Sanity check: we check that the erratum name was not already used. If it was, then we first clear it (because AAJ143 for example).
                if curr_erratumkey in errata_details:
                    print("Warning: Erratum already exists and will be overwritten: {}".format(curr_erratumkey))
                    errata_details[curr_erratumkey] = defaultdict(str)
                errata_details[curr_erratumkey][curr_datatype] += line[len(eratumname_match.group(0)):].strip()
            elif len(line) >= 8 and line[:8] == "Problem:":
                curr_datatype = "problem"
                errata_details[curr_erratumkey][curr_datatype] += line[8:].strip()
            elif len(line) >= 12 and line[:12] == "Implication:":
                # Filter bug from HSM187 that requires special formatting care.
                if curr_datatype == "implication" and re.match("implication\s*:\s*none\s*identified\s*\.?", line.lower()) is not None:
                    print("Warning: Fixed workaround<-implication problem in {}.".format(curr_erratumkey))
                    curr_datatype = "workaround"
                    errata_details[curr_erratumkey][curr_datatype] += line[12:].strip()
                else:
                    curr_datatype = "implication"
                    errata_details[curr_erratumkey][curr_datatype] += line[12:].strip()
            elif len(line) >= 11 and line[:11] == "Workaround:":
                # Filter bug from HSM187 that requires special formatting care.
                if curr_datatype == "workaround" and re.match("workaround\s*:\s*for\s+the\s+steppings\s+affected\s*,\s*see\s+the\.?", line.lower()) is not None:
                    print("Warning: Fixed status<-workaround problem in {}.".format(curr_erratumkey))
                    curr_datatype = "status"
                    errata_details[curr_erratumkey][curr_datatype] += line[11:].strip()
                else:
                    curr_datatype = "workaround"
                    errata_details[curr_erratumkey][curr_datatype] += line[11:].strip()
            elif len(line) >= 7 and line[:7] == "Status:":
                if curr_datatype == "title":
                    # For BU115 for example
                    curr_datatype = "problem"
                    errata_details[curr_erratumkey][curr_datatype] += line[7:].strip()
                    print("Warning: replaced `Status:` label with `Problem:` in erratum {}.")
                else:
                    curr_datatype = "status"
                    errata_details[curr_erratumkey][curr_datatype] += line[7:].strip()
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line.strip()

        ################
        # Remove removed errata from errata details.
        ################

        errata_details = {k: v for k, v in errata_details.items() if not is_erratum_removed(k, v["title"])}

        ################
        # Ad-hoc fixes.
        ################

        if self.cpu_name == 'intel_core_1_mobile':
            # AAT072
            errata_details['AAT072']['title'] = 'An Unexpected Page Fault or EPT Violation May Occur After Another Logical Processor Creates a Valid Translation for a Page'
            errata_details['AAT072']['problem'] = 'An Unexpected Page Fault or EPT Violation May Occur After Another Logical Processor Creates a Valid Translation for a Page An unexpected page fault (#PF) or EPT violation may occur for a page under the following conditions: \u2022 The paging structures initially specify no valid translation for the page. \u2022 Software on one logical processor modifies the paging structures so that there is a valid translation for the page (e.g., by setting to 1 the present bit in one of the paging-structure entries used to translate the page). \u2022 Software on another logical processor observes this modification (e.g., by accessing a linear address on the page or by reading the modified paging-structure entry and seeing value 1 for the present bit). \u2022 Shortly thereafter, software on that other logical processor performs a store to a linear address on the page. In this case, the store may cause a page fault or EPT violation that indicates that there is no translation for the page (e.g., with bit 0 clear in the page-fault error code, indicating that the fault was caused by a not-present page). Intel has not observed this erratum with any commercially available software.'

            # AAT122
            errata_details['AAT122']['problem'] += errata_details['AAT122']['implication']
            errata_details['AAT122']['implication'] = '<No field for `implication`>'

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
