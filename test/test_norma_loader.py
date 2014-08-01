##############################################################################
# Package: ormpy
# File:    test_norma_loader.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.norma_loader class """

import os
from unittest import TestCase

from lib.norma_loader import norma_loader

class test_norma_loader(TestCase):
    """ Unit tests for the norma_loader class.
    """
    def setUp(self):
        self.data_dir = os.getenv("ORMPY_TEST_DATA_DIR")
        self.loader = norma_loader()

    def test_bad_filename_extension(self):
        """ Confirm that exception is raised when input file has .txt extension rather than .orm extension.
        """
        with self.assertRaises(Exception) as ex:
            self.loader.parse_norma_file("test.txt")
        self.assertEqual(ex.exception.message, "Input filename must have .orm extension.")

    def test_bad_root_element(self):
        """ Confirm that exception is raised when the root element of the XML is not <ormRoot:ORM2>.
        """
        with self.assertRaises(Exception) as ex:
            self.loader.parse_norma_file(self.data_dir + "bad_root_element.orm")
        self.assertEqual(ex.exception.message, "Root element of input file must be <ormRoot:ORM2>.")

    def test_no_model_element(self):
        """ Confirm that exception is raised when the XML does not contain an ORMModel element. 
        """
        with self.assertRaises(Exception) as ex:
            self.loader.parse_norma_file(self.data_dir + "no_model_element.orm")
        self.assertEqual(ex.exception.message, "Cannot find <orm:ORMModel> element in input file.")

    def test_successful_parse(self):
        """ Confirm a successful parse on a small input file.
        """
        root = self.loader.parse_norma_file(self.data_dir + "empty_model.orm")
        self.assertEqual(root.tag, self.loader.NS_CORE + "ORMModel")
        self.assertEqual(root.get("Name"), "empty_test_model")

