from __future__ import print_function

import datetime
import dateutil.parser
import httplib2
import os
import pandas as pd 
import traces

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    print(credential_dir)
    print(' ')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def slice(series, start, end, default=0):

    result = traces.TimeSeries(default=default)

    for t0, t1, value in series.iterperiods(start, end):
        result[t0] = value
    
    result[t1] = series[t1]
    return result

def interim_periods(series, increment=15):
    """ Get incremented. Takes series (traces.TimeSeries), increment in 
    number of minutes (integer). Returns a TimeSeries object with
    timepoints for each of the periods and the value of the original 
    TimeSeries at that point 
    """
    
    result = traces.TimeSeries(default=series.default)
    increment = datetime.timedelta(minutes=increment)

    t1 = series.items()[1][0]
    end = series.items()[-1][0]

    while t1 < end:
        result[t1] = series[t1] 
        t1 = (dateutil.parser.parse(t1) + increment).isoformat()

    result[end] = series[end] 
    return result 

def check_interval(series, event_duration):
    """Check if a TimeSeries is 0 for all subintervals within a given time window,
    because being free at the beginning of the meeting != being free for the whole
    meeting time.    
    Arguments: `series` (a traces.TimeSeries object), event_duration (timedelta)
    Returns a TimeSeries where the values represent the intervals starting at the 
    measurement times, and the observations are the sum of all observations within
    the intervals of length event_duration beginning at that time (so a person is 
    free for the entire time window iff the observed value is 0).
    """

    result = traces.TimeSeries(default=series.default)

    for t0 in series.items():
        start = t0[0]
        end = (dateutil.parser.parse(start) + event_duration).isoformat()
        subseries = [i[1] for i in slice(series, start=start, end=end).items()]
        result[start] = sum(subseries)

    return result 

def within_timebox(event_time, earliest_time, latest_time, event_duration):
    start_time = dateutil.parser.parse(event_time).time() 
    end_time = (dateutil.parser.parse(event_time) + event_duration).time()
    return True if (start_time >= datetime.time(earliest_time) and end_time <= datetime.time(latest_time) and end_time >= datetime.time(earliest_time)) else False

def main():
    
    event_duration = datetime.timedelta(hours=1, minutes=20) # how long should lunch (or coffee) last?
    earliest_time = 9 # in datetime "hours" (i.e. in range(24)) 
    latest_time = 18 
    time_window = datetime.timedelta(days=7) # number of days to look ahead for a potential window
    triad = ['lnash@ideo.com', 'jzanzig@ideo.com', 'mmoliterno@ideo.com'] # TODO: unhardcode this :)
    event_name = 'Test Event'
    event_description = 'lorem ipsum'

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    
    # Got code to get freebusy times from https://gist.github.com/cwurld/9b4e10dbeecab28345a3
    body = {
        "timeMin": now,
        "timeMax": (datetime.datetime.utcnow() + time_window).isoformat() + 'Z',
        "timeZone": 'US/Central',
        "items": [{"id": email} for email in triad]
    }

    eventsResult = service.freebusy().query(body=body).execute()
    cal_dict = eventsResult[u'calendars']
    
    busy_times_list = []
    for cal_name in cal_dict:
        busy_times = traces.TimeSeries(default=0) # default is free (0) because we will add their busy times
        for busy_window in cal_dict[cal_name]['busy']:
            # add the start & end times of busy window
            busy_times[busy_window['start']] = 1
            busy_times[busy_window['end']] = 0
        busy_times_list.append(busy_times)

    # combine all of the calendars -- the times when the sum is 0 everyone is free
    # thresholding finds all that are greater than 0, i.e. returns a boolean indicating when
    # at least one group member is busy
    combined_free_times = traces.TimeSeries.merge(busy_times_list, operation=sum)
    all_start_times = interim_periods(combined_free_times) # break out free times into 15-min intervals
    all_intervals = check_interval(all_start_times, event_duration).to_bool(invert=True)
    import pdb; pdb.set_trace()
    eligible_times = [i[0] for i in all_intervals.items() if i[1] is True \
                      and within_timebox(i[0], earliest_time, latest_time, event_duration)]

    event_time = eligible_times[0] # for now, take first time that works. we can refine this 
    
    # now create an event on their calendars! 
    event = {
        'summary': event_name,
        'description': event_description,
        'start': {
            'dateTime': event_time, 

        },
        'end': { 
            'dateTime': (dateutil.parser.parse(event_time) + event_duration).isoformat(),
            
        },
 
        'attendees': [{"email": email} for email in triad],

    }

    event = service.events().insert(calendarId='primary', body=event, sendNotifications=True).execute()
    print('Event created: %s' % (event.get('htmlLink')))
    
if __name__ == '__main__':
    main()
