import luigi

from pipeline.classify.classifymsrsintel import ClassifyMSRsIntel

if __name__ == '__main__':
    num_workers = 1

    luigi.build([ClassifyMSRsIntel()], workers=num_workers, local_scheduler=True, log_level='INFO')

