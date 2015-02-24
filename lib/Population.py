##############################################################################
# Package: ormpy
# File:    Population.py
# Author:  Matthew Nizol
##############################################################################

""" Module to generate a population of an ORM model. """

import sys
from lib.ORMMinus import ORMMinus

class Population(object):
    """ A population of an ORM model. If the model is satisfiable, 
        then self.object_types and self.fact_types will contain the
        populations of objects and facts, respectively, that satisfy the
        constraints in the model.  For an unsatisfiable model, 
        self.object_types and self.fact_types will both be None."""

    DEFAULT_SIZE = 10 #: Default size of object and fact type populations.

    def __init__(self, model, ubound=DEFAULT_SIZE):
        super(Population, self).__init__()
        self._model = model

        #: A dictionary of object type populations.  Specifically, the key is
        #: the object type name and the value is a list of objects.
        self.object_types = {}  

        #: A dictionary of fact type populations.  Specifically, the key is the
        #: fact type name and the value is a :class:`lib.Population.Relation`.
        self.fact_types = {} 
   
        self.populate(ubound=ubound)

    def populate(self, ubound=DEFAULT_SIZE):
        """ Generate a population for the model. """
        solution = ORMMinus(self._model, ubound=ubound).check()

        if solution == None:
            self.object_types = None
            self.fact_types = None
        else:
            self._populate_object_types(solution)
            self._populate_fact_types(solution)

    def _populate_object_types(self, solution):
        """ Populate all object types in the model. """

        for obj_type in self._model.object_types:
            name = obj_type.fullname
            domain = obj_type.domain
            size = solution[name]             
            self.object_types[name] = list(domain.draw(size))

    def _populate_fact_types(self, solution):
        pass

    def write_csv(self, directory):
        pass

class Relation(list):
    """ A relation, which is a list of lists of identical arity. """
    
    def __init__(self, arity=1):
        super(Relation, self).__init__()
        self.arity = arity

    def add(self, tupl):
        """ Add tuple to the list. """
        if len(tupl) == self.arity:
            self.append(tupl)
        else:
            raise Exception("Cannot add tuple of arity " + str(len(tupl)) +
                            " to a Relation of arity " + str(self.arity))



