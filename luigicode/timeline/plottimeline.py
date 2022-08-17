# Plots the global timeline figure.

from collections import defaultdict
from timeline.timelineutil import strtodate, tupldate_to_int
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

if "ERRATA_BUILDDIR" not in os.environ:
    raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")

intel_cpu_prettynames = {
    "intel_core_1_desktop": "Core 1 (D)",
    "intel_core_1_mobile":  "Core 1 (M)",
    "intel_core_2_desktop": "Core 2 (D)",
    "intel_core_2_mobile":  "Core 2 (M)",
    "intel_core_3_desktop": "Core 3 (D)",
    "intel_core_3_mobile":  "Core 3 (M)",
    "intel_core_4_desktop": "Core 4 (D)",
    "intel_core_4_mobile":  "Core 4 (M)",
    "intel_core_5_desktop": "Core 5 (D)",
    "intel_core_5_mobile":  "Core 5 (M)",
    "intel_core_6":         "Core 6",
    "intel_core_7_8":       "Core 7-8",
    "intel_core_8_9":       "Core 8-9",
    "intel_core_10":        "Core 10",
    "intel_core_11":        "Core 11",
    "intel_core_12":        "Core 12",
}

amd_cpu_prettynames = {
    "amd_10h":    "10h",
    "amd_11h":    "11h",
    "amd_12h":    "12h",
    "amd_14h":    "14h",
    "amd_15h_00": "15h-0",
    "amd_15h_10": "15h-1",
    "amd_15h_30": "15h-3",
    "amd_15h_70": "15h-7",
    "amd_16h_00": "16h-0",
    "amd_16h_30": "16h-3",
    "amd_17h_00": "17h-0",
    "amd_17h_30": "17h-3",
    "amd_19h":    "19h",
}

intel_cpu_names = [
    "intel_core_1_desktop",
    "intel_core_1_mobile",
    "intel_core_2_desktop",
    "intel_core_2_mobile",
    "intel_core_3_desktop",
    "intel_core_3_mobile",
    "intel_core_4_desktop",
    "intel_core_4_mobile",
    "intel_core_5_desktop",
    "intel_core_5_mobile",
    "intel_core_6",
    "intel_core_7_8",
    "intel_core_8_9",
    "intel_core_10",
    "intel_core_11",
    "intel_core_12",
]

amd_cpu_names = [
    "amd_10h",
    "amd_11h",
    "amd_12h",
    "amd_14h",
    "amd_15h_00",
    "amd_15h_10",
    "amd_15h_30",
    "amd_15h_70",
    "amd_16h_00",
    "amd_16h_30",
    "amd_17h_00",
    "amd_17h_30",
    "amd_19h",
]

start_year = 2008

errata_dates_xlsx = '../errata_dates.xlsx'
xl = pd.ExcelFile(errata_dates_xlsx)

# @brief This function will populate ret_timeline with new processor data.
# @param npdf is a numpy matrix that contains the timeline information.
# @return ret_timelines, which is a dict[dateint] = curr_num_errata.
def fill_timelines(npdf):
    # tmp_diffs[strtoint] = diff
    tmp_diffs = defaultdict(int)

    for _, row in npdf.iterrows():
        # print("curr_row:", row['erratum'], row['date'], row['removed'])

        datestr = row['date']
        if datestr and type(datestr) != float:
            tmp_diffs[tupldate_to_int(*strtodate(row['date']))] += 1

        dateremovedstr = row['removed']
        if dateremovedstr and type(dateremovedstr) != float:
            tmp_diffs[tupldate_to_int(*strtodate(row['removed']))] -= 1
    
    # Cumulate
    tmp_cumuls = defaultdict(int)
    sorted_diffs = [(k, v) for k, v in sorted(tmp_diffs.items(), key=lambda dict_item: dict_item[0])]
    curr_cumul = 0
    for new_date, diff in sorted_diffs:
        curr_cumul += diff
        tmp_cumuls[new_date] = curr_cumul
    return tmp_cumuls

def plot_timeline():
    ########################################
    # Intel.
    ########################################

    intel_timelines = dict()

    for cpu_name in intel_cpu_names:
        curr_df = xl.parse(cpu_name)
        intel_timelines[cpu_name] = fill_timelines(curr_df)

    ########################################
    # AMD.
    ########################################

    amd_timelines = dict()

    for cpu_name in amd_cpu_names:
        curr_df = xl.parse(cpu_name)
        amd_timelines[cpu_name] = fill_timelines(curr_df)

    #########################
    # Display the timeline.
    #########################

    # Draw one line per processor
    Xs_intel = []
    Ys_intel = []

    Xs_amd = []
    Ys_amd = []

    # Intel
    for cpu_id, cpu_name in enumerate(intel_cpu_names):
        Xs_intel.append([])
        Ys_intel.append([])
        for dateint in intel_timelines[cpu_name]:
            Xs_intel[cpu_id].append(dateint)
            Ys_intel[cpu_id].append(intel_timelines[cpu_name][dateint])

    # AMD
    for cpu_id, cpu_name in enumerate(amd_cpu_names):
        Xs_amd.append([])
        Ys_amd.append([])
        for dateint in amd_timelines[cpu_name]:
            Xs_amd[cpu_id].append(dateint)
            Ys_amd[cpu_id].append(amd_timelines[cpu_name][dateint])

    AX_INTEL = 0
    AX_AMD   = 1

    fig, axs = plt.subplots(2, 1, figsize=(14, 5), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

    ####
    # Intel axis
    ####

    for cpu_id, cpu_name in enumerate(intel_cpu_names):
        axs[AX_INTEL].plot(Xs_intel[cpu_id], Ys_intel[cpu_id], marker='.', label=intel_cpu_prettynames[cpu_name])
    # Set the X labels
    xtick_locations = []
    for year in range(2008, 2024):
        xtick_locations.append(tupldate_to_int(1, year))
    axs[AX_INTEL].set_xticks(xtick_locations, range(2008, 2024))
    axs[AX_INTEL].set_xlim(-2, xtick_locations[-1])
    axs[AX_INTEL].grid()
    axs[AX_INTEL].legend(loc="lower left", ncol=8)

    ####
    # AMD axis
    ####

    for cpu_id, cpu_name in enumerate(amd_cpu_names):
        axs[AX_AMD].plot(Xs_amd[cpu_id], Ys_amd[cpu_id], marker='.', label=amd_cpu_prettynames[cpu_name])
    # Set the Y ticks
    ytick_locations = np.linspace(0, 100, 5)
    axs[AX_AMD].set_yticks(ytick_locations)
    axs[AX_AMD].grid()
    axs[AX_AMD].legend(loc="upper right", ncol=7)

    plt.xlabel("Disclosure date")
    fig.supylabel('Number of disclosed errata (cumulated)')
    fig.tight_layout()

    plt.savefig(os.path.join(os.environ['ERRATA_BUILDDIR'], 'figures', "timeline.pdf"), dpi=300)
    plt.savefig(os.path.join(os.environ['ERRATA_BUILDDIR'], 'figures', "timeline.png"), dpi=300)
