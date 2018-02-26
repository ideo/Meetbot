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
from bs4 import BeautifulSoup
from dropbox import settings as dropbox_settings
from tqdm import *
import sys

if __name__ == '__main__':
    sys.setrecursionlimit(3000)

    target_url = 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=3'
    response = requests.get(target_url,
                            headers=dropbox_settings.HEADERS,
                            timeout=5,
                            )

    #print(response.content)
    soup = BeautifulSoup(response.content, 'html.parser')

    people_info = soup.find_all('div')

    for entry in people_info:
        print(entry.strip)
    # target_url = 'https://slate.com/'
    # response = requests.get(target_url)
    #
    # #print(response.content)
    # soup = BeautifulSoup(response.content, "html.parser")
    # print(soup.find("div"))
