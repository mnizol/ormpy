##############################################################################
# Package: ormpy
# File:    ModelElement.py
# Author:  Matthew Nizol
##############################################################################

""" ModelElement.py provides an abstract class for a model element (a generic
    element in a model from which an object type, fact type, and constraint
    can be derived) as well as an abstract class for a set of model elements.
"""

import uuid

class ModelElement(object):
    """ An abstract element in an ORM model. """

    def __init__(self, uid=None, name="", *args, **kwargs):
        super(ModelElement, self).__init__(*args, **kwargs)

        # The UID (Unique ID) and Name cannot change once the model element
        # is created.  Therefore, it is defined as a ready-only property.
        self._uid = uid or uuid.uuid4().hex
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

    def commit(self):
        """ Commit any side effects of adding this model element to a model.
            This is an abstract method that must be implemented for each 
            subclass of ModelElement. """
        raise NotImplementedError()

    def rollback(self):
        """ Rollback any side effects of adding this model element to a model.
            This is an abstract method that must be implemented for each 
            subclass of ModelElement. """
        raise NotImplementedError()

class ModelElementSet(object):
    """ A set of model elements. """

    def __init__(self, name="Model Elements", *args, **kwargs):
        super(ModelElementSet, self).__init__(*args, **kwargs)
        self._set = {}
        self.name = name #: The name of the set. May be used for display, etc.

    def __iter__(self):
        """ Permit iteration over the set. """
        return self._set.itervalues()

    def add(self, element):
        """ Add an element to the set. If the name exists in the set, rename
            the element by adding an integer suffix to make it unique in
            the set.  For example, if an element named Person is added
            three times, the set will contain Person, Person2, and Person3. """
        i = 2
        name = element.name

        while element.name in self._set:
            element._name = name + str(i) # Need to access underlying _name
            i = i + 1

        self._set[element.name] = element

    def remove(self, element):
        """ Remove element from the set, if it is present. """
        try:
            del self._set[element.name]
        except KeyError:
            pass

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
