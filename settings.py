import os

DATA_DIRECTORY = './data/'

inside_ideo_json = DATA_DIRECTORY + 'people_info.json' # this json has the project lists
inside_ideo_csv = DATA_DIRECTORY + 'people_info.csv'
bl_list_csv = DATA_DIRECTORY + 'BLs.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'
suggested_triads = DATA_DIRECTORY + 'suggested_triads_2.csv'

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
               'journey': 2,
               'new_hire': 1,
               'core_project': 0}

# special settings
# Here you can force one person's weights to zero
number_of_meetings_dict = {'mandywong@ideo.com': 0,  # Old intern? 
                           'matthewgs@ideo.com': 0, # Matthew is on Inside IDEO twice

                           'tlee@ideo.com': 0, # New parents!
                           'dlee@ideo.com': 0,

                           'fgerlach@ideo.com': 0
                           }

# calendar settings
event_duration = 80 # how long should the meeting last? (in minutes)
earliest_time = 11 # when is the latest the meeting should begin? 
latest_time = 15 # when is the latest the meeting should END?
time_window = 30 # how many days out should we search for appropriate times?
event_name = 'Meet n Three!' 
event_description = """Hello!

Setting up time for you to grab lunch together! 
We chose a time that looked open on everyone's calendars, but this is a trial. 
If this time doesn't work for you, please coordinate with each other to find a new day!
(TODO: explicitly call out what to do if people can't or don't want to participate??) 

We tried to give you enough time to get out of the studio and eat somewhere in the neighborhood.
Here are <a href="https://docs.google.com/document/d/1812VOM-ANeDWk0eCCgni5HOvzTEWhEgIurWL0tJqBag/edit">some suggestions</a>, 
or you can choose your own adventure!
The budget is ~$20/person. Please expense the cost to Chicago Talent in Concur.

Thanks!"""

