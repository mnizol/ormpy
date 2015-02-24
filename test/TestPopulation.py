##############################################################################
# Package: ormpy
# File:    TestPopulation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Population module. """

import os

from unittest import TestCase

import lib.TestDataLocator as TestDataLocator
from lib.Population import Population, Relation
from lib.NormaLoader import NormaLoader

class TestPopulation(TestCase):
    """ Unit tests for the Population module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

    def test_unsat_model(self):
        """ Test population of an unsatisfiable model. """
        fname = os.path.join(self.data_dir, "unsat_smarag_2.orm")
        model = NormaLoader(fname).model
        pop = Population(model)
        self.assertIsNone(pop.object_types)
        self.assertIsNone(pop.fact_types)  

    def test_populate_object_types(self):
        """ Test population of object types. """
        fname = os.path.join(self.data_dir, "fact_type_tests.orm")
        model = NormaLoader(fname).model
        pop = Population(model, ubound=5)

        pop1 = pop.object_types["ObjectTypes.A"]
        self.assertItemsEqual(pop1, ["A0", "A1", "A2", "A3", "A4"])

        pop2 = pop.object_types["ObjectTypes.A_id"]
        self.assertItemsEqual(pop2, [0, 1, 2, 3, 4])

        pop3 = pop.object_types["ObjectTypes.B"]
        self.assertItemsEqual(pop3, ["A", "Dog", "3.567", "12/23/2014"])

    def test_add_to_relation(self):
        """ Test adding tuple to relation. """
        rel = Relation(arity=2)
        rel.add([4, 5])
        rel.add(["a", "b"])

        self.assertEquals(len(rel), 2)
        self.assertItemsEqual(rel[0], [4,5])
        self.assertItemsEqual(rel[1], ["a","b"])

    def test_add_wrong_arity_to_relation(self):
        """ Test adding a tuple of the wrong arity to a relation. """
        rel = Relation(arity=2)
        
        with self.assertRaises(Exception) as ex:
            rel.add([1])
        self.assertEquals(ex.exception.message, 
            "Cannot add tuple of arity 1 to a Relation of arity 2")


  
              

