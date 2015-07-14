##############################################################################
# Package: ormpy
# File:    TestLogiQL.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.generators.LogiQL module. """
from __future__ import print_function

from unittest import TestCase
import tempfile
import shutil
import os

import lib.TestDataLocator as TestData

from lib.generators.LogiQL import LogiQL
from lib.NormaLoader import NormaLoader
from lib.Model import Model
from lib.ORMMinusModel import ORMMinusModel
from lib.Population import Population

class TestLogiQL(TestCase):
    """ Unit tests for the LogiQL module. """

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.tempdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tempdir)

    def test_remove_ignored_constraints(self):
        """ Test that ignored constraints are removed. """
        model = NormaLoader(TestData.path("omitted_constraints.orm")).model
        model2 = ORMMinusModel(model)
        pop = Population(model2)

        tempdir = os.path.join(self.tempdir, "test_remove_ignored_constraints")
        logiql = LogiQL(model, pop, tempdir, make=False)

        self.assertEquals(len(logiql.constraints), 4)

        actual = [c.name for c in logiql.constraints]
        expected = ["InternalUniquenessConstraint1",
                    "InternalUniquenessConstraint2",
                    "InternalUniquenessConstraint3",
                    "InternalUniquenessConstraint4"]

        self.assertItemsEqual(actual, expected)

    def test_create_directories(self):
        """ Test that appropriate directories get created. """
        model = Model()
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_create_directories")

        # Directory doesn't exist before call
        self.assertFalse(os.path.isdir(tempdir))

        logiql = LogiQL(model, pop, tempdir, make=False)

        # Directory and expected sub-directories now exist
        self.assertTrue(os.path.isdir(tempdir))
        self.assertEquals(tempdir, logiql.rootdir)
        self.assertTrue(os.path.isdir(logiql.importdir))
        self.assertTrue(os.path.isdir(logiql.logicdir))

    def test_create_directory_exception(self):
        """ Test exception case in _create_directory. """
        model = Model()
        pop = Population(ORMMinusModel(model))

        try:
            handle, filename = tempfile.mkstemp()
            with self.assertRaises(OSError): # filename is a file, not a dir
                LogiQL(model, pop, filename, make=False)
        finally:
            os.remove(filename)

    def test_project_file(self):
        """ Test contents of .project file. """
        model = NormaLoader(TestData.path("empty_model.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_project_file")

        logiql = LogiQL(model, pop, tempdir, make=False)
        
        projfile = os.path.join(tempdir, "test_project_file.project")
        self.assertTrue(os.path.exists(projfile))

        with open(projfile, 'r') as infile:
            actual = infile.readlines()

        expected = ["test_project_file, projectname\n",
                    "model, module\n",
                    "import.logic, execute\n"]

        self.assertItemsEqual(actual, expected)

    def test_project_file_no_import(self):
        """ Test contents of .project file. """
        model = NormaLoader(TestData.path("empty_model.orm")).model

        tempdir = os.path.join(self.tempdir, "test_project_file_no_import")

        # Important: population is None here
        logiql = LogiQL(model, None, tempdir, make=False)
        
        projfile = os.path.join(tempdir, "test_project_file_no_import.project")
        self.assertTrue(os.path.exists(projfile))

        with open(projfile, 'r') as infile:
            actual = infile.readlines()

        expected = ["test_project_file_no_import, projectname\n",
                    "model, module\n"]

        self.assertItemsEqual(actual, expected)

    def test_config_file(self):
        """ Test contents of config.py file. """
        model = NormaLoader(TestData.path("empty_model.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_config_file")

        logiql = LogiQL(model, pop, tempdir, make=False)
        
        config_file = os.path.join(tempdir, "config.py")

        self.assertTrue(os.path.exists(config_file))

        with open(config_file, "r") as infile:
            actual = infile.readlines()

        expected = ["from lbconfig.api import *\n",
                    "lbconfig_package('test_config_file', version='0.1', default_targets=['lb-libraries'])\n",
                    "depends_on(logicblox_dep)\n",
                    "lb_library(name='test_config_file', srcdir='.')\n",
                    "check_lb_workspace(name='test_config_file', libraries=['test_config_file'])\n"]

        self.assertItemsEqual(actual, expected)

    def test_empty_model(self):
        """ Test that empty model produces empty model directory. """
        model = NormaLoader(TestData.path("empty_model.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_empty_model")

        logiql = LogiQL(model, pop, tempdir, make=False)

        model_dir = os.path.join(tempdir, "model")
        self.assertTrue(os.path.isdir(model_dir))
        self.assertEquals(0, len(os.listdir(model_dir)))

    def test_types_without_subtype(self):
        """ Test writing out of types without any subtypes present. """
        model = NormaLoader(TestData.path("objectification.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_types_without_subtype")

        logiql = LogiQL(model, pop, tempdir, make=False)

        types_file = os.path.join(tempdir, "model", "types.logic")
        
        with open(types_file, 'r') as infile:
            actual = infile.readlines()

        expected = ["block(`types) {\n",
                    "  export(`{\n",
                    "    A(x), A_constructor(x: v) -> string(v).\n",
                    "\n",
                    "    B(x), B_constructor(x: v) -> string(v).\n",
                    "\n",
                    "    AHasB(x), AHasB_constructor(x: v) -> string(v).\n",
                    "\n",
                    "    ALikesB(x), ALikesB_constructor(x: v) -> string(v).\n",
                    "\n",
                    "    AEnjoysB(x), AEnjoysB_constructor(x: v) -> string(v).\n",
                    "\n",
                    "  })\n",
                    "} <-- .\n"]

        self.assertItemsEqual(actual, expected)

    def test_subtypes(self):
        """ Test writing out of subtypes. """
        model = NormaLoader(TestData.path("object_type_tests.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_subtypes")

        logiql = LogiQL(model, pop, tempdir, make=False)

        types_file = os.path.join(tempdir, "model", "types.logic")
        
        with open(types_file, 'r') as infile:
            actual = [line for line in infile.readlines() if line != "\n"]

        expected = ["block(`types) {\n",
                    "  export(`{\n",
                    "    A(x), A_constructor(x: v) -> string(v).\n",
                    "    A_id(x), A_id_constructor(x: v) -> string(v).\n",
                    "    B(x) -> A(x).\n",
                    "    C(x) -> B(x).\n", 
                    "    CHasV1(x), CHasV1_constructor(x: v) -> string(v).\n",
                    "    V1(x), V1_constructor(x: v) -> string(v).\n",
                    "    V2(x), V2_constructor(x: v) -> string(v).\n",
                    "    V1HasV2(x), V1HasV2_constructor(x: v) -> string(v).\n",
                    "    D(x), D_constructor(x: v) -> string(v).\n",
                    "    D_id(x), D_id_constructor(x: v) -> string(v).\n",
                    "  }),\n",
                    "  clauses(`{\n",
                    "    lang:entity(`B).\n",
                    "    lang:entity(`C).\n",
                    "  })\n",
                    "} <-- .\n"]

        self.assertItemsEqual(actual, expected)

    def test_fact_types(self):
        """ Test writing out of fact types (predicates). """
        model = NormaLoader(TestData.path("fact_type_tests.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_fact_types")

        logiql = LogiQL(model, pop, tempdir, make=False)

        preds_file = os.path.join(tempdir, "model", "predicates.logic")
        
        with open(preds_file, 'r') as infile:
            actual = [line for line in infile.readlines() if line != "\n"]
        
        expected = ["block(`predicates) {\n",
                    "  export(`{\n",
                    "    AHasB(A, B) -> model:types:A(A), model:types:B(B).\n",
                    "    AHasAId(A, A_id) -> model:types:A(A), model:types:A_id(A_id).\n",
                    "    AExists(A) -> model:types:A(A).\n",
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_ternary_fact_type(self):
        """ Test writing out of ternary fact types (predicates). """
        model = NormaLoader(TestData.path("canonical_example.orm")).model
        pop = Population(ORMMinusModel(model))

        tempdir = os.path.join(self.tempdir, "test_ternary_fact_type")

        logiql = LogiQL(model, pop, tempdir, make=False)

        preds_file = os.path.join(tempdir, "model", "predicates.logic")
        
        with open(preds_file, 'r') as infile:
            actual = [line for line in infile.readlines() if line != "\n"]
        
        expected = ["block(`predicates) {\n",
                    "  export(`{\n",
                    "    AAndBLikeC(A, B, C) -> model:types:A(A), model:types:B(B), model:types:C(C).\n",
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_mandatory_constraint(self):
        """ Test writing out of mandatory constraints. """
        model = NormaLoader(TestData.path("mandatory_constraint_2.orm")).model
        tempdir = os.path.join(self.tempdir, "test_mandatory_constraint")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // SimpleMandatoryConstraint4\n",
                    "    model:types:B(x) -> model:predicates:BHasC(x, _).\n",
                    "    // InclusiveOrConstraint2\n",
                    "    model:types:C(x) -> model:predicates:CLikesC(x, _); model:predicates:CLikesC(_, x).\n",
                    "    // InclusiveOrConstraint3\n",
                    "    model:types:C(x) -> model:predicates:CHasDHasD(x, _, _); model:predicates:CLikesC(_, x).\n",
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_value_constraint(self):
        """ Test writing out of value constraints. """
        model = NormaLoader(TestData.path("value_constraints.orm")).model
        tempdir = os.path.join(self.tempdir, "test_value_constraint")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // ValueTypeValueConstraint1\n",
                    '    model:types:A_constructor(_:v) -> v="1"; v="2"; v="3"; v="4"; v="5".\n',
                    '    // RoleValueConstraint1\n',
                    '    model:predicates:AAndBHaveC(_, x, _), model:types:B_constructor(x:v) -> v="7"; v="8"; v="9".\n',
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_internal_uniq_constraint(self):
        """ Test writing out of internal uniqueness constraints. """
        model = NormaLoader(TestData.path("uniqueness_constraints_2.orm")).model
        tempdir = os.path.join(self.tempdir, "test_internal_uniq_constraint")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // InternalUniquenessConstraint1\n",
                    "    model:predicates:AHasB(A_, B_), model:predicates:AHasB(A_, B_2) -> B_ = B_2.\n",
                    "    // InternalUniquenessConstraint6\n",
                    "    model:predicates:BHasC(B_, C_), model:predicates:BHasC(B_, C_) -> .\n",
                    "    // InternalUniquenessConstraint5\n",
                    "    model:predicates:AHasBHasC(A_, B_, C_), model:predicates:AHasBHasC(A_, B_2, C_) -> B_ = B_2.\n",
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_euc_linear(self):
        """ Test writing out of linear EUC constraints. """
        model = NormaLoader(TestData.path("join_rule_valid_linear_path_euc.orm")).model

        # Remove all but EUC
        to_delete = [c for c in model.constraints if c.name != "EUC"]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_euc_linear")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // EUC\n",

                    ("    JoinFact_EUC(AHasB_A, CHasD_D, AHasB_B, BHasC_B, BHasC_C, CHasD_C) <-"
                         " model:predicates:AHasB(AHasB_A, AHasB_B)," 
                         " model:predicates:BHasC(BHasC_B, BHasC_C),"
                         " model:predicates:CHasD(CHasD_C, CHasD_D),"
                         " AHasB_B = BHasC_B,"
                         " BHasC_C = CHasD_C.\n")
,
                    ("JoinFact_EUC(AHasB_A_, CHasD_D_, AHasB_B_, BHasC_B_, BHasC_C_, CHasD_C_), "
                     "JoinFact_EUC(AHasB_A_, CHasD_D_, AHasB_B_2, BHasC_B_2, BHasC_C_2, CHasD_C_2) -> "
                     "AHasB_B_ = AHasB_B_2, "
                     "BHasC_B_ = BHasC_B_2, "
                     "BHasC_C_ = BHasC_C_2, "
                     "CHasD_C_ = CHasD_C_2.\n"),

                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_euc_branching(self):
        """ Test writing out of branching EUC constraints. """
        model = NormaLoader(TestData.path("join_rule_valid_complex_branching_path.orm")).model

        # Remove all but EUC
        to_delete = [c for c in model.constraints if c.name != "EUC1"]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_euc_branching")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // EUC1\n",

                    ("    JoinFact_EUC1(DHasE_D, FHasG_F, HHasG_H, BHasC_C, "
                                        "DHasE_E, EHasB_E, EHasB_B, GHasB_G, "
                                        "GHasB_B, FHasG_G, HHasG_G, BHasC_B) <-"
                         " model:predicates:DHasE(DHasE_D, DHasE_E)," 
                         " model:predicates:EHasB(EHasB_E, EHasB_B),"
                         " model:predicates:GHasB(GHasB_G, GHasB_B),"
                         " model:predicates:FHasG(FHasG_F, FHasG_G),"
                         " model:predicates:HHasG(HHasG_H, HHasG_G),"
                         " model:predicates:BHasC(BHasC_B, BHasC_C),"
                         " DHasE_E = EHasB_E,"
                         " EHasB_B = GHasB_B,"
                         " GHasB_G = FHasG_G,"
                         " GHasB_G = HHasG_G,"
                         " EHasB_B = BHasC_B.\n")
,
                    ("JoinFact_EUC1(DHasE_D_, FHasG_F_, HHasG_H_, BHasC_C_, "
                                    "DHasE_E_, EHasB_E_, EHasB_B_, GHasB_G_, "
                                    "GHasB_B_, FHasG_G_, HHasG_G_, BHasC_B_), "
                     "JoinFact_EUC1(DHasE_D_, FHasG_F_, HHasG_H_, BHasC_C_, "
                                    "DHasE_E_2, EHasB_E_2, EHasB_B_2, GHasB_G_2, "
                                    "GHasB_B_2, FHasG_G_2, HHasG_G_2, BHasC_B_2) -> "
                     "DHasE_E_ = DHasE_E_2, "
                     "EHasB_E_ = EHasB_E_2, "
                     "EHasB_B_ = EHasB_B_2, "
                     "GHasB_G_ = GHasB_G_2, "
                     "GHasB_B_ = GHasB_B_2, "
                     "FHasG_G_ = FHasG_G_2, "
                     "HHasG_G_ = HHasG_G_2, "
                     "BHasC_B_ = BHasC_B_2.\n"),

                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_euc_covering_left_join_role(self):
        """ Test writing EUC constraint that covers the left role in a join. """
        model = NormaLoader(TestData.path("euc_covering_join_role.orm")).model

        # Remove all but EUC
        to_delete = [c for c in model.constraints if c.name != "EUC"]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_euc_covering_left_join_role")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // EUC\n",

                    ("    JoinFact_EUC(AHasDHasB_A, AHasDHasB_B, BHasDHasC_C, "
                                      "AHasDHasB_D, BHasDHasC_B, BHasDHasC_D) <-"
                         " model:predicates:AHasDHasB(AHasDHasB_A, AHasDHasB_D, AHasDHasB_B)," 
                         " model:predicates:BHasDHasC(BHasDHasC_B, BHasDHasC_D, BHasDHasC_C),"
                         " AHasDHasB_B = BHasDHasC_B.\n")
,
                    ("JoinFact_EUC(AHasDHasB_A_, AHasDHasB_B_, BHasDHasC_C_, "
                                  "AHasDHasB_D_, BHasDHasC_B_, BHasDHasC_D_), "
                     "JoinFact_EUC(AHasDHasB_A_, AHasDHasB_B_, BHasDHasC_C_, "
                                  "AHasDHasB_D_2, BHasDHasC_B_2, BHasDHasC_D_2) -> "
                     "AHasDHasB_D_ = AHasDHasB_D_2, "
                     "BHasDHasC_B_ = BHasDHasC_B_2, "
                     "BHasDHasC_D_ = BHasDHasC_D_2.\n"),

                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_subset(self):
        """ Test writing subset constraints. """
        model = NormaLoader(TestData.path("subset_constraint.orm"), deontic=True).model

        # Remove all but SubsetConstraint1
        to_delete = [c for c in model.constraints if not c.name.startswith("SubsetConstraint")]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_subset")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // SubsetConstraint1\n",
                    "    model:predicates:AHasB(_0, _) -> model:predicates:ALikesB(_0, _).\n",
                    "    // SubsetConstraint2\n",
                    "    model:predicates:ALikesB(_, _0) -> model:predicates:AHasB(_, _0).\n",
                    "    // SubsetConstraint3\n",
                    "    model:predicates:CPlusAPlusB(_2, _0, _1) -> model:predicates:AAndBAndC(_0, _1, _2).\n",
                    "    // SubsetConstraint4\n",
                    "    model:predicates:CPlusAPlusB(_, _0, _1) -> model:predicates:AAndBAndC(_0, _1, _).\n",
                    "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_subset_2(self):
        """ Test writing subset constraints. """
        model = NormaLoader(TestData.path("subset_constraint_2.orm"), deontic=True).model

        # Remove all but SubsetConstraints
        to_delete = [c for c in model.constraints if not c.name.startswith("SubsetConstraint")]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_subset_2")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // SubsetConstraint1\n",
                    "    model:predicates:AAndBAndC(_0, _, _1) -> model:predicates:CAndBAndA(_1, _, _0).\n",
                     "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_join_subset(self):
        """ Test writing join subset constraints. """
        model = NormaLoader(TestData.path("join_subset_simple.orm")).model

        # Remove all but SubsetConstraints
        to_delete = [c for c in model.constraints if not c.name.startswith("SUB")]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_join_subset")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // SUB\n",

                    ("    JoinFact_SUB_subset(AHasB_A, BHasC_C, AHasB_B, BHasC_B) <- "
                          "model:predicates:AHasB(AHasB_A, AHasB_B), "
                          "model:predicates:BHasC(BHasC_B, BHasC_C), "
                          "AHasB_B = BHasC_B.\n"),

                     "JoinFact_SUB_subset(_0, _1, _, _) -> model:predicates:AHasC(_0, _1).\n",
                     "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

    def test_join_subset_2(self):
        """ Test writing join subset constraints. """
        model = NormaLoader(TestData.path("join_subset_simple_2.orm")).model

        # Remove all but SubsetConstraints
        to_delete = [c for c in model.constraints if not c.name.startswith("SUB")]
        for cons in to_delete: 
            model.constraints.remove(cons)

        tempdir = os.path.join(self.tempdir, "test_join_subset_2")
        logiql = LogiQL(model, None, tempdir, make=False)

        actual = file_lines(os.path.join(tempdir, "model", "constraints.logic"))
        
        expected = ["block(`constraints) {\n",
                    "  clauses(`{\n", 
                    "    // Dummy constraint\n",
                    "    string(x) -> string(x).\n",
                    "    // SUB\n",

                    ("    JoinFact_SUB_subset(AHasB_A, BHasC_C, AHasB_B, BHasC_B) <- "
                          "model:predicates:AHasB(AHasB_A, AHasB_B), "
                          "model:predicates:BHasC(BHasC_B, BHasC_C), "
                          "AHasB_B = BHasC_B.\n"),

                    ("JoinFact_SUB_superset(AHasE_A, EHasD_D, AHasE_E, EHasD_E) <- "
                          "model:predicates:AHasE(AHasE_A, AHasE_E), "
                          "model:predicates:EHasD(EHasD_E, EHasD_D), "
                          "AHasE_E = EHasD_E.\n"),

                     "JoinFact_SUB_subset(_0, _1, _, _) -> JoinFact_SUB_superset(_0, _1, _, _).\n",
                     "  })\n",
                    "} <-- .\n"]
        
        self.assertItemsEqual(actual, expected)

##############################################################################
# Utility functions
##############################################################################
def file_lines(filename):
    with open(filename, 'r') as infile:
        contents = [line for line in infile.readlines() if line != "\n"]
    return contents
       
