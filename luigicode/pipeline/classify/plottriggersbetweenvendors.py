# Plots the comparison of high-level triggers between vendors.

from collections import defaultdict
import json
import luigi
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD
from common import plainify_str, trigger_classes_map, trigger_classes

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

NUM_TRIGGER_CLASSSES = len(trigger_classes)

# @brief finds the parsed details, given a CPU name.
def cpuname_to_parseddetailspath(cpuname: str) -> str:
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_BUILDDIR'], 'parsed', '{}_details.json'.format(cpuname))

#####
# Luigi task
#####

class PlotTriggerBetweenVendors(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(PlotTriggerBetweenVendors, self).__init__(*args, **kwargs)

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
        # Load the unique errata files. To remove some duplicates that may have been removed in a later stage.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            intel_all_unique_errata = json.load(infile)
        intel_all_unique_plaintitles = list(map(lambda x: plainify_str(x['title']), intel_all_unique_errata))

        ########################################
        # Load all the classified data.
        ########################################

        # Intel
        # dict[trigger_name][errnum] = dict['chosen' or 'human']
        intel_trigger_categorization_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json')) as f:
            intel_data = json.load(f)
        for errid in intel_data:
            for cat in intel_data[errid]:
                intel_trigger_categorization_dicts[cat][errid]['human'] = intel_data[errid][cat]['human']
                intel_trigger_categorization_dicts[cat][errid]['chosen'] = intel_data[errid][cat]['chosen']

        # AMD
        amd_trigger_categorization_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_amd.json')) as f:
            amd_data = json.load(f)
        for errid in amd_data:
            for cat in amd_data[errid]:
                amd_trigger_categorization_dicts[cat][errid]['human'] = amd_data[errid][cat]['human']
                amd_trigger_categorization_dicts[cat][errid]['chosen'] = amd_data[errid][cat]['chosen']

        # Intel
        # dict[trigger_name][errnum] = bool (True iff has this trigger)
        intel_trigger_categorization_bool = defaultdict(dict)
        for trigger_name, triggerdict in intel_trigger_categorization_dicts.items():
            for errnum, smalldict in triggerdict.items():
                if plainify_str(errnum) in intel_all_unique_plaintitles:
                    intel_trigger_categorization_bool[trigger_name][errnum] = smalldict['chosen']
                else:
                    assert(False)
        # AMD
        amd_trigger_categorization_bool = defaultdict(dict)
        for trigger_name, triggerdict in amd_trigger_categorization_dicts.items():
            for errnum, smalldict in triggerdict.items():
                amd_trigger_categorization_bool[trigger_name][errnum] = smalldict['chosen']

        ########################################
        # For each erratum, add up the trigger classes
        ########################################

        num_trgs_per_class_intel = defaultdict(int)
        num_trgs_per_class_amd = defaultdict(int)

        # Intel
        for trigger, erratumdict in intel_trigger_categorization_bool.items():
            # Only look at triggers
            if len(trigger) <= 4 or trigger[:4] != 'trg_':
                continue
            for ischosen in erratumdict.values():
                num_trgs_per_class_intel[trigger_classes_map[trigger]] += int(ischosen)
        # AMD
        for trigger, erratumdict in amd_trigger_categorization_bool.items():
            # Only look at triggers
            if len(trigger) <= 4 or trigger[:4] != 'trg_':
                continue
            for ischosen in erratumdict.values():
                num_trgs_per_class_amd[trigger_classes_map[trigger]] += int(ischosen)
        
        ########################################
        # Plot
        ########################################

        width = 0.1
        spacing = 0.1

        left_offset = spacing

        # Normalize the Y axis
        Ys_intel = []
        Ys_amd = []

        for trg in trigger_classes:
            Ys_intel.append(100*num_trgs_per_class_intel[trg]/sum(num_trgs_per_class_intel.values()))
            Ys_amd.append(100*num_trgs_per_class_amd[trg]/sum(num_trgs_per_class_amd.values()))
        assert len(Ys_intel) == len(Ys_amd)

        # Generate the X axis
        xticks = []

        fig = plt.figure(figsize=(6, 2.5))
        ax = fig.gca()

        for trigger_class_id in range(len(trigger_classes)):
            xticks.append( left_offset + trigger_class_id*(2*width + 2*spacing))

        Xs_intel = [xticks[tick_id] - width/2 for tick_id in range(len(Ys_intel))]
        Xs_amd   = [xticks[tick_id] + width/2 for tick_id in range(len(Ys_amd))]

        ax.grid(axis='y')
        for tick_id in range(len(Ys_intel)):
            ax.bar(Xs_intel[tick_id], Ys_intel[tick_id], width, alpha=1, zorder=3, color='#0071c5', label='Intel' if tick_id == 0 else '')
            ax.bar(Xs_amd[tick_id], Ys_amd[tick_id], width, alpha=1, zorder=3, color='#ED1C24', label='AMD' if tick_id == 0 else '')

        ax.set_ylabel("Trigger occurrences (\%)")
        ax.legend(ncol=4, framealpha=1)

        ax.set_xticks(xticks, trigger_classes, rotation=45)
        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "triggersbetweenvendors.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "triggersbetweenvendors.png"), dpi=300)
