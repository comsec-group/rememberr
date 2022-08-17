# This file provides utility functions to manage timelines.
# It is used to generate Figure 4.

from collections import defaultdict
import pandas as pd

errata_dates_xlsx = '../errata_dates.xlsx'
xl = pd.ExcelFile(errata_dates_xlsx)

start_year = 2008

# Limit fields for sanity-checking provided dates.
MIN_YEAR = 2000
MAX_YEAR = 2023
MIN_MONTH = 1
MAX_MONTH = 12

########################################
# Helper functions.
########################################

# @brief transforms a strdate, for example `8 2013` into (8, 2013), and performs sanity checks.
# @param strdate for example `8 2013`
# @return a tupldate for example (8, 2013)
def strtodate(strdate):
    try:
        ret_tuple = strdate.split(' ')
    except:
        raise ValueError("Invalid date string `{}`.".format(strdate))
    assert len(ret_tuple) == 2, "Invalid date string `{}`.".format(strdate)
    try:
        month_int, year_int = int(ret_tuple[0]), int(ret_tuple[1])
        assert month_int >= MIN_MONTH and month_int <= MAX_MONTH, "Unsupported strdate month: {}".format(month_int)
        assert year_int >= MIN_YEAR and year_int <= MAX_YEAR, "Unsupported strdate year: {}".format(year_int)
    except:
        raise ValueError("Unsupported strdate: {}".format(strdate))
    return month_int, year_int

# @brief transforms a tuple (month_int, year_int) into an integer using the formula. Performs sanity checks.
def tupldate_to_int(month_int, year_int):
    assert month_int >= MIN_MONTH and month_int <= MAX_MONTH, "Unsupported tupldate month: {}".format(month_int)
    assert year_int >= MIN_YEAR and year_int <= MAX_YEAR, "Unsupported tupldate year: {}".format(year_int)
    assert type(month_int) == int
    assert type(year_int) == int
    return 12*(year_int-start_year)+month_int-1

# @brief does the reciprocal function of tupldate_to_int.
# So far, we do not use this function.
def int_to_tupldate(tupldate_int):
    assert type(tupldate_int) == int
    curr_year = (tupldate_int // 12) + start_year
    curr_month = tupldate_int - 12 * (curr_year - start_year) + 1
    assert curr_month >= MIN_MONTH and curr_month <= MAX_MONTH, "Unsupported tupldate month: {}".format(month_int)
    assert curr_year >= MIN_YEAR and curr_year <= MAX_YEAR, "Unsupported tupldate year: {}".format(year_int)
    return curr_month, curr_year

########################################
# Main function.
########################################

# @brief This function generates the timeline for a given CPU, filtering in the errata in errata_names.
# @param cpu_name as given in intel_cpu_names or amd_cpu_names.
# @param errata_names a list of errata names, for example `AAJ001` for Intel, or the erratum number for AMD.
# @return a dictionary with integer representations of dates as an input, and as values the number of errata public at that time.
def fill_timeline_for_cpu(cpu_name: str, errata_names: list):
    # Open the Excel file that contains the timelines.
    curr_df = xl.parse(cpu_name)

    # In tmp_diffs,
    # - the key is an integer representation of a date. 
    # - the value is the number of errata that were added or removed at that date. 
    tmp_diffs = defaultdict(int)

    for _, row in curr_df.iterrows():
        erratumname = row['erratum']
        # To manage the special case 8_9 which names errata differently.
        if type(erratumname) == int:
            erratumname = f"{erratumname:03}"

        # Filter out the current erratum if applicable.
        if errata_names and erratumname not in errata_names:
            continue

        # Check whether errata have been added or removed.
        datestr = row['date']
        if datestr and type(datestr) != float:
            tmp_diffs[tupldate_to_int(*strtodate(row['date']))] += 1
        dateremovedstr = row['removed']
        if dateremovedstr and type(dateremovedstr) != float:
            tmp_diffs[tupldate_to_int(*strtodate(row['removed']))] -= 1
    
    # Cumulate from tmp_diffs to tmp_cumuls.
    tmp_cumuls = defaultdict(int)
    sorted_diffs = [(k, v) for k, v in sorted(tmp_diffs.items(), key=lambda dict_item: dict_item[0])]
    curr_cumul = 0
    for new_date, diff in sorted_diffs:
        curr_cumul += diff
        tmp_cumuls[new_date] = curr_cumul
    return tmp_cumuls
