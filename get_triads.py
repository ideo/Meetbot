import pandas as pd
from datetime import datetime, timedelta

people_info_df = pd.read_csv('people_info.csv', parse_dates = ['hired_at'])
people_info_df['tenure'] = datetime.now() - people_info_df['hired_at']
people_info_df['number_of_meetings'] = 0 # keep track of how many groups someone is in              

min_meetings = 1
max_meetings = 2

new_hire_days = 180
new_hire_mask = timedelta(days=new_hire_days) > people_info_df['tenure']

suggested_triads = []

# keep making trios until everyone is in at least one (or min_meetings) group                       
while (sum(people_info_df.number_of_meetings < min_meetings) > 0):

    # exclude everyone who's been paired too many times                                             
    people_info_df = people_info_df[people_info_df.number_of_meetings < max_meetings]
    
    try:
        new_hire = people_info_df[new_hire_mask].sample()
    except ValueError: # if there are no new hires, just get first person from whole pool
        new_hire = people_info_df.sample()

    # grab the other two people! (if there are two other people!)                                   
    try:
        other_two = people_info_df[~people_info_df.index.isin(new_hire.index)].sample(2)
    except ValueError: # if there aren't 2 more people, just grab whoever's left
        other_two = people_info_df[~people_info_df.index.isin(new_hire.index)]

    triad = pd.concat([new_hire, other_two])

    while len(triad.discipline.unique()) < 2: # this triad is too homogeneous!                      
        triad.drop(triad.tail(1).index, inplace=True) # drop one person                             
        triad.append(people_info_df.sample()) # this person is not excluded from being a new hire

    suggested_triads.append(triad.email_address.tolist()) # add this triad to the list!
    people_info_df.loc[triad.index, 'number_of_meetings'] += 1 # increment the meeting count for people                                                                                                    
suggested_triad_df = pd.DataFrame(suggested_triads, columns=['person_1', 'person_2', 'person_3'])                              
suggested_triad_df.to_csv('suggested_triads.csv')           
