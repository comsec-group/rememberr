# Produces the plots for the most frequent
# - triggers
# - contexts
# - effects

from collections import defaultdict
import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD
from common import plainify_str, triggers, contexts, effects

#####
# Luigi task
#####

class TrigCtxEff(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(TrigCtxEff, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/trig_ctx_eff_amd.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel(), UniqueAMD()]

    def run(self):
        ########################################
        # Load all the classified data.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            intel_all_unique_errata = json.load(infile)
        intel_all_unique_plaintitles = list(map(lambda x: plainify_str(x['title']), intel_all_unique_errata))
        with open(self.input()[1].path, "r") as infile:
            amd_all_unique_errata = json.load(infile)
        tot_num_unique = len(intel_all_unique_errata) + len(amd_all_unique_errata)

        tnum = len(triggers)
        cnum = len(contexts)
        enum = len(effects)

        # dict[tcat][plaintitle] = {chosen: Bool, is_human: Bool}
        tdata = {}
        cdata = {}
        edata = {}

        # dict[trigger_cat][errnum] = dict['chosen' or 'human']
        intel_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json')) as f:
            intel_data = json.load(f)
        for errid in intel_data:
            for cat in intel_data[errid]:
                intel_dicts[cat][errid]['human'] = intel_data[errid][cat]['human']
                intel_dicts[cat][errid]['chosen'] = intel_data[errid][cat]['chosen']
        amd_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_amd.json')) as f:
            amd_data = json.load(f)
        for errid in amd_data:
            for cat in amd_data[errid]:
                amd_dicts[cat][errid]['human'] = amd_data[errid][cat]['human']
                amd_dicts[cat][errid]['chosen'] = amd_data[errid][cat]['chosen']

        # Triggers
        for cat in triggers:
            tdata[cat] = intel_dicts[cat].copy()
            tdata[cat].update(amd_dicts[cat].copy())
        # Contexts
        for cat in contexts:
            cdata[cat] = intel_dicts[cat].copy()
            cdata[cat].update(amd_dicts[cat].copy())
        # Effects
        for cat in effects:
            edata[cat] = intel_dicts[cat].copy()
            edata[cat].update(amd_dicts[cat].copy())
        ########################################
        # Remove some duplicates that may have been removed in a later stage.
        ########################################

        for cat in tdata:
            toremove = []
            for errnum in tdata[cat].keys():
                if not errnum.isdigit() and errnum not in intel_all_unique_plaintitles:
                    toremove.append(errnum)
            for errnum in toremove:
                del tdata[cat][errnum]
        for cat in cdata:
            toremove = []
            for errnum in cdata[cat].keys():
                if not errnum.isdigit() and errnum not in intel_all_unique_plaintitles:
                    toremove.append(errnum)
            for errnum in toremove:
                del cdata[cat][errnum]
        for cat in edata:
            toremove = []
            for errnum in edata[cat].keys():
                if not errnum.isdigit() and errnum not in intel_all_unique_plaintitles:
                    toremove.append(errnum)
            for errnum in toremove:
                del edata[cat][errnum]

        ########################################
        # Compute the number of errata positively classified.
        ########################################

        # errid ist nummer for AMD and plaintitle for Intel.
        # dict[errid] = count of 'chosen' == 1
        tnumtrue = {}
        cnumtrue = {}
        enumtrue = {}

        # Triggers
        for cat in triggers:
            numtrue = 0
            for v in tdata[cat].values():
                numtrue += int(v['chosen'])
            tnumtrue[cat] = numtrue    
        # Contexts
        for cat in contexts:
            numtrue = 0
            for v in cdata[cat].values():
                numtrue += int(v['chosen'])
            cnumtrue[cat] = numtrue    
        # Effects
        for cat in effects:
            numtrue = 0
            for v in edata[cat].values():
                numtrue += int(v['chosen'])
            enumtrue[cat] = numtrue    

        ########################################
        # Sort the TCEs.
        ########################################

        tlabels, tvals = zip(*dict(sorted(tnumtrue.items(), key=lambda item: item[1], reverse=True)).items())
        clabels, cvals = zip(*dict(sorted(cnumtrue.items(), key=lambda item: item[1], reverse=True)).items())
        elabels, evals = zip(*dict(sorted(enumtrue.items(), key=lambda item: item[1], reverse=True)).items())

        ########################################
        # Divide by number of errata.
        ########################################

        tvals = list(map(lambda x: round(100*x/tot_num_unique, 1), tvals))
        cvals = list(map(lambda x: round(100*x/tot_num_unique, 1), cvals))
        evals = list(map(lambda x: round(100*x/tot_num_unique, 1), evals))

        self.pp.pprint(tvals)

        ########################################
        # Do the plots.
        ########################################

        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # Triggers
        fig, ax = plt.subplots(figsize=(8, 3))
        interm_bars = ax.bar(range(tnum), tvals)
        # ax.bar_label(interm_bars)
        ax.grid(axis='y')
        ax.set_axisbelow(True)
        ax.set_xticks(np.arange(tnum), step=1)
        ax.set_xticklabels(tlabels, rotation=90)
        ax.set_ylabel('Affected errata (%)')
        fig.tight_layout()
        # Save more figures than what luigi would.
        plt.savefig(os.path.join(target_dir, "triggers.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "triggers.png"), dpi=300)

        # Contexts
        fig, ax = plt.subplots(figsize=(6, 2.5))
        interm_bars = ax.bar(range(cnum), cvals)
        ax.bar_label(interm_bars)
        ax.grid(axis='y')
        ax.set_axisbelow(True)
        ax.set_xticks(np.arange(cnum), step=1)
        ax.set_xticklabels(clabels, rotation=90)
        ax.set_ylabel('Affected errata (%)')
        ax.set_ylim(0, 8.6)
        fig.tight_layout()
        # Save more figures than what luigi would.
        plt.savefig(os.path.join(target_dir, "contexts.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "contexts.png"), dpi=300)

        # Effects
        fig, ax = plt.subplots(figsize=(6, 2.5))
        interm_bars = ax.bar(range(enum), evals)
        ax.bar_label(interm_bars)
        ax.grid(axis='y')
        ax.set_axisbelow(True)
        ax.set_xticks(np.arange(enum), step=1)
        ax.set_xticklabels(elabels, rotation=90)
        ax.set_ylabel('Affected errata (%)')
        ax.set_ylim(0, 23.5)
        fig.tight_layout()
        # Save more figures than what luigi would.
        plt.savefig(os.path.join(target_dir, "effects.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "effects.png"), dpi=300)
