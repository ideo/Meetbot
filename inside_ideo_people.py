import json
import os
import pandas as pd
import pprint
import re
import requests
import socket
import sys
from bs4 import BeautifulSoup
from dropbox import settings as dropbox_settings
from tqdm import *

import settings


class LocationScrape:
    def __init__(self, base_url_dict, location_key):
        self.location_key = location_key
        self.location_url = base_url_dict[location_key]

        self.keys_of_interest = ['email_address',
                                 'first_name',
                                 'last_name',
                                 'name',
                                 'hired_at']

        self.location_page_urls = self.get_multi_page_urls()  # the urls of all the location pages (multiple pages for lots of people)
        self.location_users = self.get_location_users()
        self.combined_list = self.get_person_data()

    def get_multi_page_urls(self):
        ''' Goes through pagination to get the urls for all the studio's people pages '''
        response = requests.get(self.location_url,
                                headers=dropbox_settings.HEADERS,
                                timeout=5,
                                )
        soup = BeautifulSoup(response.text, "lxml")
        pagination_info = soup.find_all('div', {'class': ['pagination', 'bottom-pagination']})

        studio_urls = []
        for div in pagination_info:
            pages = div.find_all('a')
            print(pages)
            for page in pages:
                url = page['href'].strip()
                url = url.split('/')[-1].split('\\')[0]
                studio_urls.append(url)
                print('url ', url)

        return studio_urls

    def get_location_users(self):
        '''Gets all the people for this location'''
        target_urls = ['https://inside.ideo.com/users/' + page for page in self.location_page_urls]

        location_users = []

        for target_url in target_urls:
            print(target_url)
            response = requests.get(target_url,
                                    headers=dropbox_settings.HEADERS,  # TODO: make this part of this repository
                                    timeout=15,
                                    )

            soup = BeautifulSoup(response.text, "lxml")

            people_info = soup.find_all('a', {'class': ['\\"js-headshot-wrapper\\"']})

            for div in people_info:
                url = div['href'].strip()
                url.replace('\\', '').strip()
                user = url.split('/')[-1].split('\\')[0]
                location_users.append(user)

        return location_users

    def get_person_data(self):
        combined_list = []
        project_lists = {}
        print('location users', self.location_users)
        print('location users', len(self.location_users))
        for user in self.location_users:

            target_url = 'https://inside.ideo.com/users/' + user
            print('this is the target url', target_url)

            response = requests.get(target_url,
                                    headers=dropbox_settings.HEADERS,
                                    timeout=5,
                                    )
            # turn content into a dictionary

            person_info = json.loads(response.content)

            # extract info that we want
            single_person_dict = {}

            for info_dict in person_info:
                parser_response = self.parse_response(info_dict, single_person_dict)
                if parser_response == AttributeError:
                    for info_list in info_dict:
                        single_person_dict = self.parse_response(info_list, single_person_dict)

            # sys.exit()

            project_page_url = 'https://inside.ideo.com/users/{}/get_my_work_projects'.format(user)

            response = requests.get(project_page_url,
                                    headers=dropbox_settings.HEADERS,
                                    timeout=5,
                                    )

            try:
                project_jsons = response.json()['projects']['Core team']
                project_id_list = []
                project_name_list = []
                projects = {}
                for p_json in project_jsons:
                    project_id_list.append(p_json['id'])
                    project_name_list.append(p_json['name'])
                    projects[p_json['id']] = p_json['name']
                project_lists[single_person_dict['email_address']] = project_id_list

            except KeyError:
                project_lists[single_person_dict['email_address']] = []

            combined_list.append(single_person_dict)
            print(single_person_dict)
            print(project_lists)

        return combined_list, project_lists

    def parse_response(self, possible_dict, single_person_dict={}):
        try:
            this_dict_keys = possible_dict.keys()
            for key in self.keys_of_interest:
                if key in this_dict_keys:
                    if (key == 'name') and ('visible_in_newtube' in this_dict_keys):
                        single_person_dict['discipline'] = possible_dict[key]
                    elif key != 'name':
                        single_person_dict = self.check_for_nicknames(possible_dict, single_person_dict, key)

        except AttributeError:
            return AttributeError

        return single_person_dict

    # TODO: do this better
    def check_for_nicknames(self, possible_dict, single_person_dict, key):
        this_dict_keys = possible_dict.keys()
        if key != 'first_name':
            single_person_dict[key] = possible_dict[key]
        else:
            if ('nickname' in this_dict_keys) and (possible_dict['nickname']):
                single_person_dict[key] = possible_dict['nickname']
            else:
                single_person_dict[key] = possible_dict[key]
        return single_person_dict


