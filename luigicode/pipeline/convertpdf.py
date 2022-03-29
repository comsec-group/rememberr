# Converts the PDFs to a readable format (camelot uses pypdf2 that only supports old PDF formats).
import luigi
import os
from pikepdf import Pdf

def cpuname_to_orig_pdfpath(cpuname):
    if 'intel' in cpuname:
        return os.path.join('..', 'errata_documents', 'intel', cpuname+".pdf")
    else:
        return os.path.join('..', 'errata_documents', 'amd', cpuname+".pdf")

#####
# Luigi task
#####

class ConvertPDF(luigi.Task):
    cpu_name = luigi.Parameter()

    def __init__(self, *args, **kwargs):
        super(ConvertPDF, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")

    def output(self):
        return luigi.LocalTarget('{}/pdfs/{}.pdf'.format(os.environ["ERRATA_BUILDDIR"], self.cpu_name), format=luigi.format.Nop)

    def requires(self):
        return []

    def run(self):
        with self.output().temporary_path() as outfile_path:
            with Pdf.open(cpuname_to_orig_pdfpath(self.cpu_name)) as pdf:
                pdf.save(outfile_path)
