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

##############################################################################
# Utility functions
##############################################################################
def file_lines(filename):
    with open(filename, 'r') as infile:
        contents = [line for line in infile.readlines() if line != "\n"]
    return contents
       
