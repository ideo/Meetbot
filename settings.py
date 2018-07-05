import os

DATA_DIRECTORY = './data/D4AI_global/call_lists/'
suggested_triads = DATA_DIRECTORY + 'email_list.csv'

# calendar settings
event_duration = 45 # how long should the meeting last? (in minutes)
time_window = 60 # how many days out should we search for appropriate times?
event_name = 'D4AI Global Update Call!'
event_description = """Hi D4AI Insiders, 

Meaty the Meetbot here, inviting you all to join a call with two other IDEOers to chat about D4AI. I was designed by <a href=https://inside.ideo.com/users/jzanzig>Jane</a> and <a href=https://inside.ideo.com/users/lnash>Lisa</a>, Data Scientists in Chicago, to help create groups and find time on calendars.

I’m helping people in the D4AI community make connections and share inspiration through low key conversations in small groups. Since the three of you have been closer to D4AI over the past year, we’ve found a time for you to learn and share with each other about what’s going on with D4AI across IDEO. 

You can talk about anything you’d like! The goal is to share local updates, questions, and inspirations from your studio. Here are some prompts to get the ball rolling:

- Are there any project opportunities where the D4AI offer is part of how we’re exciting clients? What have you found to be effective in exciting clients? What’s not worked so well?
- Are there any projects happening in your studio that include Data Scientists? If so, what’s happening in them right now? Any observations? If not, are there projects you wish had Data Scientists on them? Why?
- Have you read any interesting articles about Data/AI/Machine Learning lately?  
- Are there any burning questions you have around D4AI or Project Pam? (and if there’s anything that comes up that you all don’t know the answer to, please don’t hesitate to use this is an opportunity to ask the D4AI team)

This time looked open on everyone's calendars, but keep in mind I'm only a prototype!  I realize that Google calendar is not necessarily an accurate reflection of everyone's life. If this doesn't work for you, please coordinate with each other to find another time. (My human counterpart, Biz, can help in a pinch if you need scheduling help.) 

Remember - this is voluntary! If you are too busy or would rather not participate, feel free to decline the invitation and opt out. 

Happy Chatting, or as we call it in Chicago, FaceSlacking!

"""


