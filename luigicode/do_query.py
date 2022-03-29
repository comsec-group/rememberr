# This script provides an example query, depending on example/examplequery.py.

import luigi

from example.examplequery import ExampleQuery

if __name__ == '__main__':
    num_workers = 1

    luigi.build([ExampleQuery()], workers=num_workers, local_scheduler=True, log_level='INFO')
