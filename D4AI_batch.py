from itertools import combinations

import numpy as np
import pandas as pd

import D4AI_settings


class D4AIBatchGenerator:
    def __init__(self, batch_settings):
        self.D4AI_list = pd.read_excel(batch_settings.D4AI_excel)
        self.D4AI_list['number_of_meetings'] = 0
        self.D4AI_list['max_meetings'] = batch_settings.max_meetings

        self.hours_diff = pd.read_csv(batch_settings.time_zome_csv)
        self.good_groups = self.possible_studio_trios_based_on_time(9, 18)

    def possible_studio_trios_based_on_time(self, start_time, end_time):
        possible_groups = []

        full_df = []

        for i in range(24):  # 24 for 24 hours
            times = (self.hours_diff['hours_diff'] + i) % 24

            # get the ones that are within working hours
            working_hours_bool = (times > start_time) & (times < end_time)
            working_studios = self.hours_diff[working_hours_bool]
            working_studios['time'] = times[working_hours_bool]
            possible_groups.append(frozenset(working_studios['Studio']))
            full_df.append(working_studios)

        studio_pairings = set(possible_groups)
        actual_groups = []
        for group in studio_pairings:
            if len(group) > 2:
                actual_groups.append(group)

        # all possible combinations of 3 studios
        # could also find the combinations of the possible groups
        studios = set(self.D4AI_list['Studio'].values)
        comb = set(combinations(studios, 3))
        good_groups = []
        for entry in comb:
            entry = frozenset(entry)
            for group in actual_groups:
                if entry.issubset(group):
                    good_groups.append(entry)
        good_groups = set(good_groups)

        return good_groups

    def sample_df_meetings(self, df_to_sample, number_to_sample, exp=8):

        weight = df_to_sample['max_meetings'] - df_to_sample['number_of_meetings']
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

        for studio in trio:
            p_zero = percentage_zero.loc[studio]  # percentage people with zero meetings
            if percentage_max[studio] >= 1:
                maxed = 0
            total_weight += p_zero

        return total_weight * maxed

    def find_possible_studios(self, non_leads, selection_studio, good_groups):
        possibilities = []
        weights = []
        for group in good_groups:

            if selection_studio in group:
                possibilities.append(group)
                weights.append(100 * self.find_weight_for_studio_trio(group, non_leads))

        weights = np.array(weights)
        return possibilities, weights

    def generate_single(self):
        non_leads = self.D4AI_list[(self.D4AI_list['Call Lead'] != 'x')]
        leads = self.D4AI_list[(self.D4AI_list['Call Lead'] == 'x')]
        weights = [0, 0]

        while (sum(weights) == 0):  # get the lead and make sure they can lead a call in a group of 3 that needs a call
            selection = self.sample_df_meetings(leads, 1, exp=15)

            selection_studio = selection.Studio.values[0]
            selection_email = [selection.index[0]]

            possibilities, weights = self.find_possible_studios(non_leads, selection_studio, self.good_groups)

        studio_group = pd.DataFrame({'col': possibilities}).sample(weights=weights ** 10).values[0][0]
        other_studios = set(studio_group) - set([selection_studio])

        for studio in other_studios:
            people = non_leads[non_leads.Studio == studio]
            selection = self.sample_df_meetings(people, 1, exp=15)
            selection_email.append(selection.index[0])
        return selection_email

    def generate_batch(self):
        selected = []

        while (sum(self.D4AI_list.number_of_meetings < 1) > 0):
            group_check = False
            while not group_check:
                selection_email = self.generate_single()
                group_check = self.check_previous_batches(selection_email, selected)

            self.D4AI_list.loc[
                selection_email, 'number_of_meetings'] += 1
            selected.append(selection_email)


        return selected

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


def save_list(file_data, output_filename, settings):
    col_names = ['person_{}'.format(i) for i in range(len(file_data[0]))]
    suggested_triad_df = pd.DataFrame(file_data, columns=col_names)
    suggested_triad_df.to_csv(settings.save_directory + output_filename, index=False)


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
        emails_all.append(emails)
        studios_all.append(studios)
        names_all.append(names)
        readable_all.append(readable)

    print(emails_all)
    print(studios_all)
    print(names_all)
    print(readable_all)

    save_list(readable_all, 'readable_list.csv', D4AI_settings)
    save_list(studios_all, 'studio_list.csv', D4AI_settings)
