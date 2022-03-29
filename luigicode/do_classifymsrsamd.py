import luigi

from pipeline.classify.classifymsrsamd import ClassifyMSRsAMD

if __name__ == '__main__':
    num_workers = 1

    luigi.build([ClassifyMSRsAMD()], workers=num_workers, local_scheduler=True, log_level='INFO')

