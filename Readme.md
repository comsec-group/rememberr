**This repository hosts the artifacts for the MICRO '22 publication: RemembERR - Leveraging Microprocessor Errata for Improving Design Testing and Validation.**

# RemembERR

RemembERR is a database that contains and classifies microprocessor erratas from all Intel Core generations and AMD CPU families since 2008. 

## Setup

Our scripts rely on some Python3 packages. To avoid version conflicts with already installed packages, we recommend setting up a dedicated virtual environment. Then, install all required packages by running:

```
python3 -m pip install -r requirements.txt
```

## Reproducing of the results

The results from the paper can be reproduced by running the commands below.
The commands are mutually independent and can be run in any order, and can alternatively be launched together through `bash do_experiments.sh`.

```
source env.sh

# 1. Count the number of errata and unique errata for Intel and AMD.
cd luigicode && python3 do_counterrata.py | grep 'Number of' && cd ..

# 2. Count the number of errata with explicitly blurry triggers such as 'under complex microarchitectural conditions'.
cd luigicode && python3 do_estimblurtrg.py | grep 'Blurry triggers' && cd ..

# 3. Plot the global timeline of Intel and AMD errata (Figure 2).
cd luigicode && python3 plot_timeline.py && cd ..

# 4. Plot the errata heredity between Intel Core generations (Figure 3).
cd luigicode && python3 plot_heredityintel.py && cd ..

# 5. Plot the timeline of disclosure dates of common errata between Intel Core generations 6 ot 10 (Figure 4).
cd luigicode && python3 plot_commonskylake.py && cd ..

# 6. Plot the statistics on workarounds for Intel and AMD designs (Figure 5).
cd luigicode && python3 plot_workaroundsintelamd.py && cd ..

# 7. Plot the proportion of fixed vs. non-fixed bugs (Figure 6).
cd luigicode && python3 plot_fixednessintelamd.py && cd ..

# 8. Plot the most frequent triggers, contexts and effects (Figures 7, 11 and 12).
cd luigicode && python3 plot_trigctxeff.py && cd ..

# 9. Plot the number of required triggers (Figure 8).
cd luigicode && python3 plot_numtrigsrequired.py && cd ..

# 10. Plot the trigger cross-correlation (Figure 9).
cd luigicode && python3 plot_corrtrigctxteff.py && cd ..

# 11. Plot the trigger class timeline (Figure 10).
cd luigicode && python3 plot_triggertimeline.py && cd ..

# 12. Plot the most frequent MSRs (Figure 13).
cd luigicode && python3 plot_msrs.py && cd ..
```

## Customization

To help customization, we provide an example query script that prints all titles of errata triggered by power level changes.
The implementation is located in `luigicode/example/examplequery.py` and the query can be launched by typing:

```
cd luigicode && python3 do_query.py && cd ..
```

## Repository structure

### build

The `build` directory contains processed data that does not relate to errata classification.
```
.
├── catalog: JSON data sets containing the unique errata for Intel and AMD.
├── figures: Generated figures will appear here.
├── manual_parsefix: JSON data sets for documents that required specific manual effort for correct and accurate parsing. 
└── parsed: JSON data sets containing all the errata. 
```

### classification

The `classification` directory contains data related to errata classification.
```
.
├── generic: contains classification data into trigger, context and observable effect categories.
│   ├── human1: classification performed by the first (human) classifier.
│   ├── human2: classification performed by the second (human) classifier.
│   └── postagreement_intel.json: final classification after discussion and resolution of all mismatches between human1 and human2.
└── msrs: contains classification data regarding observable MSRs.
    ├── observable_amd.json: contains classification data regarding observable MSRs for AMD.
    └── observable_intel.json: contains classification data regarding observable MSRs for Intel.
```

### errata_documents

The `errata_documents` directory contains all considered errata PDF documents used to construct RemembERR.
```
.
├── amd: contains all considered errata PDF documents from AMD used to construct RemembERR.
└── intel: contains all considered errata PDF documents from Intel used to construct RemembERR.
```

### luigicode

The `luigicode` directory contains all the Python code that was used for the parsing and classification, and for generating all the statistics present in the paper.
```
.
├── classifytce: contains Python scripts and Luigi tasks related to errata classification.
├── example: contains an example query script.
├── pipeline: contains Python scripts and Luigi tasks used throughout the work.
├── timeline: contains Python scripts and Luigi tasks related to errata timelines.
└── *.py: python scripts acting as libraries or root jobs.
```

## Classification workflow

Important remark: **making the classification is not part of artifact evaluation** as it is extremely time consuming and requires two humans to complete.

The classification of errata involves a substantial amount of human effort (tens of hours of work), despite conservative assistance of regexes to sort in or out errata for some categories and for assisting classification by highlighting relevant errata excerpts.

The classification is done in two steps:

1. Individual classification: each (human) classifier classifies errata on his/her own.
```
cd luigicode && source ../env.sh
# For human1
ERRATA_USERNAME=human1 IS_INTEL=1 python3 -m classifytce.classify # To classify Intel errata
ERRATA_USERNAME=human1 IS_INTEL=0 python3 -m classifytce.classify # To classify AMD errata
# For human2
#ERRATA_USERNAME=human2 IS_INTEL=1 python3 -m classifytce.classify # To classify Intel errata
#ERRATA_USERNAME=human2 IS_INTEL=0 python3 -m classifytce.classify # To classify AMD errata
```

2. Classification confrontation: the two humans, once they completed their classification, discuss all the mismatches that occurred during their individual classification.
```
cd luigicode && source ../env.sh
IS_INTEL=1 python3 compare_classifications.py # To compare Intel errata classifications
IS_INTEL=0 python3 compare_classifications.py # To compare AMD errata classifications
```
