import config
import sys
from loguru import logger
from arxiv_crawler import arxiv_crawl
import datetime
import os
if __name__ == '__main__':
    os.system("mkdir -p ./content")
    arxiv_crawl()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    os.system(f"mkdir -p ./content/{date}")
    for sub_type in config.ARXIV_LIST['types']:
        # copy file as backup
        os.system(f"cp ./content/{sub_type[3:]}.db ./content/{date}/{sub_type[3:]}.db")