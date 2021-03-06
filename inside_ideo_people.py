import json
import os
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup
#import dropbox_settings
from data import settings as dropbox_settings
from tqdm import *
import settings

COOKIE = 'CloudFront-Key-Pair-Id=APKAIJUKKONKFCXJKXRQ; _fbp=fb.1.1549567235996.1626182374; __zlcmid=qki06CTyPxO1JH; dismissed_msg=Alert%3A%20There%20is%20a%20bug%20with%20the%20People%20Page%2FMy%20Work%20Section%20where%20projects%20are%20not%20populating%20correctly.%20We%20are%20working%20on%20a%20resolution%2C%20let%20us%20know%20if%20you%20have%20any%20questions%20by%20using%20the%20Feedback%20tab%20below.; __unam=5b2fc70-16345698ecc-792af5f3-6; CloudFront-Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9jZi5pbnNpZGUuaWRlby5jb20vKiIsIkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTU2NTA1OTczNH19fV19; CloudFront-Signature=MQOcgL7sin2oRodQt0GC8gmc0ieCddXkuTmRXJhFC0MJ%7EdIXCnsWsZURlIaeudcAvR9rpRbaizPD9FEb8d8F57I0WAi%7EO0IVzh54jV0DBdFFaI5KJJICeUrIJRrlrFjd3xY3tzmHchvEzgPNPhHeNBye-l8QWpnSV%7EUufz8jyOFK3wOQ264Y43nrLOwki65BXA6zL%7EBqtKiN5KUAsuR30WCiBLq6jaD-2HS27AWEoUfXHWj5WwCmbnRsYtfFGhi2qg8RP8aITbNI1BknGweUe%7EGr0uFpsS7vAK9chEjBVNUHm6Tr%7ET9c1fCiyhJO6lBORwkb9XIEP2neeYrazp7XTA__; _session_id=37b8c8ba1f255fd28f22ff062bbe9c28; _gid=GA1.2.123917050.1557110935; _gat=1'

HEADERS = {'Accept': 'application/json, text/plain, */*',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept-Language': 'en-US,en;q=0.9',
           'Connection': 'keep-alive',
           'Cookie': COOKIE,
           'Host': 'inside.ideo.com',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           'X-CSRF-TOKEN': 'ZeFOq8jQN0XOGwPHJsChaAQo0GO9qr6W5d6ynIvCdEi1opAJB4TgSQS6Zu6vkPyqjdYUssWRjyDH9HxRKdgBJQ==',
           'X-Requested-With': 'XMLHttpRequest',
           }

