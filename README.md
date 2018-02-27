# paired-lunch

This is a repo to automatically create lunch or coffee dates for IDEOers,
because it's better for a computer to coordinate Google calendar schedules
than a human.

We borrowed heavily from [looking-in](https://github.com/ideo/looking-in/).

## Initial setup

Install your requirements in your preferred environment: `pip install -r requirements`

Make a symlink to dropbox: `ln -sf ~/Dropbox\ \(IDEO\)/looking-in-data dropbox`

## Pre-run setup

Update the `COOKIE` in `dropdox/settings.py` if it's been a few days.

How to get a `COOKIE`?
* Go to any Inside IDEO project page, maybe https://inside.ideo.com/projects/21269
* Use your developer tools to peek the XHR requests (in Chrome you'd do Inspect -> Network -> XHR)
* Reload the page and click on any of the XHRs, maybe `get_parent_assets`
* Look for the Cookie in the Request Header. It will start with `CloudFront-Key-Pair-Id`
* Copy it and replace it in `dropdox/settings.py`