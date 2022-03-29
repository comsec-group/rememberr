# This root script is used to classify errata into triggers, contexts and observable effects.

import luigi
import os

from pipeline.classify.classifygenericbinarybyerrata import ClassifyGenericBinaryByErrata

num_workers = 1
do_dim = True

if "IS_INTEL" not in os.environ:
    raise ValueError("Environment variable IS_INTEL must be defined and must be 0 (AMD) or 1 (Intel).")

luigi.build([ClassifyGenericBinaryByErrata(
    is_intel=os.environ['IS_INTEL'] == '1',
    do_dim=do_dim,
)], workers=num_workers, local_scheduler=True, log_level='INFO')
