import numpy as np
import pandas as pd

class LocationScore():
    def __init__(self, location_name):
        self.location_name = location_name

    '''Scoring functions below'''

    def title_score(self, group):
        title_dict = {'Individual': 0,
                      'nan': 0,
                      'Team': 1,
                      'Director': 2,
                      'Enterprise': 2
                      }
        titles = []
        for member in group:
            member_titles = self.directory_data[self.directory_data['em_id'] == member]['title'].values[0]
            titles.append(member_titles)

        title_nums = np.array([title_dict[str(title)] for title in titles])
        if (len(title_nums[title_nums == 2]) > 1) | (len(title_nums[title_nums == 0]) > 2):
            score = 10
        else:
            score = 3 - (len(set(title_nums)))

        title_spread = (max(title_nums) - min(title_nums))

        score += (2 - title_spread)

        return score / 12

    def tenure_score(self, group):
        clip_year = 5
        years = []
        for member in group:
            member_years = self.directory_data[self.directory_data['em_id'] == member]['years_worked_here'].values[0]
            years.append(member_years)

        years = np.array(years)

        if (len(years[years > 10]) > 1) | (len(years[years < 1]) > 2):
            # don't want 3 newbies or 2 old timers
            score = 100
        else:
            group_spread = (max(years) - min(years))
            spread = np.clip(group_spread, 0, clip_year)
            score = (clip_year - spread) / clip_year  # bigger spread is better
        return score

    def division_score(self, group):
        divisions = []
        for member in group:
            member_divisions = self.directory_data[self.directory_data['em_id'] == member]['Division'].values[0]
            divisions.append(member_divisions)
        divisions = np.array(divisions)

        condition = ((divisions == 'Palo Alto') | (divisions == 'SF Health')) | (
            (divisions == 'Palo Alto') | (divisions == 'SF Hatchery'))
        if len(divisions[condition]) > 1:
            score = 4
        else:
            score = 3 - (len(set(divisions)))

        return score / 4

    def shared_projects(self, group):
        all_member_projects = []
        for member in group:
            member_projects = PROJECTS[member]
            all_member_projects += member_projects
        group_projects = pd.Series(all_member_projects)
        group_projects = group_projects.value_counts() - 1
        num_overlap = group_projects.sum()

        if num_overlap > 9:
            score = 10
        else:
            score = 0
        return score / 10.

    def bl_in_group(self, group):
        bl_ids = []
        for member in group:
            bl_id = self.directory_data[self.directory_data['em_id'] == member]['business_lead_em_id'].values[0]
            if str(bl_id) != 'nan':
                bl_ids.append(int(bl_id))
            else:
                bl_ids.append(0)

        group = set(group)
        bl_ids = set(bl_ids)
        bl_overlap = len(group.intersection(bl_ids))

        if bl_overlap > 0:
            bl_overlap = 1

        return bl_overlap

    def discipline_variety(self, group):
        divisions = []
        for member in group:
            member_divisions = self.directory_data[self.directory_data['em_id'] == member]['discipline'].values[0]
            divisions.append(member_divisions)
        divisions = np.array(divisions)

        condition = ((divisions == 'Support'))
        if len(divisions[condition]) > 1:
            score = 10
        else:
            score = (3 - (len(set(divisions)))) / 3
        return score


def recode_project_dict(project_lists, dir_data):
    new_dict = dict()
    for name in project_lists.keys():
        try:
            emp_id = dir_data[dir_data['email_address'] == name]['em_id'].values[0]
            new_dict[emp_id] = project_lists[name]
        except IndexError:
            pass
    return new_dict

if __name__ == '__main__':
    print('hello')