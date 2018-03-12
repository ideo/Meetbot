import json
import numpy as np
import pandas as pd
import settings
from datetime import datetime, timedelta


class BatchGenerator:
    def __init__(self, batch_settings):
        self.people_info_df = pd.read_csv(batch_settings.inside_ideo_csv, parse_dates=['hired_at'])
        self.directory = pd.read_csv(batch_settings.chideo_directory, parse_dates=['Anniversary'],
                                     encoding="ISO-8859-1")
        with open(batch_settings.inside_ideo_json) as json_data:
            self.project_lists = json.load(json_data)

        self.combined = self.people_info_df.merge(self.directory, left_on='email_address', right_on='Email')
        self.combined = self.combined[
            ['first_name', 'email_address', 'Journey', 'discipline', 'Anniversary', 'hired_at']]

        self.number_in_group = batch_settings.number_in_group
        self.min_disciplines = batch_settings.min_disciplines
        self.new_hire_days = batch_settings.new_hire_days
        self.weight_factor = batch_settings.weight_factor

        self.number_of_meetings_dict = batch_settings.number_of_meetings_dict

        self.min_score = batch_settings.min_score

        # score_weights = batch_settings.score_weights  # TODO: Make this a real thing later

    def sample_df(self, df_to_sample, number_to_sample):
        weight_factor = self.weight_factor

        try:
            weight = df_to_sample['max_meetings'] - df_to_sample['number_of_meetings']
            output = df_to_sample.sample(number_to_sample,
                                         weights=weight)
        except ValueError:
            output = df_to_sample
        return output

    #TODO: write this
    #def recode_disciplines(self):
        # recodes support disicplines


    def calculate_triad_score(self, triad):
        # number of disciplines
        # number of journeys
        # people with more than one meeting
        # relationship score -> this should be calculated from previous lunch + project data

        combined = self.combined
        triad_data = combined[combined['email_address'].isin(triad.email_address)]

        discipline_weight = 6
        journey_weight = 2
        core_project_weight = -2
        new_hire_weight = 0

        group_projects = []
        for email_address in triad.email_address:
            projects = self.project_lists[email_address]
            for project in projects:
                group_projects.append(project)

        group_projects = pd.Series(group_projects)
        group_projects = group_projects.value_counts() - 1

        num_overlap = group_projects.sum()

        num_disciplines = len(triad_data.discipline.unique()) / len(triad_data)
        # penalize 2 data scientists
        try:
            ds_count = triad_data['discipline'].value_counts()['Data Science']
        except KeyError:
            ds_count = 0

        if ds_count > 1:
            num_disciplines = num_disciplines - 1

        # convert journies to numbers
        journey_number = {'Individual': 1,
                          'Team': 2,
                          'Director': 3,
                          'Enterprise': 4}

        triad_journies = np.array([journey_number[i] for i in triad_data.Journey])

        if len(triad_journies[triad_journies >= 3]) > 1:
            sub = 1
        else:
            sub = 0

        num_journies = np.max(triad_journies) - np.min(triad_journies) - sub

        hire_delta = datetime.now() - triad_data['Anniversary']
        num_new_hires = (hire_delta < pd.Timedelta(days=180)).sum() / len(triad_data)

        triad_score = discipline_weight * num_disciplines + journey_weight * num_journies \
                      + num_new_hires * new_hire_weight + core_project_weight * num_overlap

        return triad_score

    def generate_single(self, people_info_df, default_member=None):
        min_disciplines = self.min_disciplines
        new_hire_days = self.new_hire_days
        number_in_group = self.number_in_group

        new_hire_delta = pd.Timedelta(days=new_hire_days)
        new_hire_mask = new_hire_delta > people_info_df[
            'tenure']  # update every iteration
        new_hire_df = people_info_df[new_hire_mask]

        if not default_member:
            if len(new_hire_df) > 0:
                new_hire = self.sample_df(new_hire_df, 1)
            else:  # if no new hires
                new_hire = self.sample_df(people_info_df, 1)
        else:
            new_hire = default_member  # replace new hire with the person we want to form the group for

        everyone_else = people_info_df[~people_info_df.index.isin(new_hire.index)]
        # grab the other two people! (if there are two other people!
        others = self.sample_df(everyone_else, number_in_group - 1)
        triad = pd.concat([new_hire, others])

        while len(triad.discipline.unique()) < min_disciplines:  # this triad is too homogeneous!
            # do we just have a two person group? In that case, just pick someone else who is a different discipline
            if len(triad) < number_in_group:
                filtered_by_discipline = people_info_df[people_info_df['discipline'] != triad.discipline.iloc[0]]
                new_to_triad = self.sample_df(filtered_by_discipline, number_in_group - len(triad))
                triad = triad.append(new_to_triad)
            else:
                triad.drop(triad.tail(1).index, inplace=True)  # drop one person, who is not the new hire
                triad = triad.append(people_info_df.sample())  # this person is not excluded from being a new hire

        return triad, people_info_df

    def check_score(self, triad):
        score = self.calculate_triad_score(triad)

        return score > self.min_score, score

    def generate_batch(self):
        batch_df = self.combined.copy()
        batch_df['tenure'] = datetime.now() - batch_df['hired_at']
        batch_df['number_of_meetings'] = 0
        batch_df['max_meetings'] = 2  # default max_meetings is 2

        # set max meetings for specific people
        special_number = self.number_of_meetings_dict
        special_number_emails = special_number.keys()

        for email in special_number_emails:
            mask = batch_df.email_address == email
            batch_df.loc[mask, 'max_meetings'] = special_number[email]

        suggested_triads = []
        scores = []
        while (sum(batch_df.number_of_meetings < 1) > 0):

            # exclude everyone who's been paired too many times
            batch_df = batch_df[
                batch_df.number_of_meetings < batch_df.max_meetings]
            good_group = False
            iterations = 0  # let's not get stuck in this loop forever.

            while (not good_group and iterations < 10):
                triad, batch_df = self.generate_single(batch_df)
                good_group, group_score = self.check_score(triad)

                iterations += 1

            batch_df.loc[
                triad.index, 'number_of_meetings'] += 1

            suggested_triads.append(triad[['first_name', 'discipline', 'Journey', 'email_address']])
            scores.append(group_score)

        return suggested_triads, scores


