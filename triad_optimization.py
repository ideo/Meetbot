import glob
import json
from datetime import datetime

import numpy as np
import pandas as pd

import settings


class BatchGenerator:
    def __init__(self, batch_settings):
        self.people_info_df = pd.read_csv(batch_settings.inside_ideo_csv, parse_dates=['hired_at'])
        self.people_info_df = self.recode_disciplines()
        self.BL_list = pd.read_csv(batch_settings.bl_list_csv)
        self.pairing_files = glob.glob(batch_settings.save_directory + '*.csv')

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

        self.number_of_meetings_dict = batch_settings.number_of_meetings_dict

        self.min_score = batch_settings.min_score
        self.score_weights = batch_settings.score_weights
        self.perfect_score = self.scoring_function(batch_settings.ideal_group)

    def sample_df(self, df_to_sample, number_to_sample):  # base class

        try:
            weight = df_to_sample['max_meetings'] - df_to_sample['number_of_meetings']
            output = df_to_sample.sample(number_to_sample,
                                         weights=weight ** 8)
        except ValueError:
            output = df_to_sample
        return output

    def recode_disciplines(self):  # paired lunch specific
        # recodes support disicplines
        support_discipline_list = [{'discipline': {'Talent': 'Support'}},
                                   {'discipline': {'Marketing': 'Support'}},
                                   {'discipline': {'Coordination': 'Support'}},
                                   {'discipline': {'Experience': 'Support'}},
                                   {'discipline': {'Accounting': 'Support'}}]

        recoded_df = self.people_info_df.copy()

        for i in range(len(support_discipline_list)):
            replacement_dict = support_discipline_list[i]
            recoded_df = recoded_df.replace(to_replace=replacement_dict)

        return recoded_df

    def calculate_triad_score(self, triad):  # paired lunch specific

        combined = self.combined
        triad_data = combined[combined['email_address'].isin(triad.email_address)]

        group_projects = []
        for email_address in triad.email_address:
            projects = self.project_lists[email_address]
            for project in projects:
                group_projects.append(project)

        group_projects = pd.Series(group_projects)
        group_projects = group_projects.value_counts() - 1

        num_overlap = group_projects.sum()

        num_disciplines = len(triad_data.discipline.unique())

        # penalize 2 data scientists
        try:
            ds_count = triad_data['discipline'].value_counts()['Data Science']
        except KeyError:
            ds_count = 0

        if ds_count > 1:
            num_disciplines = num_disciplines - 1

        # convert journies to numbers
        journey_number = {'Intern': 0,
                          '(Temp)': 0,
                          'Individual': 1,
                          'Team': 2,
                          'Director': 3,
                          'Enterprise': 3}

        triad_journies = np.array([journey_number[i] for i in triad_data.Journey])

        if len(triad_journies[triad_journies >= 3]) > 1:
            sub = 4
        else:
            sub = 0

        num_journies = np.max(triad_journies) - np.min(triad_journies) - sub

        hire_delta = datetime.now() - triad_data['hired_at']
        num_new_hires = (hire_delta < pd.Timedelta(days=180)).sum() / len(triad_data)

        score_dict = {'discipline': num_disciplines, 'journey': num_journies, 'new_hire': num_new_hires,
                      'core_project': num_overlap}

        triad_score = self.scoring_function(score_dict) / self.perfect_score

        return triad_score

    def scoring_function(self, score_dict):  # base class
        score_weights = self.score_weights

        triad_score = 0
        for key in score_dict:
            score = score_dict[key]
            weight = score_weights[key]

            triad_score += weight * score

        return triad_score

    def generate_single(self, people_info_df, default_member=None):  # split into part base class/other maybe
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

    def check_score(self, triad):  # paired lunch
        score = self.calculate_triad_score(triad)
        bl_check = self.check_bl(triad)

        return (score > self.min_score and bl_check), score

    def check_previous_pairings(self, triad):

        combined_data = []
        for file in self.pairing_files:
            data = pd.read_csv(file)
            combined_data.append(data)

        combined_data = pd.concat(combined_data)
        combined_data.drop(['score'], axis=1, inplace=True)

        combined_two_list = []
        for i in range(len(combined_data)):
            row = combined_data.iloc[i]
            row_list = self.create_two_list_for_triad(row)
            combined_two_list += row_list

        combined_two_list = set(combined_two_list)
        two_list = set(self.create_two_list_for_triad(triad.email_address.values))
        pair_intersection = two_list.intersection(combined_two_list)

        # if len(pair_intersection) > 0:
        #     print(pair_intersection)

        return len(pair_intersection) == 0

    def create_two_list_for_triad(self, email_ad):  # base class
        two_list = []
        for i in range(len(email_ad)):
            pairs = [frozenset([email_ad[i], email_ad[j]]) for j in range(i + 1, len(email_ad))]
            two_list += pairs

        return two_list

    def check_bl(self, triad):  # paired lunch
        # make pairs from triad

        email_ad = triad.email_address.values
        two_list = self.create_two_list_for_triad(email_ad)

        # check against BL
        two_list = set(two_list)

        BL_list = self.BL_list
        BL_list = set([frozenset(BL_list.iloc[i].values) for i in range(len(BL_list))])

        BL_intersection = two_list.intersection(BL_list)

        return len(BL_intersection) == 0

    def generate_batch(self):  # paired lunch
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

            best_group = []
            high_score = -100
            while (not good_group and iterations < 100):
                triad, batch_df = self.generate_single(batch_df)
                score_check, group_score = self.check_score(triad)
                bl_check = self.check_bl(triad)
                previous_pairing_check = self.check_previous_pairings(triad)

                no_overlap = (bl_check) and (previous_pairing_check)

                # print('pair check', previous_pairing_check)
                # print('bl check', bl_check)
                # print('no overlap', no_overlap)
                # print(' ')

                good_group = score_check and no_overlap

                if group_score > high_score and no_overlap:
                    best_group = triad
                    high_score = group_score

                iterations += 1

            if len(best_group) > 0:
                triad = best_group
                group_score = high_score
                batch_df.loc[
                    triad.index, 'number_of_meetings'] += 1

                suggested_triads.append(triad[['first_name', 'discipline', 'Journey', 'email_address']])
                scores.append(group_score)

        return suggested_triads, scores


if __name__ == '__main__':
    batch_generator = BatchGenerator(settings)

    triads, scores = batch_generator.generate_batch()

    file_data = []
    for i in range(len(triads)):
        emails = list(triads[i]['email_address'].values)
        file_data.append(emails)

    print(file_data)
    col_names = ['person_{}'.format(i) for i in range(len(file_data[0]))]
    suggested_triad_df = pd.DataFrame(file_data, columns=col_names)
    suggested_triad_df['score'] = scores
    suggested_triad_df.to_csv(settings.save_directory + 'suggested_triads_July.csv', index=False)
