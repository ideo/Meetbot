import json
from itertools import combinations

import numpy as np
import pandas as pd

import D4AI_settings


class D4AIBatchGenerator:
    def __init__(self, batch_settings):
        self.D4AI_list = pd.read_excel(batch_settings.D4AI_excel)
        self.save_directory = batch_settings.save_directory
        self.D4AI_list['number_of_meetings'] = 0
        self.D4AI_list['max_meetings'] = batch_settings.max_meetings
        self.min_overlap = batch_settings.min_overlap

        self.hours_diff = pd.read_csv(batch_settings.time_zome_csv)
        self.good_groups = self.possible_studio_trios_based_on_time(8, 18)

    def possible_studio_trios_based_on_time(self, start_time, end_time):

        studios = set(self.D4AI_list['Studio'].values)
        comb = set(combinations(studios, 3))

        stored_dict = {}
        for i in range(24):
            times = (self.hours_diff['hours_diff'] + i) % 24

            # get the ones that are within working hours
            working_hours_bool = (times > 8) & (times < 18)
            working_studios = self.hours_diff[working_hours_bool]
            working_studios['time'] = times[working_hours_bool]

            working_studios_set = set(working_studios.Studio.values)
            comb_bool = [sub for sub in comb if set(sub).issubset(working_studios_set)]
            if len(comb_bool) > 0:
                for c in comb_bool:
                    string = convert_to_studio_key(c)

                    if string in stored_dict:
                        time_list = stored_dict[string]
                        time_list.append(i)
                        stored_dict[string] = time_list
                    else:
                        stored_dict[string] = [i]

        with open(self.save_directory + '/overlapping_times.json', 'w') as fp:
            json.dump(stored_dict, fp)

        good_groups = []
        for string in stored_dict:
            studios = string.split('_')
            times = stored_dict[string]
            # print(studios)
            if len(times) >= self.min_overlap:
                good_groups.append(frozenset(studios))
        good_groups = set(good_groups)

        return good_groups

    def sample_df_meetings(self, df_to_sample, number_to_sample, exp=5):

        weight = df_to_sample['max_meetings'] - df_to_sample['number_of_meetings']
        weight = weight.clip(0, max(weight))
        output = df_to_sample.sample(number_to_sample,
                                     weights=weight ** exp)
        return output

    def find_weight_for_studio_trio(self, trio, D4AI_list):

        total_weight = 0
        maxed = 1

        percentage_zero = D4AI_list[D4AI_list[
                                        'number_of_meetings'] == 0].Studio.value_counts() / D4AI_list.Studio.value_counts()
        percentage_zero.fillna(0, inplace=True)

        percentage_max = D4AI_list[D4AI_list['number_of_meetings'] == D4AI_list[
            'max_meetings']].Studio.value_counts() / D4AI_list.Studio.value_counts()
        percentage_max.fillna(0, inplace=True)

        individual_studios = []
        maxed_count = 0
        for studio in trio:
            p_zero = percentage_zero.loc[studio]  # percentage people with zero meetings
            if percentage_max[studio] >= 1:
                maxed_count += 1
                if maxed_count > -2:
                    maxed = 0.00
                else:
                    maxed = 0.05
            total_weight += p_zero
            individual_studios.append(maxed)

        return total_weight * maxed, individual_studios

    def find_possible_studios(self, non_leads, selection_studio, good_groups):
        possibilities = []
        weights = []
        ind = []
        for group in good_groups:

            if selection_studio in group:
                possibilities.append(group)
                weight, individual_studios = self.find_weight_for_studio_trio(group, non_leads)
                weights.append(100 * weight)
                ind.append(individual_studios)

        weights = np.array(weights)
        return possibilities, weights, ind

    def generate_single(self):

        leads = self.D4AI_list[(self.D4AI_list['Call Lead'] == 'x')]
        weights = [0, 0]
        count = 0
        while (sum(weights) == 0):  # get the lead and make sure they can lead a call in a group of 3 that needs a call

            # first select someone (it doesn't have to be a lead)
            selection = self.sample_df_meetings(self.D4AI_list, 1, exp=5)

            selection_studio = selection.Studio.values[0]
            selection_email = [selection.index[0]]
            selection_is_lead = selection['Call Lead'].values[0] == 'x'

            possibilities, weights, studio_sc = self.find_possible_studios(self.D4AI_list, selection_studio,
                                                                           self.good_groups)
            count += 1
        print('selection is ', selection)
        possible_df = pd.DataFrame({'col': possibilities, 'col2': studio_sc})

        selected_group = possible_df.sample(weights=(weights) ** 10).values
        studio_group = selected_group[0][0]
        studio_w = selected_group[0][1]

        other_studios = list(set(studio_group))  # - set([selection_studio]))

        # if selection is not a lead, you need to select a lead

        # select two distinct people from the other studios
        add_to_group = []
        other_studio_df = pd.DataFrame({'col': other_studios, 'col2': studio_w})

        other_studio_df['num_meetings'] = 0
        other_studio_df['max_meetings'] = 2
        other_studio_df.loc[other_studio_df.col == selection_studio, 'num_meetings'] = 1
        count == 0
        while len(add_to_group) < 2:
            # if selection is not a lead, you need to select a lead


            if (not selection_is_lead):
                people = []
                while len(people)==0:
                    studio_weights = (other_studio_df['max_meetings'] - other_studio_df['num_meetings']) * (
                        other_studio_df['col2'] - 0.05)
                    studio = other_studio_df.sample(weights=studio_weights ** 5).values[0][0]
                    mask = (leads.Studio == studio)
                    people = leads[mask]
                try:
                    selection = self.sample_df_meetings(people, 1, exp=10)
                except ValueError:  # the leads all have max calls
                    print('people are ', people)
                    selection = people.sample(1)
                selection_is_lead = True

            else:
                studio_weights = (other_studio_df['max_meetings'] - other_studio_df['num_meetings']) * (
                    other_studio_df['col2'] - 0.05)

                studio = other_studio_df.sample(weights=studio_weights ** 5).values[0][0]

                mask = (self.D4AI_list.Studio == studio)
                people = self.D4AI_list[mask]

                selection = self.sample_df_meetings(people, 1, exp=10)

            if selection.Email.values[0] not in add_to_group:  # will always be added if i == 0
                selection_email.append(selection.index[0])
                add_to_group.append(selection.Email.values[0])
                other_studio_df.loc[other_studio_df.col == studio, 'num_meetings'] += 1
                count += 1
        return selection_email

    def generate_batch(self):
        selected = []
        group_count = 0
        self.D4AI_list.loc[self.D4AI_list.Name == 'pam', 'max_meetings'] = 2
        while (sum(self.D4AI_list[self.D4AI_list.Name != 'pam'].number_of_meetings < 1) > 0):
            group_check = False
            while not group_check:
                selection_email = self.generate_single()
                if len(selection_email) > 1:
                    group_check = self.check_previous_batches(selection_email, selected)
                else:
                    break

            if selection_email != 'exit':
                score = self.calculate_trio_score(selection_email)

                if score >= 2:
                    group_count += 1
                    self.D4AI_list.loc[
                        selection_email, 'number_of_meetings'] += 1
                    selected.append(selection_email)
            else:
                print('breaking while loop anyway')
                break;

        return selected

    def calculate_trio_score(self, trio):
        studios = set(self.D4AI_list.loc[
                          trio, 'Studio'].values)
        return len(studios)

    def check_previous_batches(self, trio, selected):
        # get combinations in trio
        comb_trio = set(combinations(trio, 2))

        # flatten the selected list
        selected_flat = [item for sublist in selected for item in list(sublist)]

        # combinations
        comb_selected = set(combinations(selected_flat, 2))

        # now see if there is anything in the intersection
        intersect = comb_selected.intersection(comb_trio)

        return len(intersect) == 0


