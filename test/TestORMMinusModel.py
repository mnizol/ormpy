##############################################################################
# Package: ormpy
# File:    TestORMMinusModel.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.ORMMinusModel module. """

import os
import sys

from unittest import TestCase
from nose.plugins.logcapture import LogCapture

import lib.TestDataLocator as TestDataLocator
from lib.ORMMinusModel import ORMMinusModel
from lib.InequalitySystem import Constant
from lib.NormaLoader import NormaLoader
import lib.Constraint as Constraint

class TestORMMinusModel(TestCase):
    """ Unit tests for the ORMMinusModel module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()
        self.maxDiff = None

        # Log capturing
        self.log = LogCapture()
        self.log.logformat = '%(levelname)s: %(message)s'
        self.log.begin()

        fname = os.path.join(self.data_dir, "paper_has_author.orm")
        model = NormaLoader(fname).model
        self.paper_has_author = ORMMinusModel(model=model)
        self.solution1 = self.paper_has_author.solution

    def test_overlapping_and_external_iuc(self):
        """ Test that overlapping and external IUCs are ignored. """        
        fname = os.path.join(self.data_dir, "overlapping_iuc.orm")
        model = NormaLoader(fname).model

        self.log.beforeTest(None)
        ormminus = ORMMinusModel(model=model)
        solution = ormminus.solution

        actual_vars = [var.name for var in ormminus._variables.itervalues()]

        expected_vars = ["ObjectTypes.ValueType1",
                         "ObjectTypes.ValueType2",
                         "ObjectTypes.ValueType3",
                         "FactTypes.ValueType1HasValueType3HasValueType2",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.ValueType1",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.ValueType2",
                         "FactTypes.ValueType1HasValueType3HasValueType2.Roles.ValueType3",
                         "FactTypes.ValueType1HasValueType3",
                         "FactTypes.ValueType1HasValueType3.Roles.ValueType1",
                         "FactTypes.ValueType1HasValueType3.Roles.ValueType3",
                         "FactTypes.ValueType3HasValueType2",
                         "FactTypes.ValueType3HasValueType2.Roles.ValueType3",
                         "FactTypes.ValueType3HasValueType2.Roles.ValueType2",
                         "Constraints.IUC2",
                         "Constraints.IUC3",
                         "Constraints.IUC4"]

        self.assertItemsEqual(actual_vars, expected_vars)

        actual_ignored = [cons.name for cons in ormminus.ignored]
        expect_ignored = ["IUC1", "EUC1"]

        self.assertItemsEqual(actual_ignored, expect_ignored) 

        self.assertItemsEqual(self.log.formatLogRecords(),
            ["WARNING: 1 model element was ignored while loading overlapping_iuc.orm.",
             "INFO: Ignored Join path for EUC1.",
             "WARNING: 2 constraints were ignored while checking the model.",
             "INFO: Ignored UniquenessConstraint named IUC1.",
             "INFO: Ignored UniquenessConstraint named EUC1."])

        self.log.afterTest(None)

    def test_disjunctive_mandatory(self):
        """ Test that disjunctive mandatory constraint is ignored. """
        fname = os.path.join(self.data_dir, "disjunctive_mandatory.orm")
        model = NormaLoader(fname).model

        # NormaLoader actually drops the disjunctive mandatory, so create a
        # fake one to test that the constraint is ignored
        cons = Constraint.MandatoryConstraint(name="Cons1")
        role1 = model.fact_types.get("EntityType1A").roles[0]
        role2 = model.fact_types.get("EntityType1B").roles[0]
        cons.covers = [role1, role2]        
        model.add(cons)

        ormminus = ORMMinusModel(model=model)
        solution = ormminus.solution

        actual = [cons.name for cons in ormminus.ignored]
        expected = ["Cons1"]

        self.assertItemsEqual(actual, expected)  
        
    def test_ignored_constraint(self):
        """ Test that appropriate constraints are ignored. """

        # IMPORTANT: I expect this test to fail when I update algorithm to
        # work with subset constraints.  At that point, CHANGE this test to
        # check that a different kind of constraint (e.g. Exclusion) is 
        # ignored.  That will require updating NormaLoader to load such
        # constraints rather than omitting them.

        fname = os.path.join(self.data_dir, "subset_constraint.orm")
        model = NormaLoader(fname, deontic=True).model
        ormminus = ORMMinusModel(model=model)
        solution = ormminus.solution

        actual = [cons.name for cons in ormminus.ignored]
        expect = ["SubsetConstraint1", "SubsetConstraint2", "SubsetConstraint3", "SubsetConstraint4"]
        self.assertItemsEqual(actual, expect)

    def test_ignored_value_constraint(self):
        """ Test that role value constraints are ignored. """
        fname = os.path.join(self.data_dir, "test_value_type_value_constraint.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model=model)
        solution = ormminus.solution 

        actual = [cons.name for cons in ormminus.ignored]
        expect = ["RVC_ET3", "RVC_ET4", "RVC_ET5", "RVC_VT2"]
        self.assertItemsEqual(actual, expect)               

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
        actual = set([ineq.tostring() for ineq in self.paper_has_author._ineqsys])

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
                  "FactTypes.PaperHasAuthor <= Constraints.FrequencyConstraint1 * Constraints.InternalUniquenessConstraint1"]

        self.assertItemsEqual(actual, expect)

    def test_solve_1(self):
        """ Test solution to Paper Has Author model. """
        solution = self.solution1
        self.assertEquals(solution["ObjectTypes.Author"], 5)
        self.assertEquals(solution["ObjectTypes.Paper"], 2)
        self.assertEquals(solution["FactTypes.PaperHasAuthor"], 5)
        self.assertEquals(solution["FactTypes.PaperHasAuthor.Roles.R1"], 2)
        self.assertEquals(solution["FactTypes.PaperHasAuthor.Roles.R2"], 5)
        self.assertEquals(solution["Constraints.FrequencyConstraint1"], 2)
        self.assertEquals(solution["Constraints.InternalUniquenessConstraint1"], 5)

    def test_implicit_disjunctive_ineq(self):
        """ Test implicit disjunctive mandatory inequalities. """
        self.log.beforeTest(None)
        fname = os.path.join(self.data_dir, "implicit_disjunctive_test.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model=model)
        solution = ormminus.solution

        actual = set([ineq.tostring() for ineq in ormminus._ineqsys])

        expect = ["ObjectTypes.A <= " + str(ORMMinusModel.DEFAULT_SIZE),
                  "ObjectTypes.B <= " + str(ORMMinusModel.DEFAULT_SIZE),
                  "ObjectTypes.C <= " + str(ORMMinusModel.DEFAULT_SIZE),
                  "ObjectTypes.D <= " + str(ORMMinusModel.DEFAULT_SIZE),
                  "FactTypes.ALikesA.Roles.R1 <= ObjectTypes.A",
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
                  "ObjectTypes.A <= FactTypes.ALikesA.Roles.R1 + FactTypes.ALikesA.Roles.R2 + FactTypes.AOwnsD.Roles.R5 + FactTypes.ASharesB.Roles.R3",
                  "ObjectTypes.D <= FactTypes.AOwnsD.Roles.R6",
                  "FactTypes.ALikesA <= Constraints.IUC1 * FactTypes.ALikesA.Roles.R2",
                  "FactTypes.ASharesB <= Constraints.IUC2 * FactTypes.ASharesB.Roles.R4",
                  "FactTypes.AOwnsD <= Constraints.IUC3 * FactTypes.AOwnsD.Roles.R6"
                 ]
        
        self.assertItemsEqual(actual, expect)

        self.assertItemsEqual(self.log.formatLogRecords(), [])
        self.log.afterTest(None)

    def test_unsat_smarag_1(self):
        """ Test 1st unsatisfiable model provided by Smaragdakis. """
        fname = os.path.join(self.data_dir, "unsat_smarag_1.orm")
        model = NormaLoader(fname).model
        self.assertIsNone(ORMMinusModel(model=model).solution)

    def test_unsat_smarag_2(self):
        """ Test 2nd unsatisfiable model provided by Smaragdakis. """
        fname = os.path.join(self.data_dir, "unsat_smarag_2.orm")
        model = NormaLoader(fname).model
        self.assertIsNone(ORMMinusModel(model=model).solution)

    def test_unsat_smarag_3(self):
        """ Test 3rd unsatisfiable model provided by Smaragdakis. """
        fname = os.path.join(self.data_dir, "unsat_smarag_3.orm")
        model = NormaLoader(fname).model
        self.assertIsNone(ORMMinusModel(model=model).solution)

    def test_ubound_on_object_types(self):
        """ Test upper bound on object type variables.  """
        fname = os.path.join(self.data_dir, "data_types.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model=model, ubound=sys.maxsize)
        solution = ormminus.solution

        bool_obj = model.object_types.get("B")
        bool_var = ormminus._variables[bool_obj]
        self.assertEquals(bool_var.upper, 2)

        int_obj = model.object_types.get("D")
        int_var = ormminus._variables[int_obj]
        self.assertEquals(int_var.upper, sys.maxsize)

        time_obj = model.object_types.get("J")
        time_var = ormminus._variables[time_obj]
        self.assertEquals(time_var.upper, 60*24)

    def test_fact_type_parts(self):
        """ Test that fact type parts (e.g. roles vs role sequences) are 
            correctly identified. """
        fname = os.path.join(self.data_dir, "fact_type_parts.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model=model, ubound=5)

        fact_type = model.fact_types.get("V1HasV2HasV3")
        role1, role2, role3 = fact_type.roles
        self.assertItemsEqual(ormminus.get_parts(fact_type), [role1,role2,role3])

        fact_type = model.fact_types.get("V4HasV5")
        role1, role2 = fact_type.roles
        cons = model.constraints.get("IUC4")
        self.assertItemsEqual(ormminus.get_parts(fact_type), [cons,role2])

        fact_type = model.fact_types.get("V6HasV7")
        cons = model.constraints.get("IUC5")
        self.assertItemsEqual(ormminus.get_parts(fact_type), [cons])

        fact_type = model.fact_types.get("V8HasV9")
        cons = model.constraints.get("IFC1")
        self.assertItemsEqual(ormminus.get_parts(fact_type), [cons])

        fact_type = model.fact_types.get("Seven_ary")
        roles = fact_type.roles
        iuc = model.constraints.get("IUC11")
        ifc = model.constraints.get("IFC2")
        self.assertItemsEqual(ormminus.get_parts(fact_type), [iuc, ifc, roles[3], roles[6]])

    def test_cardinality_inequalities(self):
        """ Test that correct cardinality constraint inequalities are generated. """
        self.log.beforeTest(None)
        fname = os.path.join(self.data_dir, "test_cardinality_constraint.orm")
        model = NormaLoader(fname, deontic=True).model
        ormminus = ORMMinusModel(model)

        actual = set([ineq.tostring() for ineq in ormminus._ineqsys])

        expected = ["ObjectTypes.A <= " + str(ORMMinusModel.DEFAULT_SIZE),
                    "ObjectTypes.B <= " + str(ORMMinusModel.DEFAULT_SIZE), 
                    "FactTypes.AExists.Roles.A <= ObjectTypes.A",
                    "FactTypes.AExists.Roles.A <= FactTypes.AExists",
                    "FactTypes.AExists <= Constraints.IUC1",
                    "Constraints.IUC1 <= FactTypes.AExists",
                    "Constraints.IUC1 <= FactTypes.AExists.Roles.A",
                    "FactTypes.AExists.Roles.A <= Constraints.IUC1",
                    "ObjectTypes.A <= FactTypes.AExists.Roles.A",
                    "FactTypes.BDances.Roles.B <= ObjectTypes.B",
                    "FactTypes.BDances.Roles.B <= FactTypes.BDances", 
                    "FactTypes.BDances <= Constraints.IUC2",
                    "Constraints.IUC2 <= FactTypes.BDances",
                    "Constraints.IUC2 <= FactTypes.BDances.Roles.B",
                    "FactTypes.BDances.Roles.B <= Constraints.IUC2",   
                    "FactTypes.BHopes.Roles.B <= ObjectTypes.B",
                    "FactTypes.BHopes.Roles.B <= FactTypes.BHopes",
                    "FactTypes.BHopes <= Constraints.IUC3",
                    "Constraints.IUC3 <= FactTypes.BHopes",
                    "Constraints.IUC3 <= FactTypes.BHopes.Roles.B",
                    "FactTypes.BHopes.Roles.B <= Constraints.IUC3",
                    "ObjectTypes.B <= FactTypes.BDances.Roles.B + FactTypes.BHopes.Roles.B",

                    "0 <= ObjectTypes.A",
                    "ObjectTypes.A <= 4",
                    "4 <= FactTypes.AExists.Roles.A",
                    "FactTypes.AExists.Roles.A <= 7",
                    "2 <= ObjectTypes.B",
                    "4 <= FactTypes.BHopes.Roles.B",
                    "FactTypes.BHopes.Roles.B <= 4"
                   ]
        self.assertItemsEqual(actual, expected)

        self.assertItemsEqual(ormminus.ignored, [model.constraints.get("CC5")])

        self.assertItemsEqual(self.log.formatLogRecords(),
            ["WARNING: 1 constraint was ignored while checking the model.",
             "INFO: Ignored CardinalityConstraint named CC5."])

        self.log.afterTest(None)

    def test_unbounded_freq_constraint(self):
        """ Test a model with an unbounded frequency constraint. """
        fname = os.path.join(self.data_dir, "unbounded_frequency_constraint.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model)

        cons = model.constraints.get("IFC1")
        self.assertEquals(cons.max_freq, float('inf'))
        self.assertEquals(cons.min_freq, 5)

        solution = ormminus.solution
        size = ORMMinusModel.DEFAULT_SIZE
        self.assertEquals(solution["Constraints.IFC1"], size / 5)
        self.assertEquals(solution["FactTypes.AHasB"], size)

    def test_objectification_inequalities(self):
        """ Test a model with objectifications. """
        fname = os.path.join(self.data_dir, "objectification.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model, ubound=10)

        # Confirm NORMA doesn't copy the cardinality constraint to the fact type
        self.assertEquals(len(model.constraints.of_type(Constraint.CardinalityConstraint)), 1)

        # Check for existence of expected inequalities
        actual = set([ineq.tostring() for ineq in ormminus._ineqsys])
        self.assertIn("ObjectTypes.AHasB <= FactTypes.AHasB", actual)
        self.assertIn("FactTypes.AHasB <= ObjectTypes.AHasB", actual)
        self.assertIn("ObjectTypes.ALikesB <= FactTypes.ALikesB", actual)
        self.assertIn("FactTypes.ALikesB <= ObjectTypes.ALikesB", actual)
        self.assertIn("ObjectTypes.AEnjoysB <= FactTypes.AEnjoysB", actual)
        self.assertIn("FactTypes.AEnjoysB <= ObjectTypes.AEnjoysB", actual)

        # Check that solution has expected relations
        self.assertEquals(ormminus.solution["ObjectTypes.AHasB"], 
                          ormminus.solution["FactTypes.AHasB"])
        self.assertEquals(ormminus.solution["ObjectTypes.AHasB"], 10)

        self.assertEquals(ormminus.solution["ObjectTypes.ALikesB"], 
                          ormminus.solution["FactTypes.ALikesB"])
        self.assertEquals(ormminus.solution["ObjectTypes.ALikesB"], 5)

        self.assertEquals(ormminus.solution["ObjectTypes.AEnjoysB"], 
                          ormminus.solution["FactTypes.AEnjoysB"])
        self.assertEquals(ormminus.solution["ObjectTypes.AEnjoysB"], 3)

    def test_unsat_role_and_value_type_value_constraint(self):
        """ Test unsatisfiable combination of role and value type value constraint. """
        fname = os.path.join(self.data_dir, "role_value_constraint_and_type_value_constraint.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model, ubound=10)

        self.assertItemsEqual(ormminus.ignored, [])

        a_id = model.object_types.get("A_id")
        cc1 = model.constraints.get("CC1")
        rvc1 = model.constraints.get("RVC1")
        vc1 = model.constraints.get("VC1")

        value_cons = model.constraints.of_type(Constraint.ValueConstraint)
        self.assertEquals(len(value_cons), 2)
        
        self.assertItemsEqual(value_cons, [rvc1, vc1])
        self.assertEquals(rvc1.covers, [a_id])
        self.assertEquals(vc1.covers, [a_id])

        self.assertItemsEqual(a_id.covered_by, [rvc1, vc1, cc1])
    
        # Key test 1: domain of a_id is intersection of two value constraints
        self.assertItemsEqual(a_id.domain.draw(10), [1,2])

        # Key test 2: model is unsat due to cardinality constraint
        self.assertIsNone(ormminus.solution)

    def test_subtype_inequalities(self):
        """ Test that expected subtype inequalities are created. """
        fname = TestDataLocator.path("value_constraints_on_subtypes.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model, ubound=30)

        actual = set([ineq.tostring() for ineq in ormminus._ineqsys])

        self.assertIn("ObjectTypes.J <= ObjectTypes.I", actual)
        self.assertIn("ObjectTypes.L <= ObjectTypes.J", actual)
        self.assertIn("ObjectTypes.K <= ObjectTypes.I", actual)
        self.assertIn("ObjectTypes.M <= ObjectTypes.J", actual)
        self.assertIn("ObjectTypes.M <= ObjectTypes.K", actual)

        self.assertEquals(ormminus.solution["ObjectTypes.I"], 21)
        self.assertEquals(ormminus.solution["ObjectTypes.J"], 21)
        self.assertEquals(ormminus.solution["ObjectTypes.K"], 11)
        self.assertEquals(ormminus.solution["ObjectTypes.M"], 11)

    def test_unsat_subtype_with_value_constraint(self):
        """ Test a model that is unsatisfiable because the intersection of the
            value constraints for the root type and subtype is empty. """
        fname = TestDataLocator.path("unsat_subtype_with_value_constraint.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model, ubound=30)
        self.assertIsNone(ormminus.solution)

    def test_unsat_subtype_due_to_card_constraint(self):
        """ Test a model that is unsatisfiable because the cardinality of the 
            root type is less than required for one of the subtypes. """
        fname = TestDataLocator.path("unsat_subtype_due_to_card_constraint.orm")
        model = NormaLoader(fname).model
        ormminus = ORMMinusModel(model, ubound=30)
        self.assertIsNone(ormminus.solution)

        
