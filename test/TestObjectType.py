##############################################################################
# Package: ormpy
# File:    TestObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the ObjectType module """

from unittest import TestCase

from lib.ObjectType import ObjectType

class TestObjectType(TestCase):
    """ Unit tests for the ObjectType module. """

    def setUp(self):
        pass

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

