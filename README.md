# paired-lunch

This is a repo to automatically create lunch or coffee dates for IDEOers,
because it's better for a computer to coordinate Google calendar schedules
than a human.

## 1. Initial setup + scrape Inside IDEO
For this step, we borrowed heavily from [looking-in](https://github.com/ideo/looking-in/)!

Install your requirements in your preferred environment: `pip install -r requirements`

Make a symlink to dropbox: `ln -sf ~/Dropbox\ \(IDEO\)/looking-in-data dropbox`

Update the `COOKIE` in `dropbox/settings.py` if it's been a few days.

How to get a `COOKIE`?
* Go to any Inside IDEO project page, maybe https://inside.ideo.com/projects/21269
* Use your developer tools to peek the XHR requests (in Chrome you'd do Inspect -> Network -> XHR)
* Reload the page and click on any of the XHRs, maybe `get_parent_assets`
* Look for the Cookie in the Request Header. It will start with `CloudFront-Key-Pair-Id`
* Copy it and replace it in `dropbox/settings.py`

[`inside_ideo_people.py`](inside_ideo_people.py)

## 2. Generate some candidate groups.
TODO: add some documentation about how groups are chosen 
[`triad_optimization.py`](triad_optimization.py) / [`get_triads.py`](get_triads.py) 

## 3. Find a time that works for everyone, and send them invites!  
Update the parameters:
- `event_duration`: How long you want the event to last, in hours and/or minutes.
- `earliest_time`, `latest_time`: When are the earliest and latest times, respectively, that are eligible for this meeting? You might specify 9 and 18 if it can be any time during the workday, or 12 and 2 for a lunch date. Currently you can only specify hours, between 0 and 23.
- `time_window`: How far ahead to look for a potential meeting time (). TODO: error if there are no times within the window
- `event_name`, `event_description` 

[`quickstart.py`](quickstart.py)
