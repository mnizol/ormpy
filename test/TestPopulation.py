##############################################################################
# Package: ormpy
# File:    TestPopulation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Population module. """

import os

from unittest import TestCase

import lib.TestDataLocator as TestDataLocator
from lib.Population import Population
from lib.NormaLoader import NormaLoader

class TestPopulation(TestCase):
    """ Unit tests for the Population module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

    def test_unsat_model(self):
        """ Test population of an unsatisfiable model. """
        fname = os.path.join(self.data_dir, "unsat_smarag_2.orm")
        model = NormaLoader(fname).model
        pop = Population(model)
        self.assertIsNone(pop.object_types)
        self.assertIsNone(pop.fact_types)        

