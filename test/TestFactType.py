##############################################################################
# Package: ormpy
# File:    TestFactType.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the FactType module """

from unittest import TestCase

import lib.FactType as FactType
from lib.ObjectType import ObjectType

class TestFactType(TestCase):
    """ Unit tests for the FactType module. """

    def setUp(self):
        pass

    def test_add_role(self):
        """ Confirm we can add a role to the fact type. """
        fact_type = FactType.FactType(uid="F1", name="AHasB")
        role1 = FactType.Role(uid="R1")
        role2 = FactType.Role(uid="R2")
        fact_type.add(role1)
        fact_type.add(role2)
        self.assertEquals(fact_type.arity(), 2)
        self.assertIs(fact_type.roles[0], role1)
        self.assertIs(fact_type.roles[1], role2)

        

