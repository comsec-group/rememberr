import luigi

from pipeline.classify.plotnumtrigsrequired import NumTrigsRequired 

if __name__ == '__main__':
    num_workers = 1

    luigi.build([NumTrigsRequired()], workers=num_workers, local_scheduler=True, log_level='INFO')
