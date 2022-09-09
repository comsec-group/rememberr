# This script determines the percentage of decisions that are made automatically by filtering in or out.

import luigi
import os

from pipeline.classify.filterpercentages import FilterPercentages

num_workers = 1
do_dim = True

luigi.build([FilterPercentages(
)], workers=num_workers, local_scheduler=True, log_level='INFO')
