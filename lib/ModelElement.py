##############################################################################
# Package: ormpy
# File:    ModelElement.py
# Author:  Matthew Nizol
##############################################################################

""" ModelElement.py provides an abstract class for a model element (a generic
    element in a model from which an object type, fact type, and constraint
    can be derived) as well as an abstract class for a set of model elements. 
"""

class ModelElement(object):
    """ An abstract element in an ORM model. """
    
    def __init__(self, uid=None, name=None):
        # The UID (Unique ID) and Name cannot change once the model element
        # is created.  Therefore, it is defined as a ready-only property.
        self._uid = uid
        self._name = name

    @property
    def uid(self):
        """ Unique identifier for the model element. Cannot be changed
            after the model element is created. """
        return self._uid

    @property
    def name(self):
        """ Unique name for the model element. Cannot be changed after
            the model element is created. """
        return self._name


class ModelElementSet(object):
    """ A set of model elements. """

    def __init__(self, name="Model Elements"):
        self._set = {}
        self.name = name #: The name of the set. May be used for display, etc.

    def add(self, element):
        """ Add an element to the set. """
        self._set[element.name] = element

    def get(self, name):
        """ Retrieve an element by name.  Returns **None** if the element is 
            not in the set. """
        try:
            return self._set[name]
        except KeyError:
            return None 

    def count(self):
        """ Returns the number of items in the set. """
        return len(self._set)

    def display(self):
        """ Display the set of elements to **stdout**. """
        print "{0}:".format(self.name)
        for element_name in sorted(list(self._set)):
            print " "*3, element_name # 4 leading spaces