def save_list(file_data, output_filename, settings, last_as_person=True):
    if last_as_person:
        col_names = ['person_{}'.format(i) for i in range(len(file_data[0]))]
    else:
        col_names = ['person_{}'.format(i) for i in range(len(file_data[0]) - 1)]
        col_names.append('studios_key')
    suggested_triad_df = pd.DataFrame(file_data, columns=col_names)
    suggested_triad_df.to_csv(settings.save_directory + output_filename, index=False)


def convert_to_studio_key(trio_studios):
    trio_studios = sorted(list(trio_studios))
    string = trio_studios[0] + '_' + trio_studios[1] + '_' + trio_studios[2]

    return string


if __name__ == '__main__':
    batch_generator = D4AIBatchGenerator(D4AI_settings)

    trios = batch_generator.generate_batch()

    emails_all = []
    studios_all = []
    names_all = []
    readable_all = []

    for row in trios:
        emails = []
        studios = []
        names = []
        readable = []
        for index in row:
            person = batch_generator.D4AI_list.iloc[index]
            emails.append(person.Email)
            studios.append(person.Studio)
            names.append(person.Name)
            readable.append(person.Name + '-' + person.Studio)
        emails.append(convert_to_studio_key(studios))
        emails_all.append(emails)
        studios_all.append(studios)
        names_all.append(names)
        readable_all.append(readable)

    save_list(readable_all, 'readable_list.csv', D4AI_settings)
    save_list(studios_all, 'studio_list.csv', D4AI_settings)
    save_list(emails_all, 'email_list.csv', D4AI_settings)

    (batch_generator.D4AI_list).to_csv('number_of_meetings.csv')
