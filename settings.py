import os

DATA_DIRECTORY = './data/'

inside_ideo_json = DATA_DIRECTORY + 'people_info.json'
inside_ideo_csv = DATA_DIRECTORY + 'people_info.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'

# where to save the groups
save_directory = DATA_DIRECTORY + 'previous_groupings/'
if not os.path.exists(save_directory):
    os.mkdir(save_directory)

number_in_group = 3
min_disciplines = 2
weight_factor = 50
min_meetings = 1
max_meetings = 2
new_hire_days = 180

min_score = 8

# special settings

number_of_meetings_dict = {'mandywong@ideo.com': 0, 'tlee@ideo.com': 0, 'dlee@ideo.com': 0, 'matthewgs@ideo.com': 0

                           }
