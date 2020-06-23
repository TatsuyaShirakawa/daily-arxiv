import re
import time
from tqdm import tqdm
from loguru import logger


def tweet_score(status):
    retweet_count = int(status['retweets_count'])
    favorite_count = int(status['likes_count'])
    return retweet_count + favorite_count


def total_retweet_count(paper):
    return sum([int(tweet['retweets_count']) for tweet in paper['tweets']])


def total_favorite_count(paper):
    return sum([int(tweet['likes_count']) for tweet in paper['tweets']])


def paper_score(paper):
    all_tweets = paper['tweets']
    return sum([tweet_score(tweet) for tweet in all_tweets])
    

class Viewer:

    def __init__(self,
                 favorite_tags=['cs.CV',
                                'cs.CL',
                                'cs.LG',
                                'cs.DS',
                                'cs.IR',
                                'cs.NE',
                                'stat.ML',
                                'cs.AR'],
                 unfavorite_tags=['cs.CR',
                                  'cs.IT',
                                  'cs.LO',
                                  'cs.NI',
                                  'cs.PL',
                                  'cs.RO',
                                  'cs.SE'
                 ],
    ):
        assert(len(set(favorite_tags) & set(unfavorite_tags)) == 0)
        self.favorite_tags = favorite_tags[:]
        self.unfavorite_tags = unfavorite_tags[:]        


    def save_markdown(self, data, result_file, tweet_topk=10):

        metadata = data['meta']
        papers = data['papers']

        r_subject = re.compile(r'.+ \((?P<subject>.+)\)')
        subject_tags = [tuple([r_subject.search(_).group('subject') for _ in p['subjects']]) for p in papers]

        
        def write_paper(paper, fout):
            title = paper['title']
            authors = ', '.join(paper['authors'])
            links = paper['links']
            link_abs = links['Abstract']
            link_pdf = None if not "Download PDF" in links else links['Download PDF']
            subjects = [r_subject.search(_).group('subject')
                        for _ in paper['subjects']]
            abstract = paper["summary"].replace('\n', ' ')
            total_retweet = total_retweet_count(paper)
            total_favorite = total_favorite_count(paper)            

            print(file=fout)
            print(f'### {title}', file=fout)
            print(authors, file=fout)
            print(f'abs: {links["Abstract"]}', file=fout)
            if link_pdf:
                print(f'pdf: {links["Download PDF"]}', file=fout) 
            print(' | '.join(subjects), file=fout)
            print(f'```\n{abstract}\n```', file=fout)
            print(file=fout)
            print(file=fout)
            print(f'total_retweet: {total_retweet},  total_favorite: {total_favorite}', file=fout)

            print(file=fout)
            for status in list(reversed(sorted(paper['tweets'],
                                               key=tweet_score)))[:tweet_topk]:
                user_name = status['name']
                screen_name = status['username']
                created_at = status['datestamp'] + ' ' + status['timestamp']
                retweet_count = int(status['retweets_count'])
                favorite_count = int(status['likes_count'])

                if retweet_count + favorite_count <= 20:
                    continue
                
                print(f'**{user_name} @{screen_name} {created_at}**', file=fout)
                print(file=fout)
                text = status['tweet']
                for line in text.split('\n'):
                    if line.startswith('#'):
                        line = '\\' + line
                    print('>', line, file=fout)
                print(file=fout)
                print(f'**retweets: {retweet_count}    favorites: {favorite_count}**', file=fout)
                print(file=fout)
                print(file=fout)                    
                
            print(file=fout)
            print(file=fout)                

        tags = []
        for paper in papers:
            tags.append([r_subject.search(_).group('subject')
                         for _ in paper['subjects']])

        favorites = [p for p, t in zip(papers, tags)
                     if paper_score(p) >= 30
                     and any([_ in self.favorite_tags for _ in t])
                     and 'Download PDF' in p['links']]

        favorites = list(reversed(sorted(favorites, key=paper_score)))

        with open(result_file, 'w') as fout:
            start_date = metadata['start_date']
            end_date = metadata['end_date']            
            print(f'# {len(papers)} Papers ({start_date} ~ {end_date})', file=fout)
            print(file=fout)
            print(f'## {len(favorites)} Hot Papers', file=fout)
                
            for paper in tqdm(favorites):
                write_paper(paper, fout)


if __name__ == '__main__':                
    import json
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', default='result/papers_with_tweets.json', type=Path)
    parser.add_argument('--output_file', default='result/result.md', type=Path)
    args = parser.parse_args()
    logger.info(args)
    
    data = json.load(open(args.input_file))
    viewer = Viewer()
    viewer.save_markdown(data, args.output_file)

