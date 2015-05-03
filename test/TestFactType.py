##############################################################################
# Package: ormpy
# File:    TestFactType.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the FactType module """

from unittest import TestCase

from lib.FactType import FactType, Role
from lib.ObjectType import ObjectType

class TestFactType(TestCase):
    """ Unit tests for the FactType module. """

    def setUp(self):
        pass

    def test_add_role(self):
        """ Confirm we can add a role to the fact type. """
        obj1 = ObjectType(name="Person")
        obj2 = ObjectType(name="School")

        fact_type = FactType(name="PersonAttendsSchoolWithPersonAndPerson")

        role1 = fact_type.add_role(obj1)
        role2 = fact_type.add_role(obj2)
        role3 = fact_type.add_role(obj1)
        role4 = fact_type.add_role(obj1)

        self.assertEquals(fact_type.arity(), 4)

        self.assertIs(role1.fact_type, fact_type)
        self.assertIs(role1.player, obj1)
        self.assertEquals(role1.name, "Person")

        self.assertIs(role2.fact_type, fact_type)
        self.assertIs(role2.player, obj2)
        self.assertEquals(role2.name, "School")

        self.assertIs(role3.fact_type, fact_type)
        self.assertIs(role3.player, obj1)
        self.assertEquals(role3.name, "Person2")

        self.assertIs(role4.fact_type, fact_type)
        self.assertIs(role4.player, obj1)
        self.assertEquals(role4.name, "Person3")

        self.assertItemsEqual(obj1.roles, [])
        self.assertItemsEqual(obj2.roles, [])

        fact_type.commit()

        self.assertItemsEqual(obj1.roles, [role1, role3, role4])
        self.assertItemsEqual(obj2.roles, [role2])

    def test_role_rollback(self):
        """ Confirm rollback of a role raises NotImplementedError. """
        with self.assertRaises(NotImplementedError):
            Role().rollback()

    def test_duplicate_role_name(self):
        """ Test that a new name is generated for a role if the role name is
            already present on the fact type. """
        fact_type = FactType(name="Test")
        fact_type.add_role(ObjectType(name="Person"), name="R1")
        fact_type.add_role(ObjectType(name="Dog"), name="R1")

        names = [role.name for role in fact_type.roles]

        self.assertEquals(names, ["R1", "Dog"])
        

