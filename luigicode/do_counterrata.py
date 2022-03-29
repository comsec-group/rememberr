# Check that all Intel errata titles are in the file regrouping unique Intel errata.

import luigi

from pipeline.counterrata import CountErrata

if __name__ == '__main__':
    num_workers = 1

    luigi.build([CountErrata()], workers=num_workers, local_scheduler=True, log_level='INFO')
