# Plots fixedness for Intel and AMD on the same figure.

import luigi

from pipeline.plotfixednessintelamd import FixednessIntelAMD

if __name__ == '__main__':
    num_workers = 1

    luigi.build([FixednessIntelAMD()], workers=num_workers, local_scheduler=True, log_level='INFO')
