##############################################################################
# Package: ormpy
# File:    TestObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the ObjectType module """

from unittest import TestCase
import os

from lib.ObjectType import ObjectType
from lib.NormaLoader import NormaLoader
import lib.TestDataLocator as TestDataLocator

class TestObjectType(TestCase):
    """ Unit tests for the ObjectType module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir() + os.sep

    def test_domain(self):
        """ Test object type domain under various name scenarios. """
        actual = ObjectType().domain.draw(2)
        expect = ['0', '1']
        self.assertItemsEqual(actual, expect)

        actual = ObjectType(name='').domain.draw(2)
        expect = ['0', '1']
        self.assertItemsEqual(actual, expect)

        actual = ObjectType(name='Test').domain.draw(2)
        expect = ['Test0', 'Test1']
        self.assertItemsEqual(actual, expect)

        actual = ObjectType(name='Test1').domain.draw(2)
        expect = ['Test1_0', 'Test1_1']
        self.assertItemsEqual(actual, expect)

    def test_compatible_object_types(self):
        """ Test compatible() function. """
        model = NormaLoader(self.data_dir + "subtypes.orm").model
        
        w = model.object_types.get("W")
        x = model.object_types.get("X")
        y = model.object_types.get("Y")
        z = model.object_types.get("Z")
        x1 = model.object_types.get("X1")
        y1 = model.object_types.get("Y1")
        z1 = model.object_types.get("Z1")
        e1 = model.object_types.get("E1")

        self.assertTrue(z.compatible(z))
        self.assertTrue(z.compatible(x))
        self.assertTrue(x.compatible(z))
        self.assertTrue(z.compatible(w))
        self.assertTrue(w.compatible(z))
        self.assertTrue(z.compatible(z1))
        self.assertTrue(z1.compatible(z))

        self.assertFalse(z.compatible(x1))
        self.assertFalse(x1.compatible(z))

        self.assertFalse(z.compatible(e1))
        self.assertFalse(e1.compatible(z))

        self.assertFalse(y1.compatible(x))
        self.assertFalse(x.compatible(y1))
        


