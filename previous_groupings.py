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

import settings

class PreviousGroupings:
    def __init__(self, settings):
        self.save_directory = settings.save_directory
    
    def get_credentials(self=None):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
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

    def retrieve_events(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time 
        page_token = None
        while True:
            events = service.events().list(calendarId='primary', 
                                   pageToken=page_token,
                                   timeMax=now # only get events that have happened already
                                  ).execute()
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        return events['items']

    def retrieve_groupings(self, events):
        all_lunch_groups = []
        for event in events:
            attendees = []
            if event['summary'] == 'Meet n\' Three!':
                for attendee in event['attendees']:
                    if (attendee['responseStatus'] != 'declined') & (attendee['email'] != 'meetbot@ideo.com'):
                        attendees.append(attendee['email'])
                if len(attendees) > 1:
                     all_lunch_groups.append(attendees)
        
        return all_lunch_groups

if __name__ == '__main__':
    groupings = PreviousGroupings(settings) 
    events = groupings.retrieve_events()
    all_lunch_groups = groupings.retrieve_groupings(events)

    all_lunch_groups_df = pd.DataFrame(all_lunch_groups)
    all_lunch_groups_df.to_csv(settings.save_directory + 'previous_groupings.csv')

