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
from lib.NormaLoader import NormaLoader

class TestORMMinus(TestCase):
    """ Unit tests for the ORMMinus module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

    def test_create_variables(self):
        """ Test creation of variables dictionary. """
        fname = os.path.join(self.data_dir, "fact_type_tests.orm")
        model = NormaLoader(fname).model
        orm = ORMMinus(model=model)
        orm.check()

        for var in orm._variables.itervalues():
            print var.name
