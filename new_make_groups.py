import luigi

from location_scrape import LocationScrape
from pathlib import Path
from sim_anneal import MakeAnnealedGroups
import pandas as pd
import numpy as np

pa_remove_IDs = [2215, 3925, 1124, 3966, 4493, 5154, 5487, 5052, 1832, 7112]

health_IDS = [6373, 1054, 7086,
              5553, 4962, 1717,
              6905, 2091, 4495,
              1026, 6845, 5122,
              3791, 6366, 6423,
              6848, 7106, 6263]


class MakeGroups(luigi.Task):
    location_name = luigi.Parameter(default='Chicago')
    #project_lists = luigi.Parameter()
    #directory_data = luigi.Parameter()

    def requires(self):
        # we need to have this month's scraping done already
        return LocationScrape(location_name=self.location_name)

    def get_file_names(self):
        path_dict = {}
        for key in self.input():
            path_dict[key] = Path(self.input()[key].path)

        return path_dict

    def initialize_groups(self):
        self.combine_data()
        random_emp = self.combined_data.sample(frac=1)
        random_emp_num = random_emp['Employee #'].values
        random_emp_num_short = random_emp_num[:len(random_emp_num) // 3 * 3]
        groups = np.array(np.split(random_emp_num_short, 3)).T
        return groups

    def combine_data(self):
        print('override me for your location')

    def run(self):
        print('override me for your location')


class MakeGroupsSF(MakeGroups):
    location_name = luigi.Parameter(default='San Francisco')

    def requires(self):
        # we need to have this month's scraping done already
        return {'San Francisco': LocationScrape(location_name='San Francisco'),
                'Palo Alto': LocationScrape(location_name='Palo Alto')}

    def combine_data(self):
        SF_data = pd.read_excel(SF_MEETBOT_PATH)
        directory_data_SF = pd.read_csv(self.input()['San Francisco']['directory'].path)

        directory_data_PA = pd.read_csv(self.input()['Palo Alto']['directory'].path)
        directory_data = pd.concat([directory_data_PA, directory_data_SF])
        SF_data = SF_data[SF_data['Employment Status'] == 'Full time']
        SF_data.loc[SF_data['Employee #'].isin(health_IDS), 'Division'] = 'SF Health'
        SF_data = SF_data.merge(directory_data, left_on='Employee #', right_on='em_id')

        SF_data = SF_data[~SF_data['Employee #'].isin(pa_remove_IDs)]
        SF_data['years_worked_here'] = (np.datetime64('today') - SF_data['Employment Status: Date'].values).astype(
            'timedelta64[D]') / np.timedelta64(1, 'D')
        SF_data['years_worked_here'] = SF_data['years_worked_here'] / 365.




    def run(self):
        # groups = self.initialize_groups()
        # group_maker = making_method(groups, self.project_lists, self.directory_data, self.location_name)
        # group_maker.run()
        self.combine_data()
        print('test')


if __name__ == '__main__':
    locations = ['San Francisco']

    for location in locations:
        print(location)
        tr = MakeGroupsSF()
        luigi.build([tr], local_scheduler=True)
