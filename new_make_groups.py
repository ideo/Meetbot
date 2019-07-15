import datetime
import json
from multiprocessing import Process
from pathlib import Path

import luigi
import numpy as np
import pandas as pd

import settings
from location_scores import SanFranciscoScore
from location_scrape import LocationScrape
from sim_anneal import MakeAnnealedGroups

pa_remove_IDs = [2215, 3925, 1124, 3966, 4493, 5154, 5487, 5052, 1832, 7112]

health_IDS = [6373, 1054, 7086,
              5553, 4962, 1717,
              6905, 2091, 4495,
              1026, 6845, 5122,
              3791, 6366, 6423,
              6848, 7106, 6263]


class MakeGroups(luigi.Task):
    location_name = luigi.Parameter(default='Chicago')
    directory_data = pd.DataFrame()
    project_lists = {}
    optimizer = None

    # project_lists = luigi.Parameter()
    # directory_data = luigi.Parameter()

    def requires(self):
        # we need to have this month's scraping done already
        # This will be reloaded for SF
        return LocationScrape(location_name=self.location_name)

    def set_optimizer(self, method):
        self.optimizer = method

    def set_scoring_function(self, scoring_function):
        self.scoring = scoring_function

    def get_file_names(self):
        path_dict = {}
        for key in self.input():
            path_dict[key] = Path(self.input()[key].path)

        return path_dict

    def combine_peope_data(self):
        print('COMBINE DATA: override me for your location')

    def recode_disciplines(self):
        support_discipline_list = [{'discipline': {'Talent': 'Support'}},
                                   {'discipline': {'Marketing': 'Support'}},
                                   {'discipline': {'Coordination': 'Support'}},
                                   {'discipline': {'Experience': 'Support'}},
                                   {'discipline': {'Accounting': 'Support'}},
                                   {'discipline': {'Community': 'Support'}},
                                   {'discipline': {'Technology': 'Support'}},
                                   {'discipline': {'Comm Design - Graphic': 'Comm Design'}},
                                   {'discipline': {'Comm Design - Media': 'Comm Design'}},
                                   {'discipline': {'Comm Design - Writing': 'Comm Design'}},
                                   {'discipline': {'Communication Design': 'Comm Design'}}]

        recoded_df = self.directory_data.copy()

        for i in range(len(support_discipline_list)):
            replacement_dict = support_discipline_list[i]

            recoded_df = recoded_df.replace(to_replace=replacement_dict)

        self.directory_data = recoded_df

    def recode_project_dict(self):
        new_dict = dict()
        for name in self.project_lists.keys():
            try:
                emp_id = self.directory_data[self.directory_data['email_address'] == name]['em_id'].values[0]
                new_dict[emp_id] = self.project_lists[name]
            except IndexError:
                pass
        return new_dict

    def run(self):
        self.combine_people_data()
        self.recode_disciplines()
        self.combine_project_data()
        self.scoring = self.scoring(self)
        self.optimizer = self.optimizer(self)
        self.optimizer.run()
        self.group_socre = self.optimizer

        data_path = Path(settings.DATA_DIRECTORY)
        data_path = data_path / self.location_name / 'lunch_groups'
        date_string = datetime.datetime.today().strftime("%Y-%m")

        lunch_groups = pd.DataFrame(self.optimizer.state)
        score = np.floor(pd.DataGrame(self.optimizer.current_score))

        save_path = luigi.LocalTarget(data_path / (date_string + 'lunch_groups_{}.csv').format(score))
        with save_path as output_file:
            lunch_groups.to_csv(output_file, index=False)


class MakeGroupsSF(MakeGroups):
    location_name = luigi.Parameter(default='San Francisco')

    def requires(self):
        # we need to have this month's scraping done already
        return {'San Francisco': LocationScrape(location_name='San Francisco'),
                'Palo Alto': LocationScrape(location_name='Palo Alto')}

    def combine_people_data(self):
        SF_MEETBOT_PATH = './notebooks/SF_meetbot.xlsx'  # TODO: Replace
        SF_data = pd.read_excel(SF_MEETBOT_PATH)
        SF_data = SF_data[SF_data['Employment Status'] == 'Full time']
        directory_data_SF = pd.read_csv(self.input()['San Francisco']['directory'].path)

        directory_data_PA = pd.read_csv(self.input()['Palo Alto']['directory'].path)
        directory_data = pd.concat([directory_data_PA, directory_data_SF])

        SF_data.loc[SF_data['Employee #'].isin(health_IDS), 'Division'] = 'SF Health'
        SF_data = SF_data.merge(directory_data, left_on='Employee #', right_on='em_id')

        SF_data = SF_data[~SF_data['Employee #'].isin(pa_remove_IDs)]
        SF_data['years_worked_here'] = (np.datetime64('today') - SF_data['Employment Status: Date'].values).astype(
            'timedelta64[D]') / np.timedelta64(1, 'D')
        SF_data['years_worked_here'] = SF_data['years_worked_here'] / 365.

        self.directory_data = SF_data

    def combine_project_data(self):
        pa_project_path = self.input()['Palo Alto']['project_json'].path
        sf_project_path = self.input()['San Francisco']['project_json'].path
        with open(sf_project_path) as json_data:
            project_lists_SF = json.load(json_data)

        with open(pa_project_path) as json_data:
            project_lists_PA = json.load(json_data)

        self.project_lists = dict(project_lists_SF, **project_lists_PA)

        self.project_lists = self.recode_project_dict()


if __name__ == '__main__':
    locations = ['San Francisco']

    for location in locations:

        num_iterations = 3
        things_to_start = []
        luigi_tasks = []
        for i in range(num_iterations):
            tr = MakeGroupsSF()
            tr.set_scoring_function(SanFranciscoScore)
            tr.set_optimizer(MakeAnnealedGroups)
            luigi_tasks.append(tr)

        started_tasks = []
        for task in luigi_tasks:
            p1 = Process(target=luigi.build, args=([[task]]), kwargs={'local_scheduler': True})

            p1.start()
            started_tasks.append(p1)

        for thing in started_tasks:
            thing.join()
