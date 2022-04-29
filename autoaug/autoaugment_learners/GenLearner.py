import torch

import autoaug.child_networks as cn
from autoaug.autoaugment_learners.AaLearner import AaLearner
import random


class Genetic_learner(AaLearner):

    def __init__(self, 
                # search space settings
                sp_num=5,
                p_bins=11, 
                m_bins=10, 
                discrete_p_m=False,
                exclude_method=[],
                # child network settings
                learning_rate=1e-1, 
                max_epochs=float('inf'),
                early_stop_num=20,
                batch_size=8,
                toy_size=1,
                num_offspring=1, 
                ):

        super().__init__(
                    sp_num=sp_num, 
                    p_bins=p_bins, 
                    m_bins=m_bins, 
                    discrete_p_m=discrete_p_m, 
                    batch_size=batch_size, 
                    toy_size=toy_size, 
                    learning_rate=learning_rate,
                    max_epochs=max_epochs,
                    early_stop_num=early_stop_num,
                    exclude_method=exclude_method
                    )

        self.bin_to_aug =  {}
        for idx, augmentation in enumerate(self.augmentation_space):
            bin_rep = '{0:b}'.format(idx)
            while len(bin_rep) < len('{0:b}'.format(len(self.augmentation_space))):
                bin_rep = '0' + bin_rep
            self.bin_to_aug[bin_rep] = augmentation[0]

        self.just_augs = [x[0] for x in self.augmentation_space]
    
        self.mag_to_bin = {
            '0': "0000",
            '1': '0001',
            '2': '0010',
            '3': '0011',
            '4': '0100',
            '5': '0101',
            '6': '0110',
            '7': '0111',
            '8' : '1000',
            '9': '1001',
            '10': '1010',
        }

        self.prob_to_bin = {
            '0': "0000",
            '0.0' : '0000',
            '0.1': '0001',
            '0.2': '0010',
            '0.3': '0011',
            '0.4': '0100',
            '0.5': '0101',
            '0.6': '0110',
            '0.7': '0111',
            '0.8' : '1000',
            '0.9': '1001',
            '1.0': '1010',
            '1' : '1010',
        }

        self.bin_to_prob = dict((value, key) for key, value in self.prob_to_bin.items())
        self.bin_to_mag = dict((value, key) for key, value in self.mag_to_bin.items())
        self.aug_to_bin = dict((value, key) for key, value in self.bin_to_aug.items())

        self.num_offspring = num_offspring


    def gen_random_subpol(self):
        """
        Generates a random subpolicy using the reduced augmentation_space

        Returns
        --------
        subpolicy -> ((transformation, probability, magnitude), (trans., prob., mag.))
        """
        choose_items = [x[0] for x in self.augmentation_space]
        trans1 = str(random.choice(choose_items))
        trans2 = str(random.choice(choose_items))
        prob1 = float(random.randrange(0, 11, 1) / 10)
        prob2 = float(random.randrange(0, 11, 1) / 10)

        if self.aug_space_dict[trans1]:
            mag1 = int(random.randrange(0, 10, 1))
        else:
            mag1 = None

        if self.aug_space_dict[trans2]:
            mag2 = int(random.randrange(0, 10, 1))
        else:
            mag2 = None

        subpol = ((trans1, prob1, mag1), (trans2, prob2, mag2))
        return subpol


    def gen_random_policy(self):
        """
        Generates a random policy, consisting of sp_num subpolicies

        Returns
        ------------
        policy -> [subpolicy, subpolicy, ...]
        """
        pol = []
        for _ in range(self.sp_num):
            pol.append(self.gen_random_subpol())
        return pol

    
    def bin_to_subpol(self, subpol_bin):
        """
        Converts a binary string representation of a subpolicy to a subpolicy

        Parameters
        ------------
        subpol_bin -> str
            Binary representation of a subpolicy

        
        Returns
        -----------
        policy -> [(subpolicy)]
        """
        pol = []
        for idx in range(2):

            if subpol_bin[idx*12:(idx*12)+4] in self.bin_to_aug:
                trans = self.bin_to_aug[subpol_bin[idx*12:(idx*12)+4]]
            else:
                trans = random.choice(self.just_augs)

            mag_is_none = not self.aug_space_dict[trans]

            if subpol_bin[(idx*12)+4: (idx*12)+8] in self.bin_to_prob:
                prob = float(self.bin_to_prob[subpol_bin[(idx*12)+4: (idx*12)+8]])
            else:
                prob = float(random.randrange(0, 11, 1) / 10)

            if subpol_bin[(idx*12)+8:(idx*12)+12] in self.bin_to_mag:
                mag = int(self.bin_to_mag[subpol_bin[(idx*12)+8:(idx*12)+12]])
            else:
                mag = int(random.randrange(0, 10, 1))

            if mag_is_none:
                mag = None
            pol.append((trans, prob, mag))
        pol = [tuple(pol)]
        return pol   


    def subpol_to_bin(self, subpol):
        """
        Converts a subpolicy to its binary representation 

        Parameters
        ------------
        subpol -> ((transforamtion, probability, magnitude), (trans., prob., mag.))

        Returns
        ------------
        bin_pol -> str
            Binary representation of the subpolicy
        """
        bin_pol = ''  
        trans1, prob1, mag1 = subpol[0]
        trans2, prob2, mag2 = subpol[1]

        bin_pol += self.aug_to_bin[trans1] + self.prob_to_bin[str(prob1)]
        
        if mag1 == None:
            bin_pol += '1111' 
        else:
            bin_pol += self.mag_to_bin[str(mag1)]
        
        bin_pol += self.aug_to_bin[trans2] + self.prob_to_bin[str(prob2)]
        
        if mag2 == None:
            bin_pol += '1111' 
        else:
            bin_pol += self.mag_to_bin[str(mag2)]
            
        return bin_pol


    def choose_parents(self, parents, parents_weights):
        """
        Chooses parents from which the next policy will be generated from

        Parameters
        ------------
        parents -> [policy, policy, ...]

        parents_weights -> [float, float, ...]

        Returns
        ------------
        (parent1, parent2) -> (policy, policy)
        
        """
        parent1 = random.choices(parents, parents_weights, k=1)[0][0]
        parent2 = random.choices(parents, parents_weights, k=1)[0][0]
        while parent2 == parent1:
            parent2 = random.choices(parents, parents_weights, k=1)[0][0]
        parent1 = self.subpol_to_bin(parent1)
        parent2 = self.subpol_to_bin(parent2)
        return (parent1, parent2)

    
    def generate_children(self):
        """
        Generates children via the random crossover method

        Returns 
        ------------
        new_pols -> [child_policy, child_policy, ...]
        """
        parent_acc = sorted(self.history, key = lambda x: x[1], reverse=True)
        parents = [x[0] for x in parent_acc]
        parents_weights = [x[1] for x in parent_acc]
        new_pols = []
        for _ in range(self.num_offspring):
            parent1, parent2 = self.choose_parents(parents, parents_weights)
            cross_over = random.randrange(1, int(len(parent2)/2), 1)
            cross_over2 = random.randrange(int(len(parent2)/2), int(len(parent2)), 1)
            child = parent1[:cross_over]
            child += parent2[cross_over:int(len(parent2)/2)]
            child += parent1[int(len(parent2)/2):int(len(parent2)/2)+cross_over2]
            child += parent2[int(len(parent2)/2)+cross_over2:]
            new_pols.append(child)
        return new_pols

    
    def learn(self, train_dataset, test_dataset, child_network_architecture, iterations = 100):
        """
        Generates policies through a genetic algorithm. 

        Parameters
        ------------
        train_dataset -> torchvision.dataset

        test_dataset -> torchvision.dataset

        child_network_architecture -> 

        iterations -> int
            number of iterations to run the instance for
        """

        for idx in range(iterations):
            print("ITERATION: ", idx)
            if len(self.history) < self.num_offspring:
                policy = [self.gen_random_subpol()]
            else:
                policy = self.bin_to_subpol(random.choice(self.generate_children()))
            print("Policy: ", policy)
            
            reward = self._test_autoaugment_policy(policy,
                                                child_network_architecture,
                                                train_dataset,
                                                test_dataset)  
            print("reward: ", reward)




