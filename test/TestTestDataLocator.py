##############################################################################
# Package: ormpy
# File:    TestTestDataLocator.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.TestDataLocator module. """

import os

from unittest import TestCase
import lib.TestDataLocator as TestDataLocator

class TestTestDataLocator(TestCase):
    def setup():
        pass

    def test_get_data_dir(self):
        """ Confirm get_data_dir() can locate one of our test files """
        dirname = TestDataLocator.get_data_dir()
        fname = os.path.join(dirname, "fact_type_tests.orm")
        self.assertTrue(os.path.isfile(fname))


