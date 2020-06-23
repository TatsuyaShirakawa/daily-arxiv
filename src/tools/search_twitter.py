import argparse
from pathlib import Path
import json
import time
from loguru import logger
from tqdm import tqdm
import twint
from joblib import Parallel, delayed


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
    parser.add_argument('-i', '--input_file', type=Path, default='result/papers.json')    
    parser.add_argument('-o', '--output_file', type=Path, default='result/papers_with_tweets.json')
    args = parser.parse_args()
    return args


def main(args):
    
    papers = json.load(open(args.input_file))
    '''
    for paper in papers['papers']:
        paper['tweets'] = search_tweets(paper['id'])
    '''
    ret = Parallel(n_jobs=-1, verbose=10)(
        [delayed(search_tweets)(paper['id']) for paper in papers['papers']]
    )
    for paper, tweets in zip(papers['papers'], ret):
        paper['tweets'] = tweets

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    json.dump(papers, open(args.output_file, 'w'))


if __name__ == '__main__':

    args = parse_args()
    logger.info(args)
    main(args)
