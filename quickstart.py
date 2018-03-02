from __future__ import print_function
import httplib2
import os
import pandas as pd 

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import dateutil.parser
import traces

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

# define the minimum amount of time that a window can be to support a lunch
#min_time_length = datetime.timedelta(hours=1, minutes=20)

#def window_large_enough(time_window, min_time_length):
#    if ((time_window[1] - time_window[0]) > min_time_length):
#        return True
#    else:
#        return False

#def time_windows_overlap(windows):
#    starts, ends = zip(windows)
#    if max(starts) < min(ends):
#        return True
#    else:
#        return False

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
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """
    Returns a list of dictionaries of start and end times of all busy 
    windows in the next `time_window` days for all of the people in
    `triad` (list of emails) 
    
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    #print('Getting the upcoming 10 events')
    #eventsResult = service.events().list(
    #    calendarId='lnash@ideo.com', 
    #    timeMin=now,
    #    maxResults=10, 
    #    singleEvents=True,
    #    ).execute()
    #events = eventsResult.get('items', [])

    #if not events:
    #    print('No upcoming events found.')
    #for event in events:
    #    start = event['start'].get('dateTime', event['start'].get('date'))
    #    end = event['end'].get('dateTime', event['end'].get('date'))
    #    print(start, end)

    triad = ['lnash@ideo.com', 'jzanzig@ideo.com', 'mmoliterno@ideo.com']
    time_window = datetime.timedelta(days=7)
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
            # add the start & end times of busy windows 
            busy_times[busy_window['start']] = 1
            busy_times[busy_window['end']] = 0  
        busy_times_list.append(busy_times)
    
    # combine all of the calendars -- the times when the sum is 0 everyone is free
    # thresholding finds all that are greater than 0, i.e. returns a boolean indicating when 
    # at least one group member is busy  
    # TODO: check that the time window is large enough 
   
    combined_free_times = traces.TimeSeries.merge(busy_times_list, operation=sum).threshold(0)
    eligible_times = [i[0] for i in combined_free_times.items() if i[1] is False] 

if __name__ == '__main__':
    main()
