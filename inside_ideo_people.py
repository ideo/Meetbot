import gzip
import json
import jsonlines
import os
import pandas as pd
import pprint
import re
import requests
import requests_cache
import socket
import sys
import sys
from bs4 import BeautifulSoup
from dropbox import settings as dropbox_settings
from lxml import etree
from tqdm import *

if __name__ == '__main__':
    sys.setrecursionlimit(3000)

    # target_url = 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=3'
    target_url2 = 'https://inside.ideo.com/users/search?_=1519678038902&page=2&replace=false&sort=relevance&sort_dir=desc&sort_direction_name=desc&user_location_ids%5B%5D=3'
    target_url1 = 'https://inside.ideo.com/users/search?_=1519678038902&page=1&replace=false&sort=relevance&sort_dir=desc&sort_direction_name=desc&user_location_ids%5B%5D=3'

    target_urls = [target_url1, target_url2]

    people_urls = []

    for target_url in target_urls:
        response = requests.get(target_url,
                                headers=dropbox_settings.HEADERS,
                                timeout=5,
                                )

        soup = BeautifulSoup(response.text, "lxml")

        people_info = soup.find_all('a', {'class': ['\\"js-headshot-wrapper\\"']})

        for div in people_info:
            people_urls.append(div['href'].strip())

    count = 0
    for url in people_urls:
        print(count, url)
        count += 1
