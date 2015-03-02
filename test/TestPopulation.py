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

    def test_populate_roles(self):
        """ Test population of roles. """
        fname = os.path.join(self.data_dir, "populate_roles.orm")
        model = NormaLoader(fname).model
        pop = Population(model, ubound=10)

        # Test role played by an object type that plays no other roles.
        pop1 = pop._roles["FactTypes.VT1HasVT2.Roles.R1"]
        self.assertItemsEqual(pop1, [[1],[2],[3],[4],[5]])

        # Test population of two roles played by same object type such that
        # the role populations are complete and disjoint.
        pop2a = pop._roles["FactTypes.VT1HasVT2.Roles.R2"]
        pop2b = pop._roles["FactTypes.VT2HasVT7.Roles.R1"]
        self.assertItemsEqual(pop2a, [[1],[2],[3],[4],[5]])
        self.assertItemsEqual(pop2b, [[6],[7]])

        # Test population of object type that plays enough roles that its
        # objects appear in more than one role population.
        pop3a = pop._roles["FactTypes.VT3HasVT4.Roles.R2"]
        pop3b = pop._roles["FactTypes.VT4HasVT5.Roles.R1"]
        pop3c = pop._roles["FactTypes.VT4HasVT6.Roles.R1"]
        self.assertItemsEqual(pop3a, [[1],[2]])
        self.assertItemsEqual(pop3b, [[3],[4],[5],[1],[2]])
        self.assertItemsEqual(pop3c, [[3],[4],[5]])

        # Test population of independent object type whose population is not
        # fully exhausted.
        pop4 = pop._roles["FactTypes.VT4HasVT5.Roles.R2"]
        self.assertItemsEqual(pop4, [[1],[2],[3],[4],[5]])

    def test_fact_type_parts(self):
        """ Calling pop on fact_type_parts.orm was crashing.  Confirm it 
            no longer crashes. """
        fname = os.path.join(self.data_dir, "fact_type_parts.orm")
        model = NormaLoader(fname).model
        pop = Population(model, ubound=10)
        self.assertTrue(True) # Just want to ensure test doesn't crash

#####################################################################
# Tests for Relation Class
#####################################################################
class TestRelation(TestCase):
    """ Unit tests for the Relation class. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

    def test_add_to_relation(self):
        """ Test adding tuple to relation. """
        rel = Relation(["col1", "col2"])
        rel.add([4, 5])
        rel.add(["a", "b"])

        self.assertEquals(rel.arity, 2)
        self.assertEquals(len(rel), 2)
        self.assertItemsEqual(rel[0], [4,5])
        self.assertItemsEqual(rel[1], ["a","b"])

    def test_add_wrong_arity_to_relation(self):
        """ Test adding a tuple of the wrong arity to a relation. """
        rel = Relation(["col1", "col2"])
        
        with self.assertRaises(Exception) as ex:
            rel.add([1])
        self.assertEquals(ex.exception.message, 
            "Cannot add tuple of arity 1 to a Relation of arity 2")


  
              

