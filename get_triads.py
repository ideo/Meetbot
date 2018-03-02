import pandas as pd
from datetime import datetime, timedelta


def sample_df(df_to_sample, number_to_sample, weight_factor):
    try:
        output = df_to_sample.sample(number_to_sample,
                                     weights=1 / (weight_factor * df_to_sample['number_of_meetings'] + 1))
    except ValueError:
        output = df_to_sample
    return output


if __name__ == '__main__':
    number_in_group = 3
    min_disciplines = 2
    weight_factor = 50
    min_meetings = 1
    max_meetings = 2
    new_hire_days = 120

    people_info_df = pd.read_csv('people_info.csv', parse_dates=['hired_at'])
    people_info_df['tenure'] = datetime.now() - people_info_df['hired_at']
    people_info_df['number_of_meetings'] = 0  # keep track of how many groups someone is in

    new_hire_delta = pd.Timedelta(days=new_hire_days)

    suggested_triads = []

    count = 0
    # keep making trios until everyone is in at least one (or min_meetings) group
    while (sum(people_info_df.number_of_meetings < min_meetings) > 0):

        # exclude everyone who's been paired too many times
        people_info_df = people_info_df[people_info_df.number_of_meetings < max_meetings]  # these people are eligible

        new_hire_mask = new_hire_delta > people_info_df[
            'tenure']  # update every iteration
        new_hire_df = people_info_df[new_hire_mask]

        if len(new_hire_df) > 0:
            new_hire = sample_df(new_hire_df, 1, weight_factor)
        else:  # if no new hires
            new_hire = sample_df(people_info_df, 1, weight_factor)

        everyone_else = people_info_df[~people_info_df.index.isin(new_hire.index)]

        # grab the other two people! (if there are two other people!
        others = sample_df(everyone_else, 2, weight_factor)

        triad = pd.concat([new_hire, others])

        while len(triad.discipline.unique()) < min_disciplines:  # this triad is too homogeneous!
            # do we just have a two person group? In that case, just pick someone else who is a different discipline
            if len(triad) < number_in_group:
                filtered_by_discipline = people_info_df[people_info_df['discipline'] != triad.discipline.iloc[0]]
                new_to_triad = sample_df(filtered_by_discipline, number_in_group - len(triad),
                                         weight_factor)
                triad = triad.append(new_to_triad)
            else:
                triad.drop(triad.tail(1).index, inplace=True)  # drop one person, who is not the new hire
                triad = triad.append(people_info_df.sample())  # this person is not excluded from being a new hire

        suggested_triads.append(triad.email_address.tolist())  # add this triad to the list!
        people_info_df.loc[
            triad.index, 'number_of_meetings'] += 1  # increment the meeting count for people
        count += 1

    print(suggested_triads)
    suggested_triad_df = pd.DataFrame(suggested_triads, columns=['person_1', 'person_2', 'person_3'])
    suggested_triad_df.to_csv('suggested_triads.csv')
