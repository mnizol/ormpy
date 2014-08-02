##############################################################################
# Package: ormpy
# File:    TestModel.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Model class """

from unittest import TestCase

from lib.Model import Model
from lib.ObjectType import ObjectType
from lib.FactType import FactType
from lib.Constraint import Constraint

class TestModel(TestCase):
    """ Unit tests for the Model class. """

    def setUp(self):
        self.object_type1 = ObjectType()
        self.object_type1.name = "Object Type 1"

        self.fact_type1 = FactType()
        self.fact_type1.name = "Fact Type 1"

        self.constraint1 = Constraint()
        self.constraint1.name = "Constraint 1"

    def test_add_object_type(self):
        """ Confirm we can add an object type to the model. """
        model = Model()
        self.assertEqual(model.num_object_types(), 0)
        model.add(self.object_type1)
        self.assertEqual(model.num_object_types(), 1)
        self.assertIsNotNone(model.get_object_type("Object Type 1"))

    def test_add_fact_type(self):
        """ Confirm we can add a fact type to the model. """
        model = Model()
        self.assertEqual(model.num_fact_types(), 0)
        model.add(self.fact_type1)
        self.assertEqual(model.num_fact_types(), 1)
        self.assertIsNotNone(model.get_fact_type("Fact Type 1"))

    def test_add_constraint(self):
        """ Confirm we can add a constraint to the model. """
        model = Model()
        self.assertEqual(model.num_constraints(), 0)
        model.add(self.constraint1)
        self.assertEqual(model.num_constraints(), 1)
        self.assertIsNotNone(model.get_constraint("Constraint 1"))

    def test_add_invalid(self):
        """ Confirm we cannot add something invalid to the model. """
        model = Model()
        self.assertEqual(model.num_object_types(), 0)
        model.add("Invalid")
        self.assertEqual(model.num_object_types(), 0)

    def test_get_missing_elements(self):
        """ Confirm a request for a non-existent element returns None."""
        model = Model()
        self.assertIsNone(model.get_object_type("Does not exist"))
        self.assertIsNone(model.get_fact_type("Does not exist"))
        self.assertIsNone(model.get_constraint("Does not exist"))
