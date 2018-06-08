import os

DATA_DIRECTORY = './data/Chicago/'

inside_ideo_json = DATA_DIRECTORY + 'project_json.json' # this json has the project lists
inside_ideo_csv = DATA_DIRECTORY + 'directory_data.csv'
bl_list_csv = DATA_DIRECTORY + 'BLs.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'
#suggested_triads = DATA_DIRECTORY + 'suggested_triads_test.csv'
suggested_triads = 'suggested_triads_test.csv'

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
score_weights = {'discipline': 3,
                 'journey': 1,
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


                           'dlee@ideo.com': 0,# New parents!

                           'fgerlach@ideo.com': 0, # Out of studio
                           'gwinther@ideo.com': 0,
                           'isirer@ideo.com': 0,
                           'loui@ideo.com': 0
                           }

# calendar settings
event_duration = 80 # how long should the meeting last? (in minutes)
earliest_time = 12 # when is the latest the meeting should begin?
latest_time = 14 # when is the latest the meeting should END?
time_window = 30 # how many days out should we search for appropriate times?
event_name = 'Meet n\' Three!'
event_description = """Hello! Meaty the Meetbot here, inviting you all to go out to lunch. This time looked open on 
everyone's calendars, but keep in mind I'm only a prototype! I realize that Google calendar is not necessarily an 
accurate reflection of everyone's life. If this doesn't work for you, please coordinate with each other to find another time! 

You can try a place from our <a href="https://docs.google.com/document/d/1812VOM-ANeDWk0eCCgni5HOvzTEWhEgIurWL0tJqBag/edit">curated list</a>, or choose your own adventure!

This is voluntary! If you are too busy or would rather not participate, feel free to decline the invitation and opt out. 

Please stick to a budget of about $20/person and expense the cost to Chicago Talent in Concur.

Happy FaceSlacking!"""

# TODO: try adding attachment
