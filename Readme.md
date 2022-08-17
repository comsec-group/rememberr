**This repository hosts the artifacts for the MICRO '22 publication: RemembERR - Leveraging Microprocessor Errata for Improving Design Testing and Validation.**

# RemembERR

RemembERR is a database that contains and classifies microprocessor erratas from all Intel Core generations and AMD CPU families since 2008.

We propose two ways of executing RemembERR, either with local tool installation, or with Docker.

## Reproducing the results with a local tool installation

### Setup

We recommend using Python 3.7 or a newer version. 

For Ubuntu users, the required apt dependencies can be installed with:

```
sudo apt-get update && apt-get install build-essential libpoppler-cpp-dev build-essential libpoppler-cpp-dev software-properties-common python3.8-dev libgl1 libglib2.0-0 software-properties-common git -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update && apt-get install python3.8 python3-pip python3-distutils python3-apt -y
```

Our scripts rely on some Python3 packages. To avoid version conflicts with already installed packages, we recommend setting up a dedicated virtual environment, for example:

```
python3 -m venv ~/.venv/rememberr
source ~/.venv/rememberr/bin/activate
```

Then, install all required packages by running:

```
python3 -m pip install -r requirements.txt
```

Precise package versions are not strictly necessary but guarantee that the code can be executed as expected.

### Execution

The results from the paper can be reproduced by running the commands below.
The experiments can be run through the following commands:

```
bash do_experiments.sh > build/experiments_stdout.log 2> build/experiments_stderr.log
mkdir -p build/logs
cat build/experiments_stdout.log | grep 'Number of Intel' > build/logs/num_errata_intel.log
cat build/experiments_stdout.log | grep 'Number of AMD' > build/logs/num_errata_amd.log
cat build/experiments_stdout.log | grep 'Blurry triggers' > build/logs/num_blurry_triggers.log
```

### Expected results

The expected final content of `build` is:

```
.
├── catalog
│   ├── ...
├── experiments_stderr.log # Intermediate log file, you may ignore it.
├── experiments_stdout.log # Intermediate log file, you may ignore it.
├── figures
│   ├── contexts.pdf
│   ├── contexts.png
│   ├── corrtriggers2d.pdf
│   ├── corrtriggers2d.png
│   ├── cpufix_intel_amd.pdf
│   ├── cpufix_intel_amd.png
│   ├── effects.pdf
│   ├── effects.png
│   ├── heredity_intel.pdf
│   ├── heredity_intel.png
│   ├── msrs_intel_amd.pdf
│   ├── msrs_intel_amd.png
│   ├── numtrigsrequired.pdf
│   ├── numtrigsrequired.png
│   ├── timeline.pdf
│   ├── timeline.png
│   ├── timeline_skylake.pdf
│   ├── timeline_skylake.png
│   ├── triggers.pdf
│   ├── triggers.png
│   ├── triggertimeline_relative.pdf
│   ├── triggertimeline_relative.png
│   ├── workarounds_intel_amd.pdf
│   └── workarounds_intel_amd.png
├── logs
│   ├── num_blurry_triggers.log # Contains a brief numbered result provided in the paper.
│   ├── num_errata_amd.log # Contains a brief numbered result provided in the paper.
│   └── num_errata_intel.log # Contains a brief numbered result provided in the paper.
├── manual_parsefix
│   ├── ...
└── parsed
    ├── ...
```

## Reproducing the results with Docker

Results can be reproduced using Docker.
First, ensure to have make and Docker installed.

Then, run `make`. Results will appear in a new `from-docker` directory, containing all figures, and the evaluated numbers in *.log files.

The expected result is the creation of a `from-docker` directory with the following structure:

```
.
├── figures
│   ├── contexts.png
│   ├── corrtriggers2d.png
│   ├── cpufix_intel_amd.png
│   ├── effects.png
│   ├── heredity_intel.png
│   ├── msrs_intel_amd.png
│   ├── numtrigsrequired.png
│   ├── timeline.png
│   ├── timeline_skylake.png
│   ├── triggers.png
│   ├── triggertimeline_relative.png
│   └── workarounds_intel_amd.png
└── logs
    ├── num_blurry_triggers.log
    ├── num_errata_amd.log
    └── num_errata_intel.log
```
## Customization

To help customization, we provide an example query script that prints all titles of errata triggered by power level changes.
The implementation is located in `luigicode/example/examplequery.py` and the query can be launched by typing:

```
cd luigicode && python3 do_query.py && cd ..
```

## Debugging

The code in this repository relies on the Luigi framework. In general, messages indicating `This progress looks :)` indicate success, and messages indicating `This progress looks :(` indicate failure.

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
│   ├── history: history of the agreements between the two human classifiers.
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
