import os

DATA_DIRECTORY = './data/Chicago/'

# where to save the groups
save_directory = DATA_DIRECTORY + 'previous_groupings/'
if not os.path.exists(save_directory):
    os.mkdir(save_directory)


inside_ideo_json = DATA_DIRECTORY + 'project_json.json' # this json has the project lists
inside_ideo_csv = DATA_DIRECTORY + 'directory_data.csv'
bl_list_csv = DATA_DIRECTORY + 'BLs.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'
suggested_triads = save_directory + 'triads_2.csv'
batch_info = save_directory + 'triads_info_2.csv'

# # where to save the groups
# save_directory = DATA_DIRECTORY + 'previous_groupings/'
# if not os.path.exists(save_directory):
#     os.mkdir(save_directory)

# settings for batch generation
number_in_group = 3
min_disciplines = 2
min_meetings = 1
max_meetings = 2
new_hire_days = 180

# scoring settings
min_score = 0.45
score_weights = {'discipline': 3,
                 'journey': 0.25,
                 'new_hire': 0,
                 'core_project': -2}

# settings for ideal group
ideal_group = {'discipline': 3,
               'journey': 3,
               'new_hire': 1,
               'core_project': 0}

# special settings
# Here you can force one person's weights to zero
number_of_meetings_dict = {'mandywong@ideo.com': 0,  # Old intern?
                           'matthewgs@ideo.com': 0, # Matthew is on Inside IDEO twice
                           'jsang@ideo.com':0,
                           'fgerlach@ideo.com': 0, # Out of studio
                           'gwinther@ideo.com': 0,
                           'loui@ideo.com': 0,
                           'gmitchell@ideo.com': 0,
                            'dlee@ideo.com':0,
                           'jgrimley@ideo.com': 0,
         
                           'dschonthal@ideo.com': 0,
                           'kgilbert@ideo.com': 0,
                           'dlewis@ideo.com': 0,
                           'dogan@ideo.com': 0,
                           'ppearson@ideo.com': 0,
                           'ntower@ideo.com': 0,
                           'lzheng@ideo.com': 0,
                           'payroll@ideo.com': 0,
                           'zbachiri@ideo.com': 0,
                           'astewart@ideo.com': 0, 
                           'mweibler@ideo.com': 0,
                           'plorenzoni@ideo.com':0,

                           # 'lcollins@ideo.com': 0, # project Q out all of december
                           # 'mzapan@ideo.com':0,
                           # 'mnizinski@ideo.com':0,
                           # 'bcarlson@ideo.com': 0,
                           'jzanzig@ideo.com':0,
                           'lnash@ideo.com':0,
                           'tvalentine@ideo.com':0,
                            'jgambino@ideo.com':0,
                           'bpeng@ideo.com': 0, #Shanghai
                           'zmarkshausen@ideo.com': 0
                           }

# calendar settings
event_duration = 60 # how long should the meeting last? (in minutes)
earliest_time = 12 # when is the latest the meeting should begin?
latest_time = 13 # when is the latest the meeting should END?
time_window = 30 # how many days out should we search for appropriate times?
event_name = 'Meet n\' Three!'

event_description = '''
Hello! Meaty the Meetbot here, inviting you all to go out to lunch!
If this doesn't work for you, please coordinate with each other to find another time! 
Remember that this is a voluntary benefit!  If you are too busy or would rather not participate, feel free to opt out 
by declining the invitation. 

You can try a place from our <a href="https://docs.google.com/document/d/1812VOM-ANeDWk0eCCgni5HOvzTEWhEgIurWL0tJqBag/edit">curated list</a>, or choose your own adventure! 
Please submit your receipts to ChIDEO Internal: Meet n Three in Expensify. You will be reimbursed up to $20/person.

Happy FaceSlacking!
'''
