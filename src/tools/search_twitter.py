import argparse
from pathlib import Path
import time
import json
from loguru import logger
from tqdm import tqdm
import twint


def search_tweets(arxiv_id, limit=100):
    tweets = []
    config = twint.Config()
    config.Search = f'url:arxiv url:{arxiv_id}'
    config.limit = limit
    config.Store_object = True
    config.Hide_output = True
    config.Store_object_tweets_list = tweets
    twint.run.Search(config)
    return [vars(tweet) for tweet in tweets]


def parse_args():
    parser = argparse.ArgumentParser('Search Twitter')
    parser.add_argument('-i', '--input_file', type=Path,
                        default='result/papers.json')
    parser.add_argument('-o', '--output_file', type=Path,
                        default='result/papers_with_tweets.json')
    parser.add_argument('-s', '--sleep', type=float,
                        default=0.1)
    args = parser.parse_args()
    return args


def main(args):

    papers = json.load(open(args.input_file))

    for paper in tqdm(papers['papers']):
        paper['tweets'] = search_tweets(paper['id'])
        time.sleep(args.sleep)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    json.dump(papers, open(args.output_file, 'w'))


if __name__ == '__main__':

    args = parse_args()
    logger.info(args)
    main(args)
