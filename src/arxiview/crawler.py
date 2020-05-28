import argparse
import json
from pathlib import Path
import time
import re
import locale
import datetime
import requests
from loguru import logger
from bs4 import BeautifulSoup
from tqdm import tqdm


locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')


class Crawler:

    date_format = re.compile(r'^(?P<date>\S+, \d+ \S+ \d+)')

    def __init__(self):
        ...
        
    def crawl_recent(self, targets=['cs', 'stat.ML'], days=1, num_shows=512):
        target_urls = {target: f'https://arxiv.org/list/{target}/pastweek'
                       for target in targets}
        cur_locale = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

        try:
            today = datetime.datetime.now()
            papers = []
            all_titles = set([])
            for cat, url in target_urls.items():
                logger.info(f'new target {cat} ({url})')
                next_url = url + f'?show={num_shows}'
                logger.info(f'processing from {next_url}')
                res = requests.get(next_url)
                soup = BeautifulSoup(res.text, 'lxml')
                h3s = soup.find_all('h3')
                dls = soup.find_all('dl')
                num_processed = 0
                while h3s:
                    h3 = h3s.pop(0)
                    dl = dls.pop(0)
                    s = self.date_format.search(h3.text)
                    logger.info(f'{h3.text}')
                    date = datetime.datetime.strptime(s.group('date'),
                                                      '%a, %d %B %Y')
                    if today - date > datetime.timedelta(days=days):
                        break

                    dts = dl.find_all('dt')
                    dds = dl.find_all('dd')
                    assert(len(dts) == len(dds))
                    for dt, dd in tqdm(zip(dts, dds)):
                        info = {}

                        info['date'] = datetime.datetime.strftime(date,
                                                                '%a, %d %b %Y')
                        
                        # links
                        links = {}
                        for a in dt.span.find_all('a'):
                            title = a['title']
                            href = 'https://arxiv.org' + a['href']
                            links[title] = href
                        info['links'] = links

                        # title
                        div = dd.div.find('div', class_='list-title')
                        div.find('span', class_='descriptor').extract()
                        title = div.text.strip()
                        info['title'] = title
                        if title in all_titles:
                            logger.info(f'already processed: {title}')
                            continue
                        all_titles.add(title)
                        logger.info(f'[{len(papers) + 1}] {title}')
                        
                        # authors
                        div = dd.div.find('div', class_='list-authors')
                        div.find('span', class_='descriptor').extract()
                        authors = []
                        for a in div.find_all('a'):
                            authors.append(a.text)
                        info['authors'] = authors

                        # comments
                        div = dd.div.find('div', class_='list-comments')
                        if div is not None:
                            div.find('span', class_='descriptor').extract()
                            comments = ''.join([str(_).strip() for _ in div.contents
                                                if str(_).strip()])
                            info['comments'] = comments
                        else:
                            info['comments'] = None

                        # handling href
                        
                        # subjects
                        div = dd.div.find('div', class_='list-subjects')
                        div.find('span', class_='descriptor').extract()
                        subjects = [_.strip() for _
                                    in div.text.strip().split(';')]
                        info['subjects'] = subjects
                        print(title, div.text.strip())

                        # abstract
                        time.sleep(0.1)
                        res2 = requests.get(info['links']['Abstract'])
                        soup2 = BeautifulSoup(res2.text, 'lxml')
                        blockquote = soup2.find('blockquote',
                                              class_='abstract')
                        blockquote.find('span', class_='descriptor').extract()
                        info['abstract'] = blockquote.text.strip()


                        papers.append(info)

                    num_processed += len(dds)
                    if len(h3s) == 0:
                        num_skip = num_processed  # 5 is magic number margin
                        print('@@@@', num_skip)
                        next_url = url + f'?skip={num_skip}&show={num_shows}'
                        time.sleep(0.1)
                        res = requests.get(next_url)
                        soup = BeautifulSoup(res.text, 'lxml')
                        h3s = soup.find_all('h3')
                        dls = soup.find_all('dl')
                        if len(h3s) == 0:
                            break
            return papers
        finally:
            locale.setlocale(locale.LC_TIME, '.'.join(cur_locale))
        

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--targets', nargs='+', default=['cs', 'stat.ML'],
                        type=str)
    parser.add_argument('--days', type=int, default=1)
    parser.add_argument('-o', '--output_dir', type=Path, default='result')
    args = parser.parse_args()
    logger.info(args)
    crawler = Crawler()
    papers = crawler.crawl_recent(targets=args.targets,
                                  days=args.days)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f'saving {str(args.output_dir / "papers.json")}')
    json.dump(papers, open(args.output_dir / 'papers.json', 'w'))
