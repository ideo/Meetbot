from simanneal import Annealer
import numpy as np
import random
from location_scores import LocationScore

class MakeAnnealedGroups(Annealer):
    """Test annealer"""

    def __init__(self, groups, project_lists, directory_data, location_name):
        self.state = groups # starting state for groups
        self.projects = project_lists
        self.directory_data = directory_data

        self.scores = np.zeros(len(groups))
        self.sub_scores = np.zeros([len(groups), 4])
        self.scoring_function = LocationScore(location_name=location_name)

    def move(self):
        """Swaps two people in groups."""

        group1 = random.randint(0, len(
            groups) - 1)  # np.where(self.scores == max(self.scores))[0][0]#random.randint(0, len(groups)-1)
        group2 = random.randint(0, len(groups) - 1)

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
            title_s = title_score(group)
            shared = shared_projects(group)
            division = division_score(group)
            bl_overlap = bl_in_group(group, self.directory_data)
            discipline_var = discipline_variety(group, self.directory_data)
            tenure_s = tenure_score(group)

            group_score = (
                              4 * shared + 4 * title_s + 5 * division + 5 * discipline_var + 3 * tenure_s + 10 * bl_overlap) / 22
            sub_scores.append([title_s, shared, division, bl_overlap, discipline_var, tenure_s, group_score])

            e += group_score
            scores.append(group_score)
        self.scores = np.array(scores)
        self.sub_scores = np.array(sub_scores)

        return e

    def run(self):
        self.anneal()

if __name__ == '__main__':
    print('hello')



