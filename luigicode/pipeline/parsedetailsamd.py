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

re_to_filter_out = [
    r"Revision[\s\n]*Guide[\s\n]*for[\s\n]*AMD[\s\n]*Family",
    r"Product[\s\n]*Errata"
]

# @param prev_erratumkey and prev_datatype: provided in case that an erratum spans over multiple pages.
# @return curr_erratumkey and curr_datatype: for use as previous in the following.
# Replaces errata_details in-place with field erratum_num, and with subfields 'title', 'problem', 'implication', 'workaround' and 'status'.
def parse_page(cpu_name, pdf_text, errata_details, prev_erratumkey, prev_datatype):
    lines = map(lambda s: s.strip(), pdf_text.split('\n'))

    for re_filter in re_to_filter_out:
        lines = list(filter(lambda l: re.search(re_filter, l) is None, lines))
    # Remove empty lines
    lines = list(filter(lambda l: l, lines))

    curr_datatype = None # can be None, "title", "problem", "implication", "workaround" or "status".
    curr_erratumkey = None # For example AAJ001
    for line in lines:
        if curr_datatype is None:
            erratumname_match = re.match(r"(\d{2,})\s*(.*)$", line, re.DOTALL)
            if erratumname_match is None:
                assert prev_erratumkey is not None
                assert prev_datatype is not None
                curr_erratumkey = prev_erratumkey
                curr_datatype = prev_datatype
                # Add the line, hoping that this is not the start of a new section (else, would need to implement a bit more).
                if line.lower() not in ('description', 'potential effect on system', 'suggested workaround', 'fix planned', 'fix'):
                    ValueError("[{}] Erratum `{}` spans over multiple pages, and the new page start `{}` is not yet supported.".format(cpu_name, curr_erratumkey, line))
                errata_details[curr_erratumkey][curr_datatype] += " " + line
                print ("[{}] Info: erratum `{}` spans over multiple pages.".format(cpu_name, curr_erratumkey))
            else:
                curr_erratumkey = erratumname_match.group(1)
                curr_datatype = 'title'
                errata_details[curr_erratumkey][curr_datatype] += erratumname_match.group(2)
        elif curr_datatype == 'title':
            if line.lower() == 'description':
                curr_datatype = 'problem'
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line
        elif curr_datatype == 'problem':
            if line.lower() == 'potential effect on system':
                curr_datatype = 'implication'
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line
        elif curr_datatype == 'implication':
            if 'Suggested Workaround' == line.lstrip()[:len('Suggested Workaround')]:
                curr_datatype = 'workaround'
                line = line[len('suggested workaround '):]
            if line.lower() in ('fix planned', 'fix'):
                curr_datatype = 'status'
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line
        elif curr_datatype == 'workaround':
            if line.lower() in ('fix planned', 'fix'):
                curr_datatype = 'status'
            else:
                errata_details[curr_erratumkey][curr_datatype] += " "+line
        elif curr_datatype == 'status':
            errata_details[curr_erratumkey][curr_datatype] += " "+line
        else:
            raise ValueError("Unrecognized line type of `{}`.".format(line))
    
    # Strip and remove the double spaces
    for k, v in errata_details[curr_erratumkey].items():
        v = v.strip()
        v = re.sub(r"\s+", ' ', v)
        errata_details[curr_erratumkey][k] = v
    
    return curr_erratumkey, curr_datatype

#####
# Luigi task
#####

class ParseDetailsAMD(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ParseDetailsAMD, self).__init__(*args, **kwargs)

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

        errata_details = defaultdict(lambda : defaultdict(str))

        # Extract one erratum per page
        prev_erratumkey = None
        prev_datatype = None
        for page_id in range(details_pages[self.cpu_name][0]-1, details_pages[self.cpu_name][1]):
            prev_erratumkey, prev_datatype = parse_page(self.cpu_name, pdf[page_id], errata_details, prev_erratumkey, prev_datatype)
        
        # self.pp.pprint(errata_details)

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
                    # Artifically populate the field.
                    errata_details[erratumkey][errata_field] = "<No field for `{}`>".format(errata_field)
        # Print the lists of errata with missing fields.
        for errata_field in errata_without_some_field:
            print("[{}] Errata without field `{}`:\n\t".format(self.cpu_name, errata_field), end="")
            self.pp.pprint(errata_without_some_field[errata_field])

        with self.output().temporary_path() as outfile_path:
            with open(outfile_path, "w") as outfile:
                json.dump(errata_details, outfile, indent=4)
