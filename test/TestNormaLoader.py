##############################################################################
# Package: ormpy
# File:    TestNormaLoader.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.NormaLoader class """

import os
from unittest import TestCase

from lib.NormaLoader import NormaLoader

class TestNormaLoader(TestCase):
    """ Unit tests for the NormaLoader class. """

    def setUp(self):
        self.data_dir = os.getenv("ORMPY_TEST_DATA_DIR")

    def test_bad_filename_extension(self):
        """ Confirm that exception is raised when input file has .txt extension 
            rather than .orm extension. """
        with self.assertRaises(Exception) as ex:
            NormaLoader("test.txt")
        self.assertEqual(ex.exception.message, "Input filename must have .orm extension.")

    def test_bad_root_element(self):
        """ Confirm that exception is raised when the root element of the
            XML is not <ormRoot:ORM2>. """
        with self.assertRaises(Exception) as ex:
            NormaLoader(self.data_dir + "bad_root_element.orm")
        self.assertEqual(ex.exception.message, "Root of input file must be <ormRoot:ORM2>.")

    def test_no_model_element(self):
        """ Confirm that exception is raised when the XML does not contain an
            ORMModel element. 
        """
        with self.assertRaises(Exception) as ex:
            NormaLoader(self.data_dir + "no_model_element.orm")
        self.assertEqual(ex.exception.message, "Cannot find <orm:ORMModel> in input file.")

    def test_empty_model(self):
        """ Confirm a successful parse on a small input file. """
        model = NormaLoader(self.data_dir + "empty_model.orm").model
        self.assertEqual(model.num_object_types(), 0)
        self.assertEqual(model.num_fact_types(), 0)
        self.assertEqual(model.num_constraints(), 0)


    def test_omit_subtype_derivation(self):
        """ Confirm that subtype derivation rule omission note
            is added to self.omissions. """
        loader = NormaLoader(self.data_dir + "subtype_with_derivation.orm")
        self.assertItemsEqual(loader.omissions, ["Subtype derivation rule for B"])

    def test_load_object_types(self):
        """ Test of object type load. """
        loader = NormaLoader(self.data_dir + "object_type_tests.orm")
        model = loader.model

        # No derivation rules
        self.assertItemsEqual(loader.omissions, [])

        # Independent Entity
        this = model.get_object_type("D") 
        self.assertTrue(this.independent)
        self.assertEquals(this.identifier, "_5D7B0A6D-EF11-43C0-9EB3-398933165BC4")

        # Non-independent Entity
        this = model.get_object_type("C")
        self.assertFalse(this.independent)

        # Independent value
        this = model.get_object_type("V2")
        self.assertTrue(this.independent)
        self.assertEquals(this._id, "_FD295AC2-D845-48E4-9E09-2E48EC99E3F3")

        # Non-independent value
        this = model.get_object_type("V1")
        self.assertFalse(this.independent)

        # Implicit value (created by unary fact type): should not be loaded
        this = model.get_object_type("A exists")
        self.assertIsNone(this)

        # Objectified Independent
        this = model.get_object_type("CHasV1")
        self.assertTrue(this.independent)

        # Objectified Non-independent
        this = model.get_object_type("V1HasV2")
        self.assertFalse(this.independent)
        self.assertEquals(this.identifier, "_CC5D22B1-DBA7-4383-80F2-29CEAE58A998")
        self.assertEquals(this.nested_fact_type, "_B6D10F36-FFE2-4B86-BEA4-02F7FCA655F9")

        # Implicit Objectified
        this = model.get_object_type("V1HasDHasV2") # Created by ternary, should not load
        self.assertIsNone(this)
        


        
        
 
        
