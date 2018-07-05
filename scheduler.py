from __future__ import print_function

import datetime
import dateutil.parser
import httplib2
import json
import os
import pandas as pd 
import traces

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import settings 

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

class CalendarTool:
    def __init__(self, calendar_settings):
        self.event_duration = datetime.timedelta(minutes=calendar_settings.event_duration)
        # Don't need earliest and latest time settings (they're based on the three studios' overlap)
        #self.earliest_time = calendar_settings.earliest_time
        #self.latest_time = calendar_settings.latest_time

        self.time_window = datetime.timedelta(days=calendar_settings.time_window)

        self.event_name = calendar_settings.event_name
        self.event_description = calendar_settings.event_description
  
    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        #print(credential_dir)
        #print(' ')
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

    def slice(self, series, start, end, default=0):
        """Technically TimeSeries has a method for this, but it wasn't working and it
        was easier to write something of my own than to try to fix that.
        """
        result = traces.TimeSeries(default=default)

        for t0, t1, value in series.iterperiods(start, end):
            result[t0] = value

        result[t1] = series[t1]
        return result

    def interim_periods(self, series, increment=15):
        """ Get incremented.

        Args:
            series (traces.TimeSeries):
            increment (int): Desired size of intervals

        Returns:
            traces.TimeSeries object with timepoints for each of the periods,
            and the value of the *original* TimeSeries at that point
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

    def entire_interval_free(self, series):
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
            end = (dateutil.parser.parse(start) + self.event_duration).isoformat()
            subseries = [i[1] for i in self.slice(series, start=start, end=end).items()]
            result[start] = sum(subseries)

        return result

    def within_timebox(self, event_time, studios=None):
        """Check if a time is within the appropriate parameters.

        Args:
            event_time (str): It might make more sense to have this be a datetime
            object, but u gotta parse em sometime

        Returns:
            True if this event time is valid, otherwise false"""

        start_time = dateutil.parser.parse(event_time).time()
        end_time = (dateutil.parser.parse(event_time) + self.event_duration).time()
        # override the earliest & latest times for D4AI calls
        # since they are coming from 3 different studios
        earliest_time, latest_time = self.time_overlap(studios)
       
        return True if (start_time >= datetime.time(earliest_time) and \
                        end_time <= datetime.time(latest_time) and \
                        end_time >= datetime.time(earliest_time)) \
            else False

    def is_weekend(self, event_time):
        """
        Is this day on a weekend? We can't send people invites for weekends!!!!
        Or Mondays!!! (MLM) 

        Args:
            event_time (str)

        Returns:
            True if the day is a Saturday or Sunday, else False
        """
        day_of_week = dateutil.parser.parse(event_time).weekday()
        if day_of_week in (0,5,6):
            return True
        else:
            return False

    def time_overlap(self, studio_trio):
        """
        Given a trio of studio names (e.g. London_Munich_Shanghai), 
        finds the appropriate minimum and maximum times (in CST)
        for a global d4AI call (using the lookup overlapping_times.json)
        """
        with open('overlapping_times.json') as data_file:
            times = json.load(data_file)

        interval_starts = times[studio_trio] 
        min_time = interval_starts[0]
        max_time = interval_starts[-1] + 1        
        return(min_time, max_time)


    def get_time(self, triad, studios):

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

        # Got freebusy code from https://gist.github.com/cwurld/9b4e10dbeecab28345a3
        body = {
            "timeMin": now,
            "timeMax": (datetime.datetime.utcnow() + self.time_window).isoformat() + 'Z',
            "timeZone": 'US/Central',
            "items": [{"id": email} for email in triad]
        }

        eventsResult = service.freebusy().query(body=body).execute()
        cal_dict = eventsResult[u'calendars']

        busy_times_list = []
        for cal_name in cal_dict:
            busy_times = traces.TimeSeries(default=0) # default is free (0),
            for busy_window in cal_dict[cal_name]['busy']: # manually add busy times
                busy_times[busy_window['start']] = 1
                busy_times[busy_window['end']] = 0
            busy_times_list.append(busy_times)
      
        # combine all of the calendars to find when everyone is free
        try: 
            combined_free_times = traces.TimeSeries.merge(busy_times_list, operation=sum)
        except ValueError:
            print('One of the time series is empty. One of the emails is most likely wrong.')
            return

        all_start_times = self.interim_periods(combined_free_times)

        all_intervals = self.entire_interval_free(all_start_times).to_bool(invert=True)

        eligible_times = [i[0] for i in all_intervals.items() if i[1] is True \
                          and self.within_timebox(i[0], studios)\
                          and not self.is_weekend(i[0])]

        if not eligible_times:
            print('There are no available times for that group in that time range.')
            return
        else:
            event_time = eligible_times[0] # for now, take first time that works. we can refine

            print(event_time)

        return event_time


    def make_event(self, triad, event_time):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        # now create an event and put it on their calendars!
        event = {
            'summary': self.event_name,
            'description': self.event_description,
            'start': {
                'dateTime': event_time,

            },
            'end': {
                'dateTime': (dateutil.parser.parse(event_time) + self.event_duration).isoformat(),

            },

            'attendees': [{"email": email} for email in triad],
            'guestsCanModify': True,
            'visibility': "public"

        }

        event = service.events().insert(calendarId='primary',
                                        body=event,
                                        sendNotifications=True,
                                        ).execute()

        print('Event created: %s' % (event.get('htmlLink')))

        return
    
if __name__ == '__main__':
#    main()
    calendar_tool = CalendarTool(settings)
    suggested_triads = pd.read_csv(settings.suggested_triads,
                                   usecols=[0,1,2,3,4]) 

    for triad in suggested_triads.values.tolist():
        group = triad[0:4]
        group = [name.strip(' ') for name in group] # hack to remove spaces for now -- TODO do this better :)
        print(triad)
        event_time = calendar_tool.get_time(group, 
                                            studios=triad[-1])
        calendar_tool.make_event(group, event_time)
