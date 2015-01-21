##############################################################################
# Package: ormpy
# File:    ORMMinus.py
# Author:  Matthew Nizol
##############################################################################

""" Module to implement ORMMinus satisfiability and population algorithm. """

import sys
from lib.InequalitySystem import *

class ORMMinus(object):
    """ Implements ORMMinus algorithm (Smaragdakis et al.). 
    
        :param model: A :class:`lib.Model.Model` to instantiate
        :param ubound: Upper bound on size of model elements
    """

    def __init__(self, model=None, ubound=sys.maxint):
        self._model = model #: ORM model
        self._ubound = ubound #: Bound on model element size
        self._ineqsys = InequalitySystem() #: System of inequalities
        self._variables = {} #: Dictionary from model element to variable

    def check(self):
        """ Checks model for satisifiability.  Returns true if satisfiable and
            false otherwise. """

        self._create_variables()

    def _create_variables(self):
        """ Create set of variables to be used in system of inequalities. """

        for obj_type in self._model.object_types:
            self._variables[obj_type] = Variable(obj_type.fullname, 
                                                 upper=self._ubound)

        for fact_type in self._model.fact_types:
            self._variables[fact_type] = Variable(fact_type.fullname, 
                                                  upper=self._ubound)

            for role in fact_type.roles:
                self._variables[role] = Variable(role.fullname, 
                                                 upper=self._ubound)

