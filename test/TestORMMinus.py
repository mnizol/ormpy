##############################################################################
# Package: ormpy
# File:    TestORMMinus.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.ORMMinus module. """

import os

from unittest import TestCase

import lib.TestDataLocator as TestDataLocator
from lib.ORMMinus import ORMMinus
from lib.InequalitySystem import Constant
from lib.NormaLoader import NormaLoader
import lib.Constraint as Constraint

class TestORMMinus(TestCase):
    """ Unit tests for the ORMMinus module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

        fname = os.path.join(self.data_dir, "paper_has_author.orm")
        model = NormaLoader(fname).model
        self.paper_has_author = ORMMinus(model=model)
        self.solution1 = self.paper_has_author.check()

    def test_overlapping_and_external_iuc(self):
        """ Test that overlapping and external IUCs are ignored. """
        fname = os.path.join(self.data_dir, "overlapping_iuc.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinus(model=model)
        solution = ormminus.check()

        actual_vars = [var.name for var in ormminus._variables.itervalues()]

        expected_vars = ["ObjectTypes.ValueType1",
                         "ObjectTypes.ValueType2",
                         "ObjectTypes.ValueType3",
                         "FactTypes.ValueType1HasValueType3HasValueType2",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.R1",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.R2",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.R3",
                         "FactTypes.ValueType1HasValueType3",
                         "FactTypes.ValueType1HasValueType3.Roles.R1",
                         "FactTypes.ValueType1HasValueType3.Roles.R2",
                         "FactTypes.ValueType3HasValueType2",
                         "FactTypes.ValueType3HasValueType2.Roles.R1",
                         "FactTypes.ValueType3HasValueType2.Roles.R2",
                         "Constraints.IUC2",
                         "Constraints.IUC3",
                         "Constraints.IUC4"]

        self.assertItemsEqual(actual_vars, expected_vars)

        actual_ignored = [cons.name for cons in ormminus.ignored]
        expect_ignored = ["IUC1", "EUC1"]

        self.assertItemsEqual(actual_ignored, expect_ignored) 

    def test_disjunctive_mandatory(self):
        """ Test that disjunctive mandatory constraint is ignored. """
        fname = os.path.join(self.data_dir, "disjunctive_mandatory.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinus(model=model)

        # NormaLoader actually drops the disjunctive mandatory, so create a
        # fake one to test that the constraint is ignored
        cons = Constraint.MandatoryConstraint(name="Cons1")
        cons.cover(model.fact_types.get("EntityType1A").roles[0])
        cons.simple = False
        model.constraints.add(cons)

        solution = ormminus.check()

        actual = [cons.name for cons in ormminus.ignored]
        expected = ["Cons1"]

        self.assertItemsEqual(actual, expected)  
        
    def test_create_variables(self):
        """ Test creation of variables dictionary. """
        actual_vars = [var.name for var in 
                       self.paper_has_author._variables.itervalues()]
        expect_vars = ["ObjectTypes.Paper",
                       "ObjectTypes.Author",
                       "FactTypes.PaperHasAuthor",
                       "FactTypes.PaperHasAuthor.Roles.R1",
                       "FactTypes.PaperHasAuthor.Roles.R2",
                       "Constraints.FrequencyConstraint1",
                       "Constraints.InternalUniquenessConstraint1"]

        self.assertItemsEqual(actual_vars, expect_vars)

    def test_create_inequalities_1(self):
        """ Test creation of inequalities for Paper Has Author model. """
        actual = [ineq.tostring() for ineq in self.paper_has_author._ineqsys]

        expect = ["FactTypes.PaperHasAuthor.Roles.R1 <= ObjectTypes.Paper",
                  "FactTypes.PaperHasAuthor.Roles.R1 <= FactTypes.PaperHasAuthor",
                  "FactTypes.PaperHasAuthor.Roles.R2 <= ObjectTypes.Author",
                  "FactTypes.PaperHasAuthor.Roles.R2 <= FactTypes.PaperHasAuthor",
                  "ObjectTypes.Paper <= 10",
                  "ObjectTypes.Author <= 5",
                  "ObjectTypes.Author <= FactTypes.PaperHasAuthor.Roles.R2",
                  "FactTypes.PaperHasAuthor <= 3 * Constraints.FrequencyConstraint1",
                  "Constraints.FrequencyConstraint1 <= 0.5 * FactTypes.PaperHasAuthor",
                  "Constraints.FrequencyConstraint1 <= FactTypes.PaperHasAuthor.Roles.R1",
                  "FactTypes.PaperHasAuthor.Roles.R1 <= Constraints.FrequencyConstraint1",
                  "FactTypes.PaperHasAuthor <= Constraints.InternalUniquenessConstraint1",
                  "Constraints.InternalUniquenessConstraint1 <= FactTypes.PaperHasAuthor",
                  "Constraints.InternalUniquenessConstraint1 <= FactTypes.PaperHasAuthor.Roles.R2",
                  "FactTypes.PaperHasAuthor.Roles.R2 <= Constraints.InternalUniquenessConstraint1",
                  "ObjectTypes.Paper <= FactTypes.PaperHasAuthor.Roles.R1",
                  "ObjectTypes.Author <= FactTypes.PaperHasAuthor.Roles.R2"]

        self.assertItemsEqual(actual, expect)

    def test_solve_1(self):
        """ Test solution to Paper Has Author model. """
        actual = [(name, var.upper) for name, var in self.solution1.iteritems() if not(isinstance(var, Constant))]
        
        expect = [("ObjectTypes.Author", 5),
                  ("ObjectTypes.Paper", 2),
                  ("FactTypes.PaperHasAuthor", 5),
                  ("FactTypes.PaperHasAuthor.Roles.R1", 2),
                  ("FactTypes.PaperHasAuthor.Roles.R2", 5),
                  ("Constraints.FrequencyConstraint1", 2),
                  ("Constraints.InternalUniquenessConstraint1", 5)
                 ]

        self.assertItemsEqual(actual, expect)

    def test_implicit_disjunctive_ineq(self):
        """ Test implicit disjunctive mandatory inequalities. """
        fname = os.path.join(self.data_dir, "implicit_disjunctive_test.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinus(model=model)
        solution = ormminus.check()

        actual = [ineq.tostring() for ineq in ormminus._ineqsys]

        expect = ["FactTypes.ALikesA.Roles.R1 <= ObjectTypes.A",
                  "FactTypes.ALikesA.Roles.R1 <= FactTypes.ALikesA",
                  "FactTypes.ALikesA.Roles.R2 <= ObjectTypes.A",
                  "FactTypes.ALikesA.Roles.R2 <= FactTypes.ALikesA",
                  "FactTypes.ASharesB.Roles.R3 <= ObjectTypes.A",
                  "FactTypes.ASharesB.Roles.R3 <= FactTypes.ASharesB",
                  "FactTypes.ASharesB.Roles.R4 <= ObjectTypes.B",
                  "FactTypes.ASharesB.Roles.R4 <= FactTypes.ASharesB",
                  "FactTypes.AOwnsD.Roles.R5 <= ObjectTypes.A",
                  "FactTypes.AOwnsD.Roles.R5 <= FactTypes.AOwnsD",
                  "FactTypes.AOwnsD.Roles.R6 <= ObjectTypes.D",
                  "FactTypes.AOwnsD.Roles.R6 <= FactTypes.AOwnsD",
                  "FactTypes.ALikesA <= Constraints.IUC1",
                  "Constraints.IUC1 <= FactTypes.ALikesA",
                  "Constraints.IUC1 <= FactTypes.ALikesA.Roles.R1",
                  "FactTypes.ALikesA.Roles.R1 <= Constraints.IUC1",
                  "FactTypes.ASharesB <= Constraints.IUC2",
                  "Constraints.IUC2 <= FactTypes.ASharesB",
                  "Constraints.IUC2 <= FactTypes.ASharesB.Roles.R3",
                  "FactTypes.ASharesB.Roles.R3 <= Constraints.IUC2",
                  "FactTypes.AOwnsD <= Constraints.IUC3",
                  "Constraints.IUC3 <= FactTypes.AOwnsD",
                  "Constraints.IUC3 <= FactTypes.AOwnsD.Roles.R5",
                  "FactTypes.AOwnsD.Roles.R5 <= Constraints.IUC3",
                  "ObjectTypes.A <= FactTypes.AOwnsD.Roles.R5 + FactTypes.ASharesB.Roles.R3 + FactTypes.ALikesA.Roles.R1 + FactTypes.ALikesA.Roles.R2",
                  "ObjectTypes.D <= FactTypes.AOwnsD.Roles.R6" 
                 ]
        
        self.assertItemsEqual(actual, expect)

    def test_unsat_smarag_2(self):
        """ Test 2nd unsatisfiable model provided by Smaragdakis. """
        fname = os.path.join(self.data_dir, "unsat_smarag_2.orm")
        model = NormaLoader(fname).model
        self.assertIsNone(ORMMinus(model=model).check())

    def test_unsat_smarag_3(self):
        """ Test 3rd unsatisfiable model provided by Smaragdakis. """
        fname = os.path.join(self.data_dir, "unsat_smarag_3.orm")
        model = NormaLoader(fname).model
        self.assertIsNone(ORMMinus(model=model).check())

