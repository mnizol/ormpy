##############################################################################
# Package: ormpy
# File:    Constraint.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class for ORM constraints.  
"""

from lib.ModelElement import ModelElementSet, ModelElement

class ConstraintSet(ModelElementSet):
    """ Container for a set of constraints. """

    def __init__(self):
        super(ConstraintSet, self).__init__(name="Constraints")

class Constraint(ModelElement):
    """ An ORM Constraint. """

    def __init__(self, uid=None, name=None):
        super(Constraint, self).__init__(uid=uid, name=name)