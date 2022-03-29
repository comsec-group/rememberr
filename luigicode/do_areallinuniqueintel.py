# Check that all Intel errata titles are in the file regrouping unique Intel errata.

import luigi

from pipeline.sanitycheck.areallinuniqueintel import AreAllIUniqueIntel

if __name__ == '__main__':
    num_workers = 1

    luigi.build([AreAllIUniqueIntel()], workers=num_workers, local_scheduler=True, log_level='INFO')
