import os
from collections import Counter
import pickle
import pandas as pd
import numpy as np
import scipy.special as sp
from flee import flee
from flee import spawning
import re
import shutil
import json

class ParticleFilter:
    """
    Class which creates the Particle Filter.
    """

    def __init__(self):
        self.assimilation_directory = "data_assimilation/assimilation_test"
        self.observations_file = self.assimilation_directory + "/observations.csv"
        self.current_iteration_folder = None
        self.next_iteration_folder = None
        self.observation_time = 5 # Example time, should be set according to simulation

    def select_iteration(self):
        """
        Select the subfolder with the highest iteration suffix.
        Returns the path to that subfolder.
        """
        pattern = re.compile(r"iteration*_(\d+)$")  # matches folders ending with _number

        max_suffix = -1
        selected_folder = None

        for name in os.listdir(self.assimilation_directory):
            full_path = os.path.join(self.assimilation_directory, name)
            if os.path.isdir(full_path):
                match = pattern.match(name)
                if match:
                    suffix = int(match.group(1))
                    if suffix > max_suffix:
                        max_suffix = suffix
                        selected_folder = full_path

        # Increment the suffix for the next iteration
        # Create new folder for next iteration
        self.next_iteration_folder = re.sub(r"(iteration_)(\d+)$", lambda m: f"{m.group(1)}{int(m.group(2))+1}", 
                                            selected_folder)
        os.makedirs(self.next_iteration_folder, exist_ok=True)

        print("Subfolder with highest suffix:", selected_folder)
        return selected_folder

    def load_particles(self) -> dict:
        """
        Load particle ecosystems and location maps from pickle files.
        Returns a dictionary of particles with their ecosystems and location maps.
        """
        self.current_iteration_folder = self.select_iteration()
        particles_dict = {}
        for root, dirs, files in os.walk(self.current_iteration_folder):
            for filename in files:
                if filename.startswith("particle_") and filename.endswith("_ecosystem.pkl"):
                    full_path_e = os.path.join(root, filename)
                    particle_name = root.split("/")[-1]
                    particles_dict[particle_name] = {}
                    particles_dict[particle_name]["file_e"] = full_path_e
                if filename.startswith("particle_") and filename.endswith("_location_map.pkl"):
                    full_path_lm = os.path.join(root, filename)
                    particles_dict[particle_name]["file_lm"] = full_path_lm     

        for key, filepath in particles_dict.items():
            with open(filepath["file_e"], "rb") as f:
                particles_dict[key]["e"] = pickle.load(f)
            with open(filepath["file_lm"], "rb") as f:
                particles_dict[key]["lm"] = pickle.load(f)
        
        try:
            with open(self.assimilation_directory + "/particle_weights.json", "r") as f:
                weights_data = json.load(f)
            for particle_id in particles_dict.keys():
                particles_dict[particle_id]["weight"] = weights_data[particle_id]
                print("\nLoaded weight for particle\n", particle_id, ":", weights_data[particle_id])
        except FileNotFoundError:        
            # add initialization of weights eqaully
            print("\nNo weights file found, initializing equal weights.\n")
            for particle_id in particles_dict.keys():
                particles_dict[particle_id]["weight"] = 1.0 / len(particles_dict.keys())

        return particles_dict

    def get_camp_populations(self, particles_dict: dict) -> dict:
        """
        For every camp location add up number of agents in that location for each particle.
        Returns a dictionary with camp populations per particle.
        """
        camp_populations = {}
        for particle_id, particle_data in particles_dict.items():
            e = particle_data["e"]
            lm = particle_data["lm"]
            camp_locations = e.get_camp_names()
            for camp in camp_locations:
                num_agents = lm[camp].numAgents
                if camp not in camp_populations:
                    camp_populations[camp] = {}
                camp_populations[camp][particle_id] = num_agents
        camp_populations = self.add_observations_to_camp_populations(camp_populations, 
                                                                     self.observation_time, 
                                                                     obs_csv_path=self.observations_file)
        
        return camp_populations

    def add_observations_to_camp_populations(self, camp_populations:dict, observation_time:int, obs_csv_path:str) -> dict:
        """
        Add observation data from CSV to camp populations dictionary.
        """
        obs_df = pd.read_csv(obs_csv_path)
        row = obs_df[obs_df["Day"] == observation_time]
        if not row.empty:
            obs_data = row.iloc[0].to_dict()
            obs_data.pop("Day", None)
            obs_data.pop("Date", None)
            for camp, value in obs_data.items():
                if camp not in camp_populations:
                    camp_populations[camp] = {}
                camp_populations[camp]["observation"] = value
        else:
            print(f"No observation data for Day == {observation_time}")
        # print(camp_populations)
        return camp_populations


    def compute_particle_weights_from_dict(self, 
                                           camp_populations: dict, 
                                           particles_dict: dict, 
                                           likelihood:str, 
                                           obs_sigma=None, 
                                           lognormal_sigma=None,
                                           eps=1e-12):
        """
        Compute particle weights from a nested dictionary of the form:

        Parameters
        ----------
        data_dict : dict
            Nested dict with structure: {location: {particle_id: value, ..., 'observation': obs_value}}
        likelihood : str
            'poisson' or 'gaussian'
        obs_sigma : float or dict, optional
            Observation standard deviation(s) for Gaussian likelihood.
            If a dict, should map location names -> sigma.
        eps : float
            Small number to avoid log(0) in Poisson.

        Returns
        -------
        weights : dict
            Normalized weights per particle_id (as strings).
        log_weights : dict
            Unnormalized log-likelihoods per particle_id.
        ESS : float
            Effective sample size.
        """

        # --- 1. Get all particle IDs ---
        particle_ids = particles_dict.keys()

        # --- 2. Initialize log-weight array ---
        logw = {particle_id: 0.0 for particle_id in particle_ids}

        # --- 3. Iterate through each location ---
        for location, population_entries in camp_populations.items():
            if "observation" not in population_entries:
                continue  # skip if no observation at this location
            y = population_entries["observation"]
            if y is None or np.isnan(y):
                continue  # skip missing obs

            # Gaussian sigma per location (if provided)
            if likelihood == "gaussian":
                if obs_sigma is None:
                    raise ValueError("obs_sigma must be provided for Gaussian likelihood")
                sigma = obs_sigma[location] if isinstance(obs_sigma, dict) else obs_sigma

            for particle_id in particle_ids:
                estimate = population_entries.get(particle_id, None)
                if estimate is None:
                    continue  # skip missing particle values
                
                # Maybe only gaussian or lognormal is necessary
                # Compute contribution to log-likelihood
                if likelihood == "poisson":
                    lam = max(estimate, eps)
                    log_term = y * np.log(lam) - lam - sp.gammaln(y + 1.0)
                elif likelihood == "gaussian":
                    log_term = -0.5 * ((estimate - y) ** 2) / (sigma**2) - 0.5 * np.log(2 * np.pi * sigma**2)
                # --- Lognormal likelihood (Gaussian on log scale) ---
                elif likelihood == "lognormal":
                    sigma = lognormal_sigma if lognormal_sigma else 0.5  # default ~50% relative noise
                    log_term = (
                        -0.5 * ((np.log(estimate + eps) - np.log(y + eps)) ** 2) / (sigma**2)
                        - np.log(y * sigma * np.sqrt(2 * np.pi))
                    )
                else:
                    raise ValueError("likelihood must be 'poisson' or 'gaussian'")

                logw[particle_id] += log_term

        # --- 4. Normalize log-weights (prevent underflow) ---
        logw_values = np.array(list(logw.values()))
        max_logw = np.max(logw_values)
        w_unnorm = np.exp(logw_values - max_logw)
        w_norm = w_unnorm / np.sum(w_unnorm)

        # --- 5. Package results ---
        weights = dict(zip(particle_ids, w_norm))
        log_weights = dict(zip(particle_ids, logw_values))
        ess = 1.0 / np.sum(w_norm**2)

        return weights, log_weights, ess

    def systematic_resample(self, particles=None, weights=None):
        """
        Systematic (low variance) resampling.
        If `particles` is None, returns a list of particle IDs from the weights dict.
        If `particles` is provided, returns resampled particle objects.
        """
        if isinstance(weights, dict):
            particle_ids = list(weights.keys())
            weight_values = np.array(list(weights.values()))
        else:
            raise ValueError("weights must be a dictionary {id: weight}")

        N = len(particle_ids)
        positions = (np.arange(N) + np.random.uniform()) / N
        cumulative_sum = np.cumsum(weight_values)
        cumulative_sum[-1] = 1.0
        indexes = np.zeros(N, dtype=int)

        i, j = 0, 0
        while i < N:
            if positions[i] < cumulative_sum[j]:
                indexes[i] = j
                i += 1
            else:
                j += 1

        # Return IDs or objects depending on input
        if particles is None:
            return [particle_ids[k] for k in indexes]
        else:
            return [particles[k] for k in indexes]

    def resample_with_jitter(self, camp_populations: dict, resampled_ids: list, sigma=5.0):
        """
        Create new particle states after resampling, adding jitter only to duplicates.

        Parameters
        ----------
        particle_states : dict
            {location: {particle_id: population}}
        resampled_ids : list
            List of particle IDs from the resampling step (e.g. ['200', '100', '100'])
        sigma : float
            Standard deviation of Gaussian jitter (default 5.0)
        
        Returns
        -------
        new_particle_states : dict
            {location: {new_particle_id: new_population}}
        """

        # Create new dictionary with the same structure
        new_particle_states = {loc: {} for loc in camp_populations.keys()}

        # Track how many times each particle has been copied so we can jitter correctly
        copy_tracker = Counter()

        for new_id in resampled_ids:
            copy_tracker[new_id] += 1
            # print(copy_tracker)
            copy_index = copy_tracker[new_id]
            # print(copy_index)
            
            for loc, pops in camp_populations.items():
                        base_value = pops[new_id]

                        # Jitter only if this is a duplicate (copy 2, 3, ...)
                        if copy_index > 1:
                            new_particle_id = f"{new_id}_v{copy_index}"
                            jitter = np.random.normal(0, sigma)
                            new_value = int(round(max(0, base_value + jitter)))
                        else:
                            new_particle_id = new_id
                            new_value = base_value

                        new_particle_states[loc][new_particle_id] = new_value
                        
        return new_particle_states

    def update_particles(self, particles_dict: dict, camp_populations: dict, new_camp_populations: dict):
        """
        Update particle ecosystems based on resampled populations.
        """
        # Copy over unchanged particles
        # If particle from particles_dict is in new_camp_populations, keep as is
        # If particle from particles_dict is in new_camp_populations with _vX suffix,
        # copy particle from new_camp_populations and update its ecosystem
        # If particle from particles_dict is not in new_camp_populations, remove particle

        swapped_camp_populations = self.swap_dict_keys(camp_populations)
        swapped_new_camp_populations = self.swap_dict_keys(new_camp_populations)
        # print("\nSwapped camp populations\n", swapped_new_camp_populations)
        # Make a list to avoid changing dict size during iteration
        for particle in list(particles_dict.keys()):
            print("Processing particle:\n", particle)

            # Use a flag (found_suffix) to track if a _vX match was found.
            found_suffix = False
            for new_particle in swapped_new_camp_populations.keys():
                if re.fullmatch(rf"{particle}_v\d+", new_particle):
                    # Update ecosystem agent counts here as needed
                    print(f"\nCreating new particle {new_particle} from existing particle {particle}\n", )
                    # You can add your agent update logic here
                    found_suffix = True
                    # Copy particle and update ecosystem
                    particles_dict[new_particle] = particles_dict[particle].copy()
                    # Update file paths to new particle
                    for key in ['file_e', 'file_lm']:
                        particles_dict[new_particle][key] = particles_dict[new_particle][key].replace(particle, new_particle)
                    
                    # Copy existing files to new particle folder
                    root_folder_particle = os.path.join(self.current_iteration_folder, particle)
                    root_folder_new_particle = os.path.join(self.next_iteration_folder, new_particle)
                    os.makedirs(root_folder_new_particle, exist_ok=True)
                    shutil.copytree(root_folder_particle, root_folder_new_particle, dirs_exist_ok=True)
                    
                    # Compare current number of agents in each location to new_camp_populations
                    diff_dict = {}
                    diff_dict[new_particle] = {}
                    for location in swapped_new_camp_populations[new_particle]:
                        new_num = swapped_new_camp_populations[new_particle][location]
                        old_num = swapped_camp_populations[particle][location]
                        diff_dict[new_particle][location] = new_num - old_num

                    # print("\ndiff_dict\n", diff_dict)
                    particles_dict[new_particle]["e"] = self.update_agents(
                        particles_dict[new_particle]["e"],
                        particles_dict[new_particle]["lm"],
                        diff_dict[new_particle])
            
            if particle in swapped_new_camp_populations:
                print(f"\nCopying particle {particle} for next iteration.\n")
                # Copy existing files to new particle folder
                root_folder_particle = os.path.join(self.current_iteration_folder, particle)
                root_folder_new_particle = os.path.join(self.next_iteration_folder, particle)
                os.makedirs(root_folder_new_particle, exist_ok=True)
                shutil.copytree(root_folder_particle, root_folder_new_particle, dirs_exist_ok=True)
                continue  # keep as is        
            
            if not found_suffix:
                # Remove particle from dictionary
                print("Removing particle:\n", particle)
                del particles_dict[particle]

        print("\nUpdated particles dictionary:\n", particles_dict.keys())
        return particles_dict


    def update_agents(self, e, lm, location_update_dict: dict) -> None:
        """
        update a specific number of agents from each location, using a nested dictionary.
        Args:
            location_update_dict (dict): {location_name: {"update": num_to_update}}
        """
        new_agents = []
        update_counters = {loc: 0 for loc in location_update_dict}
        # In the original agents list, remove agents as needed
        e.agents
        print("agents before update:", len(e.agents))
        for i in range(0, len(e.agents)):
            loc_name = e.agents[i].location.name        
            if loc_name not in location_update_dict.keys():             
                new_agents.append(e.agents[i])  # agent is preserved
            else:
                num_to_update = location_update_dict[loc_name]
                if loc_name not in location_update_dict.keys() or (num_to_update < 0 and update_counters[loc_name] > num_to_update):
                    e.agents[i].location.DecrementNumAgents()
                    update_counters[loc_name] -= 1
                else:
                    new_agents.append(e.agents[i])  # agent is preserved
        e.agents = new_agents

        # Now add agents where needed        
        for loc_name in location_update_dict:
            num_to_update = location_update_dict[loc_name]
            if num_to_update > 0:
                for num in range(num_to_update):
                    update_counters[loc_name] += 1
                    loc = lm[loc_name]
                    attributes = spawning.draw_samples(e, loc)
                    e.addAgent(location=loc, attributes=attributes) 


        
        print("agents after update:", len(e.agents))
        return e
        

    def swap_dict_keys(self, old_dict: dict) -> dict:
        """
        Swap keys in a nested dictionary from {location: {particle_id: value}} 
        to {particle_id: {location: value}}.
        """
        new_dict = {}
        for location, particles in old_dict.items():
            for particle_id, num_agents in particles.items():
                if particle_id not in new_dict:
                    new_dict[particle_id] = {}
                new_dict[particle_id][location] = num_agents
        return new_dict
         

    # TODO: Implement data assimilation step here.
    # GOAL: Compare current number of agents in each location to observed data and adjust agent locations accordingly
    # Add in simulation setttings a flag to turn data assimilation on or off
    # Read in observed data from file or other source
    # For every location compare observed to simulated using particle filter
    # Use AddAgents, InsertAgents or Location.IncrementNumAgents to add agents to locations
    # Use clearLocationsFromAgents, Location.DecrementNumAgens, or something similar as code piece in flee at line 1683
    # to remove agents from locations
    # I am not sure what the difference between methods are, need to test and see response
    def filter(self):
        print("\nStarting data assimilation process..................................\n")
        # if SimulationSettings.spawn_rules["data_assimilation_enabled"] == True:
        # Read the days in the observation file

        # Run particles until that the next observation day

        # Load particles
        particles_dict = self.load_particles()
        print("example particle:" , particles_dict["100"])
        # Get camp populations per particle
        camp_populations = self.get_camp_populations(particles_dict)
        print("Camp populations with observations:", camp_populations)
        # print("Camp populations:", camp_populations)
        # print("-----------------Poisson test------------------")
        # weights, log_weights, ess = self.compute_particle_weights_from_dict(camp_populations, particles_dict, likelihood="poisson")
        # print("Weights:", weights)
        # print("Log Weights:", log_weights)
        # print("ESS:", ess)

        # print("-----------------Gaussian test-----------------")
        # weights, log_weights, ess = self.compute_particle_weights_from_dict(camp_populations, particles_dict, likelihood="gaussian", obs_sigma=100)
        # print("Weights:", weights)
        # print("Log Weights:", log_weights)
        # print("ESS:", ess)    

        print("------------------Lognormal test---------------")
        weights, log_weights, ess = self.compute_particle_weights_from_dict(camp_populations, 
                                                                            particles_dict, 
                                                                            likelihood="lognormal", 
                                                                            lognormal_sigma=0.56)
        print("Weights:", weights)
        print("Log Weights:", log_weights)
        print("ESS:", ess) 
        
        N = len(weights)
        ess_threshold = N / 2.0  # common rule of thumb
        print("ESS Threshold:", ess_threshold)
        if ess < ess_threshold:
            print("Resampling triggered (ESS too low).")
            resampled_ids = self.systematic_resample(weights=weights)
            print("Resampled particle IDs:", resampled_ids)

            new_camp_populations = self.resample_with_jitter(camp_populations, resampled_ids, sigma=10.0)
            # print("New camp populations after resampling with jitter:\n", new_camp_populations)

            # Update particles based on new populations
            particles_dict = self.update_particles(particles_dict, camp_populations, new_camp_populations)
            # Reset weights after resampling (equal again)
            for particle_id in particles_dict.keys():
                particles_dict[particle_id]["weight"] = 1.0 / len(particles_dict.keys())

            # Extract only the "weight" value
            weights_dict = {k: v["weight"] for k, v in particles_dict.items()}
            # save weights to json file
            with open(self.assimilation_directory + "/particle_weights.json", "w") as f:
                json.dump(weights_dict, f, indent=2)    
            print("example jittered particle:" , particles_dict["100_v2"])       
        else:
            for particle_id in particles_dict.keys():
                particles_dict[particle_id]["weight"] = weights[particle_id]
            # Extract only the "weight" value
            weights_dict = {k: v["weight"] for k, v in particles_dict.items()}
            # save weights to json file
            with open(self.assimilation_directory + "/particle_weights.json", "w") as f:
                json.dump(weights_dict, f, indent=2)  
            print("example particle (no resampling):" , particles_dict["100"])
            print("No resampling needed (ESS sufficient).")

            root_folder_particles = os.path.join(self.current_iteration_folder)
            root_folder_new_particles = os.path.join(self.next_iteration_folder)
            os.makedirs(root_folder_new_particles, exist_ok=True)
            shutil.copytree(root_folder_particles, root_folder_new_particles, dirs_exist_ok=True)

if __name__ == "__main__":
    np.random.seed(1)
    flee.SimulationSettings.ReadFromYML("data_assimilation/assimilation_test/simsetting.yml")
    pf = ParticleFilter()
    pf.filter()
    
        
            