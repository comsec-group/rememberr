## Numbers

Num Intel errata, unique: 743, total: 2057.
Num AMD   errata, unique: 385, total: 506.

## Duplicates

Intel core 1 mobile:

- AAT51 and121: exactly the same (except capital letters).
- AAT108 and122: exactly the same (except one UTF-8 character).

Intel core 4 mobile:

- HSM38 and85: exactly the same, but the second says better how to trigger (using power states).
- HSM117 and131: exactly the same (except a negligible remark on effects).
- HSM134 and141: exactly the same.

Intel core 4 desktop:

- HSD37 and82: exactly the same, but the second says better how to trigger (using power states).
- HSD109 and121: exactly the same (except a negligible remark on effects).
- HSD124 and130: exactly the same.

Intel core 5 desktop:

- BDM48 and54: Exactly the same but very slightly rephrased. As if they re-discovered it.

Intel core 6:

- SKL149 and 151: exactly the same.

Intel core 7_8:

- KBL133 and134: exactly the same, except that one has a BIOS workaround, and the other not.
--> This is because they may affect different models slightly differently.

AMD errata 1327 and 1329 look identical (only the workaround differs). I treated them as distinct because they have distinct identifiers.

## Uniqueness methodology

It is sometimes ambiguous whether two errata are copies, especially for Intel where errata do not have cross-document identifiers.

Method:
- if two errata mention distinct power levels, then do not merge even if the rest of the erratum is identical.
- if two errata are identical except that one of them specifies more triggers, then do not merge.
- if one erratum says *overcount* and another says *overcount or undercount*, then do not merge.

## Dates

intel core 1 mobile
Two different dates for the same action (adding AAT097 for example) (4 errata)

intel core 1 desktop
March 14th , 2011: should be 2012

intel core 5 mobile
Errata BDM130-135 not dated.

intel core 6
Errata SKL152-157 not dated.

intel core 6_7
Two different dates for the same action (adding KBL129-131).


amd_15h_00
- Two different dates for the same action (adding 709).
- Erratum 759 does not appear in the overview table.

## Titles

intel core 2 mobile
BK036: was written FXSTOR instead of FXRSTOR

intel core 6-9
was written Inter PT instead of Intel PT.


## Other errors

intel_core_1_desktop: AAJ143 names tow different bugs. The first of two AAJ143 errata is identical to the last erratum (AAJ168)
intel_core_1_mobile:  AAT122 has no "problem" label displayed.
intel_core_3_desktop: BV16 and BV41 have no "status" field.
intel_core_3_mobile:  BU16 and BU41 have no "status" field. BU115 has "Status:" label instead of "Problem:".
intel_core_4_mobile:  HSM187 has "Implication:" label instead of "Workaround:".
intel_core_6_mobile:  SKL143 was removed because it was a duplicate of SKL139.

Wrong IA32_MC3_STATUS MSR number in erratum `Back to Back Uncorrected Machine Check Errors May Overwrite IA32_MC3_STATUS.MSCOD`
Wrong IA32_PERF_GLOBAL_STATUS in erratum `Performance-Counter Overflow Indication May Cause Undesired Behavior`

Wrong MC6_ADDR, said MSR0000_040A should be MSR0000_041A in `Processor May Alter Machine Check Registers on a Warm Reset`.
