# Estimates the count of blurry triggers in unique Intel and AMD errata.

import json
import luigi
import os
import re

from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD

candidate_blur_regexes = [
    (r'\bcomplex\b', re.IGNORECASE | re.DOTALL),
    (r'\bdetailed\b', re.IGNORECASE | re.DOTALL),
    (r'\bhighly\b', re.IGNORECASE | re.DOTALL),
    (r'\brare\b', re.IGNORECASE | re.DOTALL),
    (r'\bmicroarchitectural\s*cond', re.IGNORECASE | re.DOTALL),
]

# @param unique_errata a list of errata dicts, each containing keys 'title', 'workaround', etc.
# @return an estimate of the number of errata with blurry triggers.
def estim_classify_blurry(unique_errata: list) -> int:
    estim_blurrycount = 0
    for erratum in unique_errata:
        for fieldname, fieldcontent in erratum.items():
            if fieldname == 'status':
                continue
            for candidateregex, candidateflags in candidate_blur_regexes:
                if re.search(candidateregex, fieldcontent, candidateflags):
                    estim_blurrycount += 1
                    break
            else:
                continue
            break
    return estim_blurrycount

#####
# Luigi task
#####

class EstimateBlurTrg(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(EstimateBlurTrg, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")

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
            intel_unique_errata = json.load(infile)
        with open(self.input()[1].path, "r") as infile:
            amd_unique_errata = json.load(infile)
        
        totcnt_intel = len(intel_unique_errata)
        blrcnt_intel = estim_classify_blurry(intel_unique_errata)
        blrratio_intel = blrcnt_intel/totcnt_intel
        totcnt_amd = len(amd_unique_errata)
        blrcnt_amd = estim_classify_blurry(amd_unique_errata)
        blrratio_amd = blrcnt_amd/totcnt_amd
        
        print("Blurry triggers for Intel: {}/{} ({:.1f}%)".format(blrcnt_intel, totcnt_intel, 100*blrratio_intel))
        print("Blurry triggers for AMD:   {}/{} ({:.1f}%)".format(blrcnt_amd,   totcnt_amd,   100*blrratio_amd))
