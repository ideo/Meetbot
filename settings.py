import os

DATA_DIRECTORY = './data/'

inside_ideo_json = DATA_DIRECTORY + 'people_info.json' # this json has the project lists
inside_ideo_csv = DATA_DIRECTORY + 'people_info.csv'
bl_list_csv = DATA_DIRECTORY + 'BLs.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'

# where to save the groups
save_directory = DATA_DIRECTORY + 'previous_groupings/'
if not os.path.exists(save_directory):
    os.mkdir(save_directory)

# settings for batch generation
number_in_group = 3
min_disciplines = 2
min_meetings = 1
max_meetings = 2
new_hire_days = 180

# scoring settings
min_score = 0.9
score_weights = {'discipline': 3, 'journey': 1, 'new_hire': 0,
                      'core_project': -2}
# settings for ideal group
ideal_group = {'discipline': 3, 'journey': 2, 'new_hire': 1,
                      'core_project': 0}

# special settings

number_of_meetings_dict = {'mandywong@ideo.com': 0, 'tlee@ideo.com': 0, 'dlee@ideo.com': 0, 'matthewgs@ideo.com': 0

                           }
