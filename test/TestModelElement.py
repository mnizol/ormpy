##############################################################################
# Package: ormpy
# File:    TestModelElement.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the ModelElement and ModelElementSet
    classes. """

import sys
from unittest import TestCase

from lib.ModelElement import ModelElementSet, ModelElement

from lib.ObjectType import ObjectType
from lib.FactType import FactType
from lib.Constraint import Constraint

# ModelElement currently has no public functions, just two public properties.
# Thus, unit tests in this file are currently just for ModelElementSet.

class TestModelElementSet(TestCase):
    """ Unit tests for :class:`lib.ModelElement.ModelElementSet` """

    def setUp(self):
        self.object_type1 = ObjectType(name="Object Type 1")
        self.fact_type1 = FactType(name="Fact Type 1")
        self.constraint1 = Constraint(name="Constraint 1")
        

    def test_add_element(self):
        """ Confirm we can add elements to the set. """
        _set = ModelElementSet()

        self.assertEqual(_set.count(), 0)
        _set.add(self.object_type1)
        self.assertEqual(_set.count(), 1)

        _set.add(self.fact_type1)
        _set.add(self.constraint1)
        self.assertEqual(_set.count(), 3)

    def test_remove_element(self):
        """ Confirm we can remove elements from the set. """
        _set = ModelElementSet()
        
        _set.add(self.constraint1)
        _set.add(self.object_type1)
        _set.add(self.fact_type1)
        self.assertEqual(_set.count(), 3)
        self.assertIs(_set.get("Object Type 1"), self.object_type1)

        _set.remove(self.object_type1)
        self.assertEqual(_set.count(), 2)
        self.assertEqual(_set.get("Object Type 1"), None)

        # Try to remove an item that is already removed
        _set.remove(self.object_type1)
        self.assertEqual(_set.count(), 2)

    def test_get_element(self):
        """ Confirm we can successfully retrieve added elements. """
        _set = ModelElementSet()

        _set.add(self.fact_type1)
        _set.add(self.constraint1)
        
        result = _set.get("Constraint 1")
        self.assertEqual(result, self.constraint1)
        self.assertIsInstance(result, Constraint)

    def test_get_missing_elements(self):
        """ Confirm a request for a non-existent element returns None."""
        _set = ModelElementSet()
        self.assertIsNone(_set.get("Does not exist"))

    def test_rename(self):
        """ Confirm items with same name added to set get renamed. """
        _set = ModelElementSet()
        _set.add(ObjectType(name="Item"))
        _set.add(FactType(name="Item"))
        _set.add(FactType(name="Item"))
        self.assertEqual(_set.count(), 3)
        self.assertIsInstance(_set.get("Item"), ObjectType)
        self.assertIsInstance(_set.get("Item2"), FactType)
        self.assertIsInstance(_set.get("Item3"), FactType)

    def test_display_empty(self):
        """ Test display of empty set. """
        _set = ModelElementSet(name="Elements")
        _set.display()
        output = sys.stdout.getvalue().strip() 
        self.assertEqual(output, "Elements:")

    def test_display_nonempty(self):
        """ Test display of non-empty set."""
        _set = ModelElementSet()
        _set.add(ObjectType(name="GHI"))
        _set.add(ObjectType(name="XYZ"))
        _set.add(ObjectType(name="ABC"))
        _set.display()

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, "Model Elements:\n    ABC\n    GHI\n    XYZ")

    def test_commit(self):
        """ Confirm commit raises NotImplementedError."""
        el = ModelElement()
        with self.assertRaises(NotImplementedError) as ex:
            el.commit()

    def test_rollback(self):
        """ Confirm rollback raises NotImplementedError."""
        el = ModelElement()
        with self.assertRaises(NotImplementedError) as ex:
            el.rollback()
        
        



