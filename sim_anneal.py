import random

import numpy as np
from simanneal import Annealer


class MakeAnnealedGroups(Annealer):
    """Test annealer"""

    def __init__(self, GroupsClass):
        # Groups class groups, project_lists, directory_data, location_name
        self.projects = GroupsClass.project_lists
        self.directory_data = GroupsClass.directory_data

        self.state = None  # starting state for groups
        self.current_score = None
        self.scores = None
        self.sub_scores = None
        self.scoring_function = GroupsClass.scoring

    def initialize_state(self):
        random_emp = self.directory_data.sample(frac=1)
        random_emp_num = random_emp['Employee #'].values
        random_emp_num_short = random_emp_num[:len(random_emp_num) // 3 * 3]
        groups = np.array(np.split(random_emp_num_short, 3)).T
        return groups

    def move(self):
        """Swaps two people in groups."""

        group1 = random.randint(0, len(
            self.state) - 1)  # np.where(self.scores == max(self.scores))[0][0]#random.randint(0, len(groups)-1)
        group2 = random.randint(0, len(self.state) - 1)

        a = random.randint(0, 2)
        b = random.randint(0, 2)

        new_state = self.state.copy()

        new_state[group1, a] = self.state[group2, b]
        new_state[group2, b] = self.state[group1, a]
        self.state = new_state

    def energy(self):
        """Calculates the energy as the number of shared projects."""
        e = 0

        scores = []
        sub_scores = []
        for group in self.state:
            group_score, sub_score = self.scoring_function.score_group(group)

            e += group_score
            scores.append(group_score)
            sub_scores.append(sub_score)
        self.scores = np.array(scores)
        self.sub_scores = np.array(sub_scores)
        self.current_score = e
        print(e)
        return e

    def run(self):
        self.state = self.initialize_state()
        self.steps = 2000  # 15000
        self.Tmax = 70
        self.Tmin = 0.001

        self.anneal()


if __name__ == '__main__':
    print('hello')
