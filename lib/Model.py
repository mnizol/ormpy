##############################################################################
# Package: ormpy
# File:    Model.py
# Author:  Matthew Nizol
##############################################################################

""" Model.py provides a class to store a simplified ORM model
    consisting of a set of object types, a set of fact types, and a set of
    constraints.
"""

from lib.ObjectType import ObjectTypeSet, ObjectType
from lib.FactType import FactTypeSet, FactType
from lib.Constraint import ConstraintSet, Constraint

class Model(object):
    """ Simplified representation of an ORM model. """

    def __init__(self):
        #: The set of object types in the model
        #: (:class:`lib.ObjectType.ObjectTypeSet`)
        self.object_types = ObjectTypeSet()

        #: The set of fact types in the model
        #: (:class:`lib.FactType.FactTypeSet`)
        self.fact_types = FactTypeSet()

        #: The set of constraints in the model
        #: (:class:`lib.Constraint.ConstraintSet`)
        self.constraints = ConstraintSet()

    def get(self, full_name):
        """ Get a model element by name from the model. """
        if full_name.startswith('ObjectTypes.'):
            _set = self.object_types
        elif full_name.startswith('FactTypes.'):
            _set = self.fact_types
        elif full_name.startswith('Constraints.'):
            _set = self.constraints
        else:
            _set = None

        return _set.get(full_name.partition(".")[2]) if _set else None

    def add(self, model_element):
        """ Add a model element to the model. """        
        self._container_for(model_element).add(model_element)
        model_element.commit() # Commit side effects (if any)

    def remove(self, model_element):
        """ Remove the model element from the model. """
        self._container_for(model_element).remove(model_element)        
        model_element.rollback() # Rollback side effects (if any)

    def display(self):
        """ Prints the model to stdout. """
        self.object_types.display()
        self.fact_types.display()
        self.constraints.display()

    def _container_for(self, model_element):
        """ Return the appropriate container for the model element. """
        if isinstance(model_element, ObjectType):
            return self.object_types
        elif isinstance(model_element, FactType):
            return self.fact_types
        elif isinstance(model_element, Constraint):
            return self.constraints
        else:
            raise ValueError("Unexpected model element type")


