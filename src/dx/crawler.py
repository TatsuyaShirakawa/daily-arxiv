import time
import re
import locale
import datetime
import requests
from loguru import logger
from bs4 import BeautifulSoup
import arxiv


locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')


class Crawler:

    date_format = re.compile(r'^(?P<date>\S+, \d+ \S+ \d+)')

    def crawl_recent(self,
                     targets=['cs', 'stat.ML'],
                     from_days_ago=1,
                     to_days_ago=0,
                     num_shows=512):
        assert(from_days_ago <= to_days_ago)
        target_urls = {target: f'https://arxiv.org/list/{target}/pastweek'
                       for target in targets}
        cur_locale = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')

        
        # list papers
        try:
            now = datetime.datetime.now()
            today = datetime.datetime(now.year, now.month, now.day)
            start_date = today - datetime.timedelta(from_days_ago)
            end_date = today - datetime.timedelta(days=to_days_ago - 1)
            metadata = {'start_date': start_date.strftime('%Y/%m/%d'),
                        'end_date': end_date.strftime('%Y/%m/%d')}
            logger.info(metadata)
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
                    date_str = s.group('date')
                    print(date_str)
                    elms = date_str.split()
                    if len(elms[1]) == 1:
                        elms[1] = '0' + elms[1]  # strptime
                    elms[2] = {'Jun': 'June'}.get(elms[2], elms[2])
                    date_str = ' '.join(elms)
                    date_str2 = datetime.datetime.now().strftime('%a, %d %B %Y')
                    date = datetime.datetime.strptime(date_str,
                                                      '%a, %d %B %Y')
                    if date >= end_date:
                        continue
                    if date < start_date:
                        break
                    dts = dl.find_all('dt')
                    dds = dl.find_all('dd')
                    assert(len(dts) == len(dds))
                    for dt, dd in zip(dts, dds):
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

                        info['id'] = info['links']['Abstract'].split('/')[-1]

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
        finally:
            locale.setlocale(locale.LC_TIME, '.'.join(cur_locale))


        arxiv_infos = arxiv.query(id_list=[paper['id'] for paper in papers])
        for paper, arxiv_info in zip(papers, arxiv_infos):
            paper['summary'] = arxiv_info['summary'].strip()
            paper['detail'] = arxiv_info
        
        return {'meta': metadata, 'papers': papers}