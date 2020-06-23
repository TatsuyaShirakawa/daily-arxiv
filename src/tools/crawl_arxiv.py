import argparse
from pathlib import Path
import json
from loguru import logger
from dx.crawler import Crawler


def parse_args():
    parser = argparse.ArgumentParser('Crawl arXiv')
    parser.add_argument('--targets', nargs='+', default=['cs', 'stat.ML'],
                        type=str)
    parser.add_argument('--from_days_ago', type=int, default=0)
    parser.add_argument('--to_days_ago', type=int, default=0)    
    parser.add_argument('-o', '--output_file', type=Path, default='result/papers.json')
    args = parser.parse_args()
    assert(args.from_days_ago >= args.to_days_ago)
    return args


def main(args):
    logger.info(args)

    crawler = Crawler()
    papers = crawler.crawl_recent(targets=args.targets,
                                  from_days_ago=args.from_days_ago,
                                  to_days_ago=args.to_days_ago
    )
    
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f'saving {str(args.output_file)}')
    json.dump(papers, open(args.output_file, 'w'))
    

if __name__ == '__main__':

    args = parse_args()
    logger.info(args)
    main(args)
