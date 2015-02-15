##############################################################################
# Package: ormpy
# File:    Population.py
# Author:  Matthew Nizol
##############################################################################

""" Module to generate a population of an ORM model. """

import sys
from lib.ORMMinus import ORMMinus

class Population(object):
    """ A population of an ORM model. """

    def __init__(self, model):
        self._model = model
        self.object_types = {}
        self.fact_types = {}
        self.populate()

    def populate(self, ubound=sys.maxint):
        """ Generate a population for the model.  If the model is satisfiable, 
            then self.object_types and self.fact_types will be 
            dictionaries whose key is the object_type (fact_type) name and
            whose value is a :class:`lib.Relation.Relation` that satisfies the
            constraints in the model.  If the model is unsatisfiable, then 
            self.object_types and self.fact_types will both be set to None. """

        solution = ORMMinus(self._model, ubound=ubound).check()

        if solution == None:
            self.object_types = None
            self.fact_types = None
        else:
            self._populate_object_types(solution)
            self._populate_fact_types(solution)

    def _populate_object_types(self, solution):
        # (1) Populate any object type with a ValueConstraint by drawing
        #     from that ValueConstraint
        # (2) Populate ValueType by drawing from its domain
        # (3) Populate EntityType as Name<n>
        # (4) Populate sub types per Smarag
        pass

    def _populate_fact_types(self, solution):
        pass

    def write_csv(self, directory):
        pass

