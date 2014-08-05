##############################################################################
# Package: ormpy
# File:    TestNormaLoader.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.NormaLoader class """

import os
from unittest import TestCase
from datetime import datetime, date, time

from lib.NormaLoader import NormaLoader
import lib.ObjectType as ObjectType

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
        self.assertEqual(model.object_types.count(), 0)
        self.assertEqual(model.fact_types.count(), 0)
        self.assertEqual(model.constraints.count(), 0)


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
        
        # Overall count
        self.assertEqual(model.object_types.count(), 10)

        # Independent Entity
        this = model.object_types.get("D") 
        self.assertTrue(this.independent)
        self.assertEquals(this.identifying_constraint, "_5D7B0A6D-EF11-43C0-9EB3-398933165BC4")
        self.assertIsInstance(this, ObjectType.EntityType)

        # Non-independent Entity
        this = model.object_types.get("C")
        self.assertFalse(this.independent)

        # Independent value
        this = model.object_types.get("V2")
        self.assertTrue(this.independent)
        self.assertEquals(this.uid, "_FD295AC2-D845-48E4-9E09-2E48EC99E3F3")
        self.assertIsInstance(this, ObjectType.ValueType)

        # Non-independent value
        this = model.object_types.get("V1")
        self.assertFalse(this.independent)

        # Implicit value (created by unary fact type): should not be loaded
        this = model.object_types.get("A exists")
        self.assertIsNone(this)

        # Objectified Independent
        this = model.object_types.get("CHasV1")
        self.assertTrue(this.independent)
        self.assertIsInstance(this, ObjectType.ObjectifiedType)

        # Objectified Non-independent
        this = model.object_types.get("V1HasV2")
        self.assertFalse(this.independent)
        self.assertEquals(this.identifying_constraint, "_CC5D22B1-DBA7-4383-80F2-29CEAE58A998")
        self.assertEquals(this.nested_fact_type, "_B6D10F36-FFE2-4B86-BEA4-02F7FCA655F9")

        # Implicit Objectified
        this = model.object_types.get("V1HasDHasV2") # Created by ternary, should not load
        self.assertIsNone(this)

    def test_data_type_load(self):
        """ Confirm data types are loaded properly for Value Types. """
        model = NormaLoader(self.data_dir + "data_types.orm").model
        ot = model.object_types

        self.assertIsInstance(ot.get("A").data_type, int) # data type undefined
        self.assertIsInstance(ot.get("B").data_type, bool)      # True or false
        self.assertIsInstance(ot.get("C").data_type, bool)      # Yes or no
        self.assertIsInstance(ot.get("D").data_type, int)       # auto counter
        self.assertIsInstance(ot.get("E").data_type, float)     # float
        self.assertIsInstance(ot.get("F").data_type, float)     # money
        self.assertIsInstance(ot.get("G").data_type, int)       # big int
        self.assertIsInstance(ot.get("H").data_type, datetime)  # timestamp
        self.assertIsInstance(ot.get("I").data_type, date)      # date
        self.assertIsInstance(ot.get("J").data_type, time)      # time
        self.assertIsInstance(ot.get("K").data_type, str)       # text

        # Confirm scale and length are read
        special = ot.get("Special")
        self.assertIsInstance(special.data_type, float)  # float
        self.assertEquals(special.data_type_scale, "35")
        self.assertEquals(special.data_type_length, "29")

    def test_unknown_data_type(self):
        """ Confirm that data type defaults to int() if the actual type 
            is unexpected. """
        model = NormaLoader(self.data_dir + "unknown_data_types.orm").model
        self.assertIsInstance(model.object_types.get("A").data_type, int)
        self.assertIsInstance(model.object_types.get("B").data_type, int)

        

    
        


        
        
 
        
