import json
import requests
import argparse
from bs4 import BeautifulSoup
from tqdm import tqdm 
from pathlib import Path
from multiprocessing.pool import ThreadPool
from functools import partial

def get_transcript(url:str, title:str):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # get li from <dic class="full-page"> <ul class="section-list">
    full_page = soup.find('div', class_='full-page')
    
    transcripts = []
    lis = full_page.find('ul', class_='section-list').find_all('li', class_="speech")
    for li in tqdm(lis, desc=f'Processing {title}'):
        # get speaker in <span class=speech__meta-data__speaker-name>
        speaker = li.find('div', class_='speech__meta-data').text.strip()
        # get content from <div class="speech__content">
        content = li.find('div', class_='speech__content').text.strip()
        transcripts.append({
            'speaker': speaker,
            'content': content
        })
    return transcripts

def parse_meeting(meeting, output_dir:Path) -> None:
    url = meeting.find('a')['href']
    url = f'{root_url}{url}'
    title = meeting.find('a').text.strip()
    # merge root_url with url
    output_path = output_dir / f'{title}.json'
    if output_path.exists():
        print(f'{output_path} already exists')
        return
    
    try:
        transcript = get_transcript(url, title)
        with output_path.open('w') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f'Error: {title}')
        print(f'Error: {e}')
        return

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', type=str, default='data')
    parser.add_argument('--thread', type=int, default=4)
    return parser.parse_args()

if __name__ == '__main__':
    root_url = 'https://sayit.pdis.nat.gov.tw'
    
    args = get_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    response = requests.get(root_url + '/speeches')
    soup = BeautifulSoup(response.text, 'html.parser')

    pool = ThreadPool(args.thread)
    meetings = soup.find('ul', class_='unstyled').find_all('li')
    iterator = pool.imap_unordered(partial(parse_meeting, output_dir=output_dir), meetings)
    for li in tqdm(iterator, total=len(meetings)):
        continue