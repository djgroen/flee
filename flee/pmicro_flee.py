import numpy as np
import sys
import random
from flee.SimulationSettings import SimulationSettings
from flee import pflee
# from flee import micro_flee as flee
from mpi4py import MPI
from mpi4py.MPI import ANY_SOURCE


class MPIManager(pflee.MPIManager):

    def __init__(self):
        super().__init__()


class Person(pflee.Person):

    def __init__(self, e, location):
        super().__init__(e, location)


class Location(pflee.Location):

    def __init__(self, e, cur_id, name, x=0.0, y=0.0, movechance=0.001, capacity=-1, pop=0, foreign=False, country="unknown"):
        super().__init__(e, cur_id, name, x, y, movechance, capacity, pop, foreign, country)


class Link(pflee.Link):

    def __init__(self, startpoint, endpoint, distance, forced_redirection=False, link_type=None):
        super().__init__(startpoint, endpoint, distance, forced_redirection)
        self.link_type = link_type


class Ecosystem(pflee.Ecosystem):

    def __init__(self):
        super().__init__()

    def linkUp(self, endpoint1, endpoint2, distance="1.0", forced_redirection=False, link_type=None):
        """ Creates a link between two endpoint locations
        """
        endpoint1_index = -1
        endpoint2_index = -1
        for i in range(0, len(self.locationNames)):
            if(self.locationNames[i] == endpoint1):
                endpoint1_index = i
            if(self.locationNames[i] == endpoint2):
                endpoint2_index = i

        if endpoint1_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print("Error: link created to non-existent source: ",
                  endpoint1, " with dest ", endpoint2)
            sys.exit()
        if endpoint2_index < 0:
            print("Diagnostic: Ecosystem.locationNames: ", self.locationNames)
            print("Error: link created to non-existent destination: ",
                  endpoint2, " with source ", endpoint1)
            sys.exit()

        self.locations[endpoint1_index].links.append(
            Link(self.locations[endpoint1_index],
                 self.locations[endpoint2_index],
                 distance,
                 forced_redirection,
                 link_type
                 )
        )
        self.locations[endpoint2_index].links.append(
            Link(
                self.locations[endpoint2_index],
                self.locations[endpoint1_index],
                distance
            )
        )

if __name__ == "__main__":
    print("No testing functionality here yet.")