class LocationScrape:
    def __init__(self, base_url_dict, location_key):
        self.location_key = location_key
        self.location_url = base_url_dict[location_key]

        self.keys_of_interest = ['email_address',
                                    'first_name',
                                    'last_name',
                                    'hired_at',
                                    'em_id',
                                    'title',
                                    'business_lead_em_id',
                                    'journey_role',
                                    'is_active',
                                    'id',
                                    'name',
                                    'visible_in_newtube',
                                 'employee_type']

        self.location_page_urls = self.get_multi_page_urls()  # the urls of all the location pages (multiple pages for lots of people)
        self.location_users = self.get_location_users()
        self.combined_list, self.project_lists = self.get_person_data()

    def get_multi_page_urls(self):
        ''' Goes through pagination to get the urls for all the studio's people pages '''
        print(self.location_url)
        response = requests.get(self.location_url,
                                headers=HEADERS,
                                timeout=45,
                                )

        #print('this is the cookie', dropbox_settings.HEADERS['Cookie'])
        soup = BeautifulSoup(response.text, "lxml")
        pagination_info = soup.find_all('div', {'class': ['pagination', 'bottom-pagination']})

        studio_urls = []
        for div in pagination_info:
            pages = div.find_all('a')

            for page in pages:
                url = page['href'].strip()
                url = url.split('/')[-1].split('\\')[0]
                studio_urls.append(url)

        return studio_urls

    def get_location_users(self):
        '''Gets all the people for this location'''
        target_urls = ['https://inside.ideo.com/users/' + page for page in self.location_page_urls]
        target_urls.append(self.location_url)
        target_urls = list(set(target_urls))

        location_users = []

        for target_url in target_urls:
            print(target_url)
            response = requests.get(target_url,
                                    headers=HEADERS,  # TODO: make this part of this repository
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
                                    headers=HEADERS,
                                    timeout=15,
                                    )
            # turn content into a dictionary

            person_info = json.loads(response.content)

            # extract info that we want
            single_person_dict = {}
            try:
                for i in range(len(person_info)):
                    info_dict = person_info[i]

                    if i == 0 :
                        parser_response = self.parse_response(info_dict, single_person_dict)

                    if i == 1:
                        parser_response = self.parse_response(info_dict[0], single_person_dict)

                # for info_dict in person_info:
                #     parser_response = self.parse_response(info_dict, single_person_dict)
                #     if parser_response == AttributeError:
                #         for info_list in info_dict:
                #             single_person_dict = self.parse_response(info_list, single_person_dict)

                project_page_url = 'https://inside.ideo.com/users/{}/get_my_work_projects'.format(user)

                response = requests.get(project_page_url,
                                        headers=HEADERS,
                                        timeout=15,
                                        )

                project_id_list = []
                # get their core team/leader contributions
                project_id_list = self.parse_project_response(response, project_id_list, responsibility='Team')
                project_id_list = self.parse_project_response(response, project_id_list, responsibility='Project leader')

                project_lists[single_person_dict['email_address']] = project_id_list

                combined_list.append(single_person_dict)
            except:
                print('there was an error')
                pass
        return combined_list, project_lists



    def parse_project_response(self, response, project_id_list, responsibility='Team'):
        try:
            project_jsons = response.json()['projects'][responsibility]
            for p_json in project_jsons:
                project_id_list.append(p_json['id'])

        except:
            pass

        return project_id_list

    def parse_response(self, possible_dict, single_person_dict={}):
        try:
            this_dict_keys = possible_dict.keys()
            for key in self.keys_of_interest:
                if key in this_dict_keys:
                    if (key == 'name'):
                        if ('visible_in_newtube' in this_dict_keys):
                            single_person_dict['discipline'] = possible_dict[key]
                        else:
                            pass
                    elif key == 'em_id' and ('first_name' not in this_dict_keys):
                        pass
                    else:  # key != 'name':
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


def save_data(project_lists, combined_list, data_path, location):
    save_directory = os.path.join(data_path, location)
    if not os.path.exists(save_directory):
        os.mkdir(save_directory)
    json_file = os.path.join(save_directory, 'project_json')
    csv_path = os.path.join(save_directory, 'directory_data.csv')
    with open(json_file, 'w') as fp:
        json.dump(project_lists, fp)
        print('saved file ', json_file)

    people_info_df = pd.DataFrame(combined_list)
    people_info_df.to_csv(csv_path, encoding='utf-8', index=False)


if __name__ == '__main__':
    sys.setrecursionlimit(3000)

    # div class="pagination bottom-pagination" # TODO: incorporate pagination correctly. append the href here onto inside.ideo.com

    base_urls = {'Chicago': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=3'}
        # 'Cambridge': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=2',
        # 'London': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=4',
        # 'Munich': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=5',
        # 'New York': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=8',
     #   'Palo Alto': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=24'}
     #'San Francisco': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=23'}
    # 'Shanghai': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=14',
    # 'Tokyo': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=15',
    # 'Global': 'https://inside.ideo.com/users/search?user_location_ids%5B%5D=9'}

    # chicago = LocationScrape(base_url_dict = base_urls, location_key ='Palo Alto')

    for location in base_urls:
        print('scraping ', location)
        data = LocationScrape(base_url_dict=base_urls, location_key=location)
        save_data(data.project_lists, data.combined_list, settings.DATA_DIRECTORY, location)
