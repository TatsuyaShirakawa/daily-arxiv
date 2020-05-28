import re
import time
from tqdm import tqdm
# from googletrans import Translator
# from arxiview.translator import DeepLTranslator as Translator


class Viewer:

    def __init__(self, prioritized_tags=['cs.CV',
                                         'cs.CL',
                                         'cs.LG',
                                         'cs.AI',
                                         'cs.NE',
                                         'cs.SD',
                                         'cs.DS',
                                         'cs.IR',
                                         'stat.ML']):
        self.prioritized_tags = prioritized_tags[:]


    def save_markdown(self, papers, result_file):

        r_subject = re.compile(r'.+ \((?P<subject>.+)\)')
        subject_tags = [tuple([r_subject.search(_).group('subject') for _ in p['subjects']]) for p in papers]

        
        def write_paper(paper, fout, markup):
            title = paper['title']
            authors = ', '.join(paper['authors'])
            links = paper['links']
            link_abs = links['Abstract']
            link_pdf = None if not "Download PDF" in links else links['Download PDF']
            subjects = [r_subject.search(_).group('subject')
                        for _ in paper['subjects']]
            abstract = paper["abstract"].replace('\n', ' ')

            if markup:
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
            else:
                print(file=fout)
                print(title, file=fout)
                print(file=fout)
                print(authors, file=fout)
                print(f'abs: {links["Abstract"]}', file=fout)
                if link_pdf:
                    print(f'pdf: {links["Download PDF"]}', file=fout) 
                print(' | '.join(subjects), file=fout)
                print(file=fout)
                print(abstract, file=fout)
                print(file=fout)
                print(file=fout)
                

        tags = []
        for paper in papers:
            tags.append([r_subject.search(_).group('subject')
                         for _ in paper['subjects']])

        prioritized = [p for p, t in zip(papers, tags)
                       if t[0] in self.prioritized_tags
                       and 'Download PDF' in p['links']]
                       # if len(set(t) & self.prioritized_tags) > 0]

        not_prioritized = [p for p, t in zip(papers, tags)
                           if p not in prioritized]

        prioritized = sorted(prioritized, key=lambda p: p['subjects'][0])
        not_prioritized = sorted(not_prioritized, key=lambda p: p['subjects'][0])
        
        # translator = Translator()
        with open(result_file, 'w') as fout:
            if args.no_markup:
                print(f'{len(papers)} Papers', file=fout)
                print(f'{len(prioritized)} Prioritized Papers', file=fout)
                print(' | '.join(sorted(self.prioritized_tags)), file=fout)
            else:
                print(f'# {len(papers)} Papers', file=fout)
                print(f'## {len(prioritized)} Prioritized Papers', file=fout)
                print(' | '.join(sorted(self.prioritized_tags)), file=fout)
                
            for paper in tqdm(prioritized):
                write_paper(paper, fout, markup=not args.no_markup)

            if args.no_markup:
                print(f'{len(not_prioritized)} Other Papers', file=fout)
            else:
                print(f'## {len(not_prioritized)} Other Papers', file=fout)
            for paper in tqdm(not_prioritized):
                write_paper(paper, fout, markup=not args.no_markup)

    def save_tsv(self, papers, result_file):

        r_subject = re.compile(r'.+ \((?P<subject>.+)\)')
        subject_tags = [tuple([r_subject.search(_).group('subject') for _ in p['subjects']]) for p in papers]

        
        def write_paper(paper, fout):
            title = paper['title']
            authors = ', '.join(paper['authors'])
            links = paper['links']
            link_abs = links['Abstract']
            link_pdf = links['Download PDF']
            subjects = [r_subject.search(_).group('subject')
                        for _ in paper['subjects']]
            abstract = paper["abstract"].replace('\n', ' ')
            print(title, authors, link_pdf, abstract, file=fout, sep='\t')


        tags = []
        for paper in papers:
            tags.append([r_subject.search(_).group('subject')
                         for _ in paper['subjects']])

        prioritized = [p for p, t in zip(papers, tags)
                      if len(set(t) & self.prioritized_tags) > 0]
        not_prioritized = [p for p, t in zip(papers, tags)
                      if len(set(t) & self.prioritized_tags) == 0]
        
        # translator = Translator()
        with open(result_file, 'w') as fout:
            for paper in tqdm(prioritized):
                write_paper(paper, fout)

            for paper in tqdm(not_prioritized):
                write_paper(paper, fout)
                
    def save_spreadsheet(self, papers, result_file):
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials

        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'daily-arxiv-731732d1cac3.json', scope)
        gc = gspread.authorize(credentials)
        wks = gc.open('Daily ArXiv').sheet1        

        r_subject = re.compile(r'.+ \((?P<subject>.+)\)')
        subject_tags = [tuple([r_subject.search(_).group('subject') for _ in p['subjects']]) for p in papers]

        
        def write_paper(paper, i, markup=True):
            title = paper['title']
            authors = ', '.join(paper['authors'])
            links = paper['links']
            link_abs = links['Abstract']
            link_pdf = links['Download PDF']
            subjects = [r_subject.search(_).group('subject')
                        for _ in paper['subjects']]
            abstract = paper["abstract"].replace('\n', ' ')
            if markup:
                print(file=fout)
                print(f'### {title}', file=fout)
                print(authors, file=fout)
                print(f'abs: {links["Abstract"]}', file=fout)
                print(f'pdf: {links["Download PDF"]}', file=fout) 
                # print(f'[[abs]({link_abs})] [[pdf]({link_pdf})]', file=fout)
                print(' | '.join(subjects), file=fout)
                print(f'```\n{abstract}\n```', file=fout)
                '''
                time.sleep(0.1)
                abstract_ja = translator.translate(abstract,
                src='en', dest='ja').text
                print(f'```\n{abstract_ja}\n```', file=fout)                
                '''
                # time.sleep(1)
                # abstract_ja = translator.translate(abstract)
                # print(f'```\n{abstract_ja}\n```', file=fout)
                print(file=fout)
                print(file=fout)
            else:
                print(file=fout)
                print(title, file=fout)
                print(authors, file=fout)
                print(f'abs: {links["Abstract"]}', file=fout)
                print(f'pdf: {links["Download PDF"]}', file=fout) 
                # print(f'[[abs]({link_abs})] [[pdf]({link_pdf})]', file=fout)
                print(' | '.join(subjects), file=fout)
                print(file=fout)
                print(abstract, file=fout)
                print(file=fout)
                print(file=fout)


        tags = []
        for paper in papers:
            tags.append([r_subject.search(_).group('subject')
                         for _ in paper['subjects']])

        prioritized = [p for p, t in zip(papers, tags)
                      if len(set(t) & self.prioritized_tags) > 0]
        not_prioritized = [p for p, t in zip(papers, tags)
                      if len(set(t) & self.prioritized_tags) == 0]
        
        # translator = Translator()
        with open(result_file, 'w') as fout:
            print(f'# {len(papers)} Papers', file=fout)

            print(f'## {len(prioritized)} Prioritized Papers', file=fout)
            for paper in tqdm(prioritized):
                write_paper(paper, fout, markup=not args['no_markup'])

            print(f'## {len(not_prioritized)} Other Papers', file=fout)
            for paper in tqdm(not_prioritized):
                write_paper(paper, fout, markup=not args['no_markup'])
                


if __name__ == '__main__':                
    import json
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_json', default='result/papers.json', type=Path)
    parser.add_argument('--output_dir', default='result', type=Path)
    parser.add_argument('--no_markup', action='store_true')
    args = parser.parse_args()
    print(args)
    papers = json.load(open(args.input_json))
    viewer = Viewer()
    viewer.save_markdown(papers, args.output_dir / 'result.md')
    # viewer.save_tsv(papers, args.output_dir / 'result.tsv')
