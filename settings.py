import os

DATA_DIRECTORY = './data/D4AI_global/call_lists/'

inside_ideo_json = DATA_DIRECTORY + 'project_json.json' # this json has the project lists
inside_ideo_csv = DATA_DIRECTORY + 'directory_data.csv'
bl_list_csv = DATA_DIRECTORY + 'BLs.csv'
chideo_directory = DATA_DIRECTORY + 'ChIDEO_directory.csv'
suggested_triads = DATA_DIRECTORY + 'email_list.csv'
#suggested_triads = 'suggested_triads_test.csv'

# calendar settings
event_duration = 30 # how long should the meeting last? (in minutes)
earliest_time = 12 # when is the latest the meeting should begin?
latest_time = 13 # when is the latest the meeting should END?
time_window = 60 # how many days out should we search for appropriate times?
event_name = 'D4AI Global Update Call!'
event_description = """D4AI Global Call! Text goes here.
"""


