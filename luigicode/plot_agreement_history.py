import json
import os
from pathlib import Path
import subprocess

import matplotlib.pyplot as plt

COMMITS = {
    'intel': [
        '406b70402499321ee3a547c7227bd394ced7f1c1',
        '70d3d8e98a39c2d610d8350a055fa4dca0899247',
        'effbc608fea1c91339198dd56e4268e936908e0b',
        'eea8b8e11ca3efc0411020283db7781d9bd14221',
        '20bf712cfcad0842a7d9bff28d09d0dbd5aff217',
        '6a1bfb8a46c12820b04d4d47f6729446cba2dfb7',
        '9887fcb6ddbb42ce907cf373727d6ce98a477af4',
    ],
    'amd': [
        '326279a20309bce5770a1b7219dd3cdf6390494e',
        '8a656838ec36e5f2736623869b95ba2a85f7ca4d',
        '229f8ddab87ef0cb28be196b10bda67607527fe1',
        '6eba442db2c409e8f1e43ecfbd8dd1caea6c5418',
        '3a5f986bdc35bf3f5afcbb26ee8e6e82a18a97a0',
        '620cacf8f504e54186198ebb18b66f67ff066a7d',
        '22d7ab859ad00d609772151d8652b828024569c4',
    ]
}

if "ERRATA_BUILDDIR" not in os.environ:
    raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
path_to_hostories = os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'history')

##################
# Plot num errata
##################

X_numerrata = dict()
Y_numerrata = dict()

Y_numerrata['intel'] = []
Y_numerrata['amd'] = []
for commit_id in range(len(COMMITS['intel'])):
    with open(os.path.join(path_to_hostories, 'intel', f"postagreement_{'intel'}_{commit_id}.json"), 'r') as f:
        content = json.load(f)
    Y_numerrata['intel'].append(len(content))
for commit_id in range(len(COMMITS['amd'])):
    with open(os.path.join(path_to_hostories, 'amd', f"postagreement_{'amd'}_{commit_id}.json"), 'r') as f:
        content = json.load(f)
    Y_numerrata['amd'].append(len(content))
X_numerrata['intel'] = list(range(len(Y_numerrata['intel'])))
X_numerrata['amd'] = list(range(len(Y_numerrata['amd'])))

fig, ax = plt.subplots(1, 2, figsize=(6, 2.5))

AX = dict()
AX['intel'] = 0
AX['amd']   = 1

ax[AX['intel']].set_ylabel('Number of errata')
ax[AX['intel']].set_xlabel('Step')
ax[AX['intel']].set_ylim(0, Y_numerrata['intel'][-1]*1.1)
ax[AX['intel']].grid()
ax[AX['intel']].plot(X_numerrata['intel'], Y_numerrata['intel'])
ax[AX['intel']].set_title('Intel')
ax[AX['intel']].set_xticks(range(len(X_numerrata['intel'])))
ax[AX['amd']].set_xlabel('Step')
ax[AX['amd']].set_ylim(0, Y_numerrata['amd'][-1]*1.1)
ax[AX['amd']].grid()
ax[AX['amd']].plot(X_numerrata['amd'], Y_numerrata['amd'])
ax[AX['amd']].set_title('AMD')
ax[AX['amd']].set_xticks(range(len(X_numerrata['amd'])))

fig.tight_layout()

target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
Path(target_dir).mkdir(parents=True, exist_ok=True)
plt.savefig(os.path.join(target_dir, "errataperstep.pdf"), dpi=300)
plt.savefig(os.path.join(target_dir, "errataperstep.png"), dpi=300)


##################
# Plot num mismatches
##################

X_numagreements = dict()
Y_numagreements = dict()

Y_numagreements['intel'] = []
Y_numagreements['amd'] = []

NUM_CATEGORIES = 60

for commit_id in range(len(COMMITS['intel'])):
    with open(os.path.join(path_to_hostories, 'intel', f"postagreement_{'intel'}_{commit_id}.json"), 'r') as f:
        content = json.load(f)

    curr_num_agreements = 0
    num_human_cats = 0
    for errid in content:
        if len(content[errid]) < NUM_CATEGORIES:
            break
        for category_content in content[errid].values():
            if category_content['human']:
                curr_num_agreements += 1-int(category_content['wasmismatch'])
                num_human_cats += 1
    # Normalize by the num of errata.
    if commit_id == 0:
        Y_numagreements['intel'].append(100*curr_num_agreements / num_human_cats)
    else:
        Y_numagreements['intel'].append(100*curr_num_agreements / num_human_cats)

for commit_id in range(len(COMMITS['amd'])):
    with open(os.path.join(path_to_hostories, 'amd', f"postagreement_{'amd'}_{commit_id}.json"), 'r') as f:
        content = json.load(f)

    curr_num_agreements = 0
    num_human_cats = 0
    for errid in content:
        if len(content[errid]) < NUM_CATEGORIES:
            break
        for category_content in content[errid].values():
            if category_content['human']:
                curr_num_agreements += 1-int(category_content['wasmismatch'])
                num_human_cats += 1
    # Normalize by the num of errata.
    if commit_id == 0:
        Y_numagreements['amd'].append(100*curr_num_agreements / num_human_cats)
    else:
        Y_numagreements['amd'].append(100*curr_num_agreements / num_human_cats)

X_numagreements['intel'] = list(range(len(Y_numagreements['intel'])))
X_numagreements['amd'] = list(range(len(Y_numagreements['amd'])))

fig, ax = plt.subplots(1, 2, sharey=True, figsize=(6, 2.5))

AX = dict()
AX['intel'] = 0
AX['amd']   = 1

ax[AX['intel']].set_ylabel('Agreements (%)')
ax[AX['intel']].grid()
ax[AX['intel']].plot(X_numagreements['intel'], Y_numagreements['intel'])
ax[AX['intel']].set_title('Intel')
ax[AX['intel']].set_xlabel('Step')
ax[AX['intel']].set_ylim(0, 100)
ax[AX['intel']].set_xticks(range(len(X_numagreements['intel'])))
ax[AX['amd']].grid()
ax[AX['amd']].plot(X_numagreements['amd'], Y_numagreements['amd'])
ax[AX['amd']].set_title('AMD')
ax[AX['amd']].set_xlabel('Step')
ax[AX['amd']].set_ylim(0, 100)
ax[AX['amd']].set_xticks(range(len(X_numagreements['amd'])))

fig.tight_layout()

target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
Path(target_dir).mkdir(parents=True, exist_ok=True)
plt.savefig(os.path.join(target_dir, "agreementstats.pdf"), dpi=300)
plt.savefig(os.path.join(target_dir, "agreementstats.png"), dpi=300)