if __name__ == '__main__':
    sys.setrecursionlimit(3000)

    # div class="pagination bottom-pagination" #TODO: incorporate pagination correctly. append the href here onto inside.ideo.com

    base_urls = {'Chicago': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=3',
                 'Cambridge': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=2',
                 'London': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=4',
                 'Munich': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=5',
                 'New York': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=8',
                 'Palo Alto': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=24',
                 'San Francisco': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=23',
                 'Shanghai': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=14',
                 'Tokyo': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=15',
                 'Global': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=9'}

    chicago = LocationScrape(base_url_dict = base_urls, location_key ='Palo Alto')


    # target_url = 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=3'
    # base_url = 'https://inside.ideo.com/users/search?_=1519678038902&page={}&replace=false&sort=relevance&sort_dir=desc&sort_direction_name=desc&user_location_ids%5B%5D=3'
    #
    # for key in base_urls:
    #     key = 'San Francisco'
    #     base_url = base_urls[key]
    #     print(base_url)
    #     response = requests.get(base_url,
    #                             headers=dropbox_settings.HEADERS,
    #                             timeout=5,
    #                             )
    #
    #     soup = BeautifulSoup(response.text, "lxml")
    #     pagination_info = soup.find_all('div', {'class': ['pagination', 'bottom-pagination']})
    #
    #     studio_urls = []
    #     for div in pagination_info:
    #         pages = div.find_all('a')
    #         for page in pages:
    #             url = page['href'].strip()
    #             url = url.split('/')[-1].split('\\')[0]
    #             studio_urls.append(url)
    #
    # target_urls = [base_url.format(1), base_url.format(2)]
    #
    # people_urls = []
    #
    # for target_url in target_urls:
    #     response = requests.get(target_url,
    #                             headers=dropbox_settings.HEADERS,
    #                             timeout=5,
    #                             )
    #     print('this is the response', response)
    #
    #     soup = BeautifulSoup(response.text, "lxml")
    #
    #     people_info = soup.find_all('a', {'class': ['\\"js-headshot-wrapper\\"']})
    #
    #     for div in people_info:
    #         people_urls.append(div['href'].strip())
    #
    # combined_list = []
    # project_lists = {}
    # for url in people_urls:
    #     url.replace('\\', '').strip()
    #     user = url.split('/')[-1].split('\\')[0]
    #     target_url = 'https://inside.ideo.com/users/' + user
    #     print('this is the target url', target_url)
    #
    #     response = requests.get(target_url,
    #                             headers=dropbox_settings.HEADERS,
    #                             timeout=5,
    #                             )
    #     # turn content into a dictionary
    #
    #     person_info = json.loads(response.content)
    #
    #     # extract info that we want
    #     single_person_dict = {}
    #
    #     for info_dict in person_info:
    #         parser_response = parse_response(info_dict, keys_of_interest, single_person_dict)
    #         if parser_response == AttributeError:
    #             for info_list in info_dict:
    #                 parse_response(info_list, keys_of_interest, single_person_dict)
    #
    #     # sys.exit()
    #
    #     project_page_url = 'https://inside.ideo.com/users/{}/get_my_work_projects'.format(user)
    #
    #     response = requests.get(project_page_url,
    #                             headers=dropbox_settings.HEADERS,
    #                             timeout=5,
    #                             )
    #
    #     try:
    #         project_jsons = response.json()['projects']['Core team']
    #         project_id_list = []
    #         project_name_list = []
    #         projects = {}
    #         for p_json in project_jsons:
    #             project_id_list.append(p_json['id'])
    #             project_name_list.append(p_json['name'])
    #             projects[p_json['id']] = p_json['name']
    #         project_lists[single_person_dict['email_address']] = project_id_list
    #
    #     except KeyError:
    #         project_lists[single_person_dict['email_address']] = []
    #
    #     combined_list.append(single_person_dict)
    #
    # with open(settings.inside_ideo_json, 'w') as fp:
    #     json.dump(project_lists, fp)
    # print('saved file ', settings.inside_ideo_json)
    #
    # # people_info_df = pd.DataFrame(combined_list)
    # # people_info_df.to_csv(settings.inside_ideo_csv, index=False)
