import torch
import torch.nn as nn
import pygad
import pygad.torchga as torchga
import torchvision
import torch

from autoaug.autoaugment_learners.AaLearner import AaLearner
import autoaug.controller_networks as cont_n


class EvoLearner(AaLearner):
    """Evolutionary Strategy learner
    
    This learner generates neural networks that predict optimal augmentation
    policies. Hence, there is no backpropagation or gradient descent. Instead,
    training is done by randomly changing weights of the 'parent' networks, where
    parents are determined by their ability to produce policies that 
    increase the accuracy of the child network.

    Args:
        AaLearner: 
            Base class of all-auto augmentation learners.
    
        sp_num: int, default 5
            Number of subpolicies to keep in the final policy

        p_bins: int, default 1
            Number of probability bins for the controller network.

        m_bins: int, default 1
            Number of magnitude bins for the controller network

        discrete_p_m: bool, default False
            Boolean value to set if there are discrete or continuous
            probability and mangitude bins (if False; p_bins, m_bins = 1)

        exclude_method: list, default []
            List of augmentations to be excluded from the search space

        (Child Network Args)

        learning_rate: float, default 1e-6
            Learning rate of the child network

        max_epochs: float, default float('inf')
            Theoretical maximum number of epochs that the child network 
            can be trained on 

        early_stop_num: int, default 20
            Criteria for early stopping. I.e. if the network has not improved 
            after early_stop_num iterations, the training is stopped

        batch_size: int, default 8
            Batch size for the datasets

        toy_size: float, default 1
            If a toy dataset is created, it will be of size toy_size compared
            to the original dataset

        (Evolutionary learner specific settings)

        num_solutions: int, default 5
            Number of offspring spawned at each generation of the algorithm 

        num_parents_mating: int, default 3
            Number of networks chosen as parents for the next generation of networks 

        controller: Torch Network, default cont_n.EvoController
            Controller network for the evolutionary algorithm


    See Also
    --------


    Notes
    -----
    The Evolutionary algorithm runs in generations, and so batches of child networks
    are trained at specific time intervals.


    References
    ----------

    

    Examples
    --------
    from autoaug.autoaugment_learners.EvlLearner import EvoLearner
    evo_learner = EvoLearner()


    """
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
                # evolutionary learner specific settings
                num_solutions=5,
                num_parents_mating=3,
                controller=cont_n.EvoController
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

        # evolutionary algorithm settings
        # self.controller = controller(
        #                 fun_num=self.fun_num, 
        #                 p_bins=self.p_bins, 
        #                 m_bins=self.m_bins, 
        #                 sub_num_pol=self.sp_num
        #                 )
        self.controller = controller
        self.num_solutions = num_solutions
        self.torch_ga = torchga.TorchGA(model=self.controller, num_solutions=num_solutions)
        self.num_parents_mating = num_parents_mating
        self.initial_population = self.torch_ga.population_weights

        # store our logs
        self.policy_dict = {}

        self.running_policy = []


        assert num_solutions > num_parents_mating, 'Number of solutions must be larger than the number of parents mating!'

    
    def _get_single_policy_cov(self, x, alpha = 0.5):
        """
        Selects policy using population and covariance matrices. For this method 
        we require p_bins = 1, num_sub_pol = 1, m_bins = 1. 

        Parameters
        ------------
        x -> PyTorch Tensor
            Input data for the AutoAugment network 

        alpha -> Float
            Proportion for covariance and population matrices 

        Returns
        -----------
        Subpolicy -> [(String, float, float), (String, float, float)]
            Subpolicy consisting of two tuples of policies, each with a string associated 
            to a transformation, a float for a probability, and a float for a magnittude
        """
        section = self.fun_num + self.p_bins + self.m_bins

        y = self.controller.forward(x)

        y_1 = torch.softmax(y[:,:self.fun_num], dim = 1) 
        y[:,:self.fun_num] = y_1
        y_2 = torch.softmax(y[:,section:section+self.fun_num], dim = 1)
        y[:,section:section+self.fun_num] = y_2
        concat = torch.cat((y_1, y_2), dim = 1)

        cov_mat = torch.cov(concat.T)
        cov_mat = cov_mat[:self.fun_num, self.fun_num:]
        shape_store = cov_mat.shape

        counter, prob1, prob2, mag1, mag2 = (0, 0, 0, 0, 0)


        prob_mat = torch.zeros(shape_store)
        for idx in range(y.shape[0]):
            prob_mat[torch.argmax(y_1[idx])][torch.argmax(y_2[idx])] += 1
        prob_mat = prob_mat / torch.sum(prob_mat)

        cov_mat = (alpha * cov_mat) + ((1 - alpha)*prob_mat)

        cov_mat = torch.reshape(cov_mat, (1, -1)).squeeze()
        max_idx = torch.argmax(cov_mat)
        val = (max_idx//shape_store[0])
        max_idx = (val, max_idx - (val * shape_store[0]))


        if not self.augmentation_space[max_idx[0]][1]:
            mag1 = None
        if not self.augmentation_space[max_idx[1]][1]:
            mag2 = None
    
        for idx in range(y.shape[0]):
            if (torch.argmax(y_1[idx]) == max_idx[0]) and (torch.argmax(y_2[idx]) == max_idx[1]):
                prob1 += torch.sigmoid(y[idx, self.fun_num]).item()
                prob2 += torch.sigmoid(y[idx, section+self.fun_num]).item()
                if mag1 is not None:
                    mag1 += min(9, 10 * torch.sigmoid(y[idx, self.fun_num+1]).item())
                if mag2 is not None:
                    mag2 += min(9, 10 * torch.sigmoid(y[idx, self.fun_num+1]).item())

                counter += 1

        prob1 = round(prob1/counter, 1) if counter != 0 else 0
        prob2 = round(prob2/counter, 1) if counter != 0 else 0
        if mag1 is not None:
            mag1 = int(mag1/counter)
        if mag2 is not None:
            mag2 = int(mag2/counter)  

        
        return [((self.augmentation_space[max_idx[0]][0], prob1, mag1), (self.augmentation_space[max_idx[1]][0], prob2, mag2))]


    def learn(self, train_dataset, test_dataset, child_network_architecture, iterations = 15, return_weights = False):
        """
        Runs the GA instance and returns the model weights as a dictionary

        Parameters
        ------------
        return_weights -> Bool
            Determines if the weight of the GA network should be returned 
        
        Returns
        ------------
        If return_weights:
            Network weights -> Dictionary
        
        Else:
            Solution -> Best GA instance solution

            Solution fitness -> Float

            Solution_idx -> Int
        """
        print("learn0")
        self.num_generations = iterations
        self.history_best = []

        self.best_model = 0

        self._set_up_instance(train_dataset, test_dataset, child_network_architecture)

        self.ga_instance.run()

        solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
        if return_weights:
            return torchga.model_weights_as_dict(model=self.controller, weights_vector=solution)
        else:
            return solution, solution_fitness, solution_idx


    def _in_pol_dict(self, new_policy):
        new_policy = new_policy[0]
        trans1, trans2 = new_policy[0][0], new_policy[1][0]
        new_set = {new_policy[0][1], new_policy[0][2], new_policy[1][1], new_policy[1][2]}
        if trans1 in self.policy_dict:
            if trans2 in self.policy_dict[trans1]:
                for test_pol in self.policy_dict[trans1][trans2]:
                    if new_set == test_pol:
                        return True
                self.policy_dict[trans1][trans2].append(new_set)
            else:
                self.policy_dict[trans1] = {trans2: [new_set]}
        return False


    def _set_up_instance(self, train_dataset, test_dataset, child_network_architecture):
        """
        Initialises GA instance, as well as fitness and _on_generation functions
        
        """

        def _fitness_func(solution, sol_idx):
            """
            Defines the fitness function for the parent selection

            Parameters
            --------------
            solution -> GA solution instance (parsed automatically)

            sol_idx -> GA solution index (parsed automatically)

            Returns 
            --------------
            fit_val -> float            
            """

            model_weights_dict = torchga.model_weights_as_dict(model=self.controller,
                                                            weights_vector=solution)

            self.controller.load_state_dict(model_weights_dict)
            train_dataset.transform = torchvision.transforms.ToTensor()
            self.train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=100)
            count = 0
            for idx, (test_x, label_x) in enumerate(self.train_loader):
                print("here idx: ", idx)
                count += 1
                sub_pol = self._get_single_policy_cov(test_x)


                while self._in_pol_dict(sub_pol):
                    sub_pol = self._get_single_policy_cov(test_x)[0]

                if idx == 0:
                    break

            print("start test")
            fit_val = self._test_autoaugment_policy(sub_pol,child_network_architecture,train_dataset,test_dataset)
            print("end test")


            self.running_policy.append((sub_pol, fit_val))

            if len(self.running_policy) > self.sp_num:
                self.running_policy = sorted(self.running_policy, key=lambda x: x[1], reverse=True)
                self.running_policy = self.running_policy[:self.sp_num]


            if len(self.history_best) == 0:
                self.history_best.append((fit_val))
                self.best_model = model_weights_dict
            elif fit_val > self.history_best[-1]:
                self.history_best.append(fit_val) 
                self.best_model = model_weights_dict
            else:
                self.history_best.append(self.history_best[-1])
            

            

            return fit_val

        def _on_generation(ga_instance):
            """
            Prints information of generational fitness

            Parameters 
            -------------
            ga_instance -> GA instance

            Returns
            -------------
            None
            """
            print("Generation = {generation}".format(generation=ga_instance.generations_completed))
            print("Fitness    = {fitness}".format(fitness=ga_instance.best_solution()[1]))
            return


        self.ga_instance = pygad.GA(num_generations=self.num_generations, 
            num_parents_mating=self.num_parents_mating, 
            initial_population=self.initial_population,
            mutation_percent_genes = 0.1,
            fitness_func=_fitness_func,
            on_generation = _on_generation)