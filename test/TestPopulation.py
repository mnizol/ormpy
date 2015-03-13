##############################################################################
# Package: ormpy
# File:    TestPopulation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Population module. """

import os, sys
from StringIO import StringIO

from unittest import TestCase

import lib.TestDataLocator as TestDataLocator
from lib.ORMMinusModel import ORMMinusModel
from lib.Population import Population, Relation, lcm
from lib.NormaLoader import NormaLoader

class TestPopulation(TestCase):
    """ Unit tests for the Population module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()
        self.maxDiff = None

    def test_unsat_model(self):
        """ Test population of an unsatisfiable model. """
        fname = os.path.join(self.data_dir, "unsat_smarag_2.orm")
        model = ORMMinusModel(NormaLoader(fname).model)

        with self.assertRaises(ValueError) as ex:
            pop = Population(model)

        self.assertEquals(ex.exception.message, 
                          "Cannot populate an unsatisfiable model.")

    def test_populate_object_types(self):
        """ Test population of object types. """
        fname = os.path.join(self.data_dir, "fact_type_tests.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=5)
        pop = Population(model)

        pop1 = pop.object_types["ObjectTypes.A"]
        self.assertItemsEqual(pop1, ["A0", "A1", "A2", "A3", "A4"])

        pop2 = pop.object_types["ObjectTypes.A_id"]
        self.assertItemsEqual(pop2, [0, 1, 2, 3, 4])

        pop3 = pop.object_types["ObjectTypes.B"]
        self.assertItemsEqual(pop3, ["A", "Dog", "3.567", "12/23/2014"])

    def test_populate_roles(self):
        """ Test population of roles. """
        fname = os.path.join(self.data_dir, "populate_roles.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=10)
        pop = Population(model)

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
        model = ORMMinusModel(NormaLoader(fname).model, ubound=10)
        pop = Population(model)
        self.assertTrue(True) # Just want to ensure test doesn't crash

    def test_populate_role_sequences_and_fact_types(self):
        """ Test population of role sequences and fact types. """
        fname = os.path.join(self.data_dir, "populate_fact_types.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=6)
        pop = Population(model)

        pop1 = pop._roles["Constraints.IFC1"]
        self.assertItemsEqual(pop1, [[1, 'B1'],[2,'B2'],[3,'B3']])

        # Note, pop of B role starts with B4 because previous B role was
        # already instantiated with B1,B2,B3
        pop2 = pop._roles["Constraints.IUC1"]
        self.assertItemsEqual(pop2, [['B4','C1','C1'], ['B5','C2','C2'],
                                     ['B1','C3','C3'], ['B2','C4','C4'],
                                     ['B3','C1','C1'], ['B4','C2','C2']])

        pop3 = pop._roles["FactTypes.AHasBBCCD.Roles.R6"]
        self.assertItemsEqual(pop3, [[False],[True]])

        # Population of whole predicate
        pop4 = pop.fact_types["FactTypes.AHasBBCCD"]
        self.assertItemsEqual(pop4, [[1, 'B1', 'B4', 'C1', 'C1', False],
                                     [2, 'B2', 'B5', 'C2', 'C2', True],
                                     [3, 'B3', 'B1', 'C3', 'C3', False],
                                     [1, 'B1', 'B2', 'C4', 'C4', True],
                                     [2, 'B2', 'B3', 'C1', 'C1', False],
                                     [3, 'B3', 'B4', 'C2', 'C2', True]])
        self.assertEquals(pop4.names, ['R1','R2','R3','R4','R5','R6'])

        
    def test_ignored_overlapping_iuc(self):
        """ Test that overlapping IUC is ignored while populating fact type. """
        fname = os.path.join(self.data_dir, "populate_fact_types.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=6)
        pop = Population(model)

        self.assertIsNone(pop._roles.get("Constraints.IUC2", None))
        self.assertIsNotNone(pop._roles.get("Constraints.IUC3", None))        
        
    def test_population_with_no_fact_types(self):
        """ Test population with no fact types. """
        fname = os.path.join(self.data_dir, "no_fact_types.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=5)
        pop = Population(model)

        self.assertItemsEqual(pop.object_types["ObjectTypes.A"], [0,1,2,3,4])

    def test_write_stdout(self):
        """ Test writing population to stdout. """    
        fname = os.path.join(self.data_dir, "populate_fact_types.orm")
        model = ORMMinusModel(NormaLoader(fname).model, ubound=6)
        pop = Population(model)

        saved = sys.stdout
        sys.stdout = StringIO()

        pop.write_stdout() # Method under test

        actual = sys.stdout.getvalue().split('\n\n') # Double newline separates
                                                     # different populations
       
        expected = ['Population of ObjectTypes.A:\n' + \
                   '1\n2\n3',

                   'Population of ObjectTypes.B:\n' + \
                   'B1\nB2\nB3\nB4\nB5', 

                   'Population of ObjectTypes.C:\n' + \
                   'C1\nC2\nC3\nC4',

                   'Population of ObjectTypes.D:\n' + \
                   'False\nTrue', 

                   'Population of ObjectTypes.E:\n' + \
                   '1',

                   'Population of ObjectTypes.F:\n' + \
                   '2',

                   'Population of ObjectTypes.G:\n' + \
                   '3',

                   'Population of FactTypes.AHasBBCCD:\n' + \
                   'R1,R2,R3,R4,R5,R6\n' + \
                   '1,B1,B4,C1,C1,False\n' + \
                   '2,B2,B5,C2,C2,True\n' + \
                   '3,B3,B1,C3,C3,False\n' + \
                   '1,B1,B2,C4,C4,True\n' + \
                   '2,B2,B3,C1,C1,False\n' + \
                   '3,B3,B4,C2,C2,True',

                   'Population of FactTypes.EHasFG:\n' + \
                   'R1,R3,R2\n' + \
                   '1,3,2',

                    '']
                   
        self.assertItemsEqual(actual, expected)
        
        sys.stdout = saved

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

    def test_combine_with_nullary(self):
        """ Test combining a nullary relation with another relation. """
        null_rel = Relation([])
        bin_rel = Relation(['one','two'])

        self.assertIs(null_rel.combine_with(bin_rel, 100), bin_rel)
        self.assertIs(bin_rel.combine_with(null_rel, 100), bin_rel)

    def test_combine_with_0_tuple(self):
        """ Test combining a non-empty relation with an empty relation. """

        rel1 = Relation(['col1'])
        rel2 = Relation(['col2'])

        rel2.add([1])
        rel2.add([2])

        self.assertEquals(len(rel1), 0)
        self.assertEquals(len(rel2), 2)

        rel3 = rel1.combine_with(rel2, 100)
        self.assertEquals(rel3.arity, 2)
        self.assertEquals(rel3.names, ['col1', 'col2'])
        self.assertEquals(len(rel3), 0)

        rel4 = rel2.combine_with(rel1, 100)
        self.assertEquals(rel4.arity, 2)
        self.assertEquals(rel4.names, ['col2', 'col1'])
        self.assertEquals(len(rel4), 0)

    def test_combine_with(self):
        """ Test combine_with under various settings for n. """
        
        src = Relation(['col1'])
        tgt = Relation(['col2'])

        for i in xrange(4): src.add([i])
        for i in xrange(6): tgt.add([i])

        # n < |src|
        result = src.combine_with(tgt, 3)
        self.assertEquals(result, [[0,0], [1,1], [2,2]])

        # n < |tgt|
        result = src.combine_with(tgt, 5)
        self.assertEquals(result, [[0,0], [1,1], [2,2], [3,3], [0,4]])

        # n <= lcm(src,tgt)
        result = src.combine_with(tgt, 12)
        self.assertEquals(result, [[0,0], [1,1], [2,2], [3,3], [0,4],
                                   [1,5], [2,0], [3,1], [0,2], [1,3],
                                   [2,4], [3,5]])

        # lcm(src,tgt) < n < |s| x |t|
        result = src.combine_with(tgt, 14)
        self.assertEquals(result, [[0,0], [1,1], [2,2], [3,3], [0,4],
                                   [1,5], [2,0], [3,1], [0,2], [1,3],
                                   [2,4], [3,5], [0,1], [1,2]])

        # n == |s| x |t|
        result = src.combine_with(tgt, 24)
        self.assertEquals(result, [[0,0], [1,1], [2,2], [3,3], [0,4],
                                   [1,5], [2,0], [3,1], [0,2], [1,3],
                                   [2,4], [3,5], [0,1], [1,2], [2,3],
                                   [3,4], [0,5], [1,0], [2,1], [3,2],
                                   [0,3], [1,4], [2,5], [3,0]])

        # n > |s| x |t|
        self.assertEquals(src.combine_with(tgt, 24),
                          src.combine_with(tgt, 10000))

        # n == 0
        result = src.combine_with(tgt, 0)
        self.assertEquals(result.arity, 2)
        self.assertEquals(len(result), 0)

    def test_combine_with_multiple_shifts(self):
        """ Test case when cyclic shift has to occur more than once. """
        
        src = Relation(['col1'])
        tgt = Relation(['col2'])

        for i in xrange(3): src.add([i])
        for i in xrange(3): tgt.add([i])

        result = src.combine_with(tgt, 9)
        self.assertEquals(result, [[0,0], [1,1], [2,2],
                                   [0,1], [1,2], [2,0],
                                   [0,2], [1,0], [2,1]])

       

#####################################################################
# Tests for Utility Functions
#####################################################################
class TestUtility(TestCase):
    """ Unit tests for utility functions. """

    def setUp(self):
        pass

    def test_lcm(self):
        """ Test least common multiple function. """
        self.assertEquals(lcm(3,4), 12)
        self.assertEquals(lcm(0,1), 0)
        self.assertEquals(lcm(1,0), 0)
        self.assertEquals(lcm(2,4), 4)
        self.assertEquals(lcm(4,6), 12)
  
              