if __name__ == '__main__':
    batch_generator = BatchGenerator(settings)

    triads, scores = batch_generator.generate_batch()

    for i in range(len(triads)):
        print(triads[i], scores[i])
        print(' ')


#
# def generate_random_list(batch_settings):
#     number_in_group = batch_settings.number_in_group
#     max_meetings = batch_settings.max_meetings
#     weight_factor = batch_settings.weight_factor
#
#     people_info_df = pd.read_csv(settings.inside_ideo_csv, parse_dates=['hired_at'])
#
#     people_info_df['number_of_meetings'] = 0  # keep track of how many groups someone is in
#
#     suggested_triads = []
#
#     while (sum(people_info_df.number_of_meetings < 1) > 0):
#         # exclude everyone who's been paired too many times
#         people_info_df = people_info_df[people_info_df.number_of_meetings < max_meetings]  # these people are eligible
#
#         triad = sample_df(people_info_df,
#                           number_in_group, weight_factor)
#
#         people_info_df.loc[
#             triad.index, 'number_of_meetings'] += 1  # increment the meeting count for people
#         suggested_triads.append(triad.email_address.tolist())  # add this triad to the list!
#
#     suggested_triad_df = pd.DataFrame(suggested_triads, columns=['person_1', 'person_2', 'person_3'])
#
#     return suggested_triad_df
#
#
# if __name__ == '__main__':
#     directory = pd.read_csv(settings.chideo_directory, parse_dates=['Anniversary'])
#     inside_ideo = pd.read_csv(settings.inside_ideo_csv)
#     with open(settings.inside_ideo_json) as json_data:
#         project_lists = json.load(json_data)
#
#     combined = inside_ideo.merge(directory, left_on='email_address', right_on='Email')
#
#     combined = combined[['email_address', 'Journey', 'discipline', 'Anniversary']]
#
#     highest = 0
#
#     highest_grouping = []
#     lowest_grouping = []
#
#     for i in range(20):
#         triads = generate_random_list(settings)
#
#         score_list = calculate_triad_score(triads, combined, project_lists)
#
#         score = np.median(np.array(score_list))
#         triads['score'] = score_list
#
#         if i == 0:
#             lowest = score
#
#         if score > highest:
#             highest = score
#             highest_grouping = triads
#
#         if score < lowest:
#             lowest = score
#             lowest_grouping = triads
#
#     print(lowest, highest)
#     highest_grouping.to_csv(settings.save_directory + 'best_grouping_generate_random_list.csv', index=False)
#     lowest_grouping.to_csv(settings.save_directory + 'worst_grouping_generate_random_list.csv', index=False)
#     print('saved ', settings.save_directory + 'best_grouping_generate_triad_group.csv')
