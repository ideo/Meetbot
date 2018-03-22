# paired-lunch

This is a repo to automatically create lunch or coffee dates for IDEOers,
because it's better for a computer to coordinate Google calendar schedules
than a human.

## Initial setup

Install your requirements in your preferred environment: `pip install -r requirements`
Make a symlink to dropbox: `ln -sf ~/Dropbox\ \(IDEO\)/paired_lunch_data data`

### Scrape Inside IDEO (from [looking-in](https://github.com/ideo/looking-in/))
You should only need to rerun this step if the studio roster changes, e.g. if new hires 
have been added to Inside IDEO since the last time you scraped it. 

Update the `COOKIE` in `data/settings.py` if it's been a few days.

How to get a `COOKIE`?
* Go to any Inside IDEO project page, maybe https://inside.ideo.com/projects/21269
* Use your developer tools to peek the XHR requests (in Chrome you'd do Inspect -> Network -> XHR)
* Reload the page and click on any of the XHRs, maybe `get_parent_assets`
* Look for the Cookie in the Request Header. It will start with `CloudFront-Key-Pair-Id`
* Copy it and replace it in `dropbox/settings.py`



## Generating candidate groups 
First, update [settings.py](settings.py) as appropriate. If you have access to the `paired_lunch_data` 
Dropbox folder and created the symlink as above, you should be good to go. The parameters you might want 
to change at runtime are:
- `number_in_group`: How many people should be in each group?
- `min_disciplines`: What is the minimum number of disciplines that an appropriate group can have? (Setting 
this to 2 means no group will contain only one discipline. Don't set this larger than `number_in_group`) 
- `min_meetings`, `max_meetings`: For an individual, what is the minimum number and maximum number of meetings 
they should have on their calendar? (This will affect the overall number of groups generated.)
- `new_hire_days`: What is the maximum time that may have passed since someone's hire date such that they're 
still considered a new hire.
- In `number_of_meetings_dict`, you can force the number of meetings to 0 on an individual level, e.g. for 
folks who are on parental leave, doing rotations in Tokyo, or who just plain don't work here anymore!

## Scheduling meeting times 
Once you've generated and validated your list of candidate groups, you're ready to send some invites! 
You'll need to update the following parameters:
- `event_duration`: How long you want the event to last, in minutes.
- `earliest_time`, `latest_time`: When are the earliest start and latest end times, respectively, for this meeting? 
You might specify 9 and 18 if it can be any time during the workday, or 12 and 2 for a lunch date. Currently you 
can only specify hours, between 1 and 24.
- `time_window`: How far ahead to search for a potential meeting time. If there are no times that work for everyone 
in the group within this time window, they will not receive an invitation.
- `event_name`, `event_description`: How do you want the invite to look on people's calendars? 
