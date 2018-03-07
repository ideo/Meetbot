import json
import pandas as pd
import settings
import numpy as np
from datetime import datetime, timedelta


def sample_df(df_to_sample, number_to_sample, weight_factor):
    try:
        output = df_to_sample.sample(number_to_sample,
                                     weights=1 / (weight_factor * df_to_sample['number_of_meetings'] + 1))
    except ValueError:
        output = df_to_sample
    return output


def generate_triad(group_settings):
    number_in_group = group_settings.number_in_group
    min_disciplines = group_settings.min_disciplines

    min_meetings = group_settings.min_meetings
    max_meetings = group_settings.max_meetings

    new_hire_days = group_settings.new_hire_days

    weight_factor = group_settings.weight_factor

    people_info_df = pd.read_csv(settings.inside_ideo_csv, parse_dates=['hired_at'])
    people_info_df['tenure'] = datetime.now() - people_info_df['hired_at']
    people_info_df['number_of_meetings'] = 0  # keep track of how many groups someone is in

    new_hire_delta = pd.Timedelta(days=new_hire_days)
    suggested_triads = []

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
        others = sample_df(everyone_else, number_in_group - 1, weight_factor)

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
    suggested_triad_df = pd.DataFrame(suggested_triads, columns=['person_1', 'person_2', 'person_3'])

    return suggested_triad_df


def generate_random_list(group_settings):
    number_in_group = group_settings.number_in_group
    max_meetings = group_settings.max_meetings
    weight_factor = group_settings.weight_factor

    people_info_df = pd.read_csv(settings.inside_ideo_csv, parse_dates=['hired_at'])

    people_info_df['number_of_meetings'] = 0  # keep track of how many groups someone is in

    suggested_triads = []

    while (sum(people_info_df.number_of_meetings < 1) > 0):
        # exclude everyone who's been paired too many times
        people_info_df = people_info_df[people_info_df.number_of_meetings < max_meetings]  # these people are eligible

        triad = sample_df(people_info_df,
                          number_in_group, weight_factor)

        people_info_df.loc[
            triad.index, 'number_of_meetings'] += 1  # increment the meeting count for people
        suggested_triads.append(triad.email_address.tolist())  # add this triad to the list!

    suggested_triad_df = pd.DataFrame(suggested_triads, columns=['person_1', 'person_2', 'person_3'])

    return suggested_triad_df


def calculate_triad_score(triads, combined, project_lists):
    # number of disciplines
    # number of journeys
    # people with more than one meeting
    # relationship score -> this should be calculated from previous lunch + project data

    discipline_weight = 5
    journey_weight = 1
    core_project_weight = -2
    new_hire_weight = 0

    dis_count = 0
    journey_count = 0
    new_hire_score = 0
    project_score = 0
    triad_scores = []
    for index, row in triads.iterrows():
        triad_data = combined[combined['email_address'].isin(row)]

        group_projects = []
        for email_address in row:
            projects = project_lists[email_address]
            for project in projects:
                group_projects.append(project)

        group_projects = pd.Series(group_projects)
        group_projects = group_projects.value_counts() - 1

        num_overlap = group_projects.sum()
        num_disciplines = len(triad_data.discipline.unique()) / len(triad_data)

        try:
            ds_count = triad_data['discipline'].value_counts()['Data Science']
        except KeyError:
            ds_count = 0

        if ds_count > 1:
            num_disciplines = num_disciplines - 1


        num_journies = len(triad_data.Journey.unique()) / len(triad_data)

        hire_delta = datetime.now() - triad_data['Anniversary']
        num_new_hires = (hire_delta < pd.Timedelta(days=180)).sum() / len(triad_data)

        triad_score = discipline_weight * num_disciplines + journey_weight * num_journies + num_new_hires * new_hire_weight + core_project_weight * num_overlap
        triad_scores.append(triad_score)

    return triad_scores


if __name__ == '__main__':
    directory = pd.read_csv(settings.chideo_directory, parse_dates=['Anniversary'])
    inside_ideo = pd.read_csv(settings.inside_ideo_csv)
    with open(settings.inside_ideo_json) as json_data:
        project_lists = json.load(json_data)

    combined = inside_ideo.merge(directory, left_on='email_address', right_on='Email')

    combined = combined[['email_address', 'Journey', 'discipline', 'Anniversary']]

    highest = 0

    highest_grouping = []
    lowest_grouping = []

    for i in range(20):
        triads = generate_triad(settings)

        score_list = calculate_triad_score(triads, combined, project_lists)

        score = np.median(np.array(score_list))
        triads['score'] = score_list

        if i == 0:
            lowest = score

        if score > highest:
            highest = score
            highest_grouping = triads

        if score < lowest:
            lowest = score
            lowest_grouping = triads


    print(lowest, highest)
    highest_grouping.to_csv(settings.save_directory + 'best_grouping_generate_triad.csv', index=False)
    lowest_grouping.to_csv(settings.save_directory + 'worst_grouping_generate_triad.csv', index=False)
    print('saved ', settings.save_directory + 'best_grouping_generate_triad.csv')
