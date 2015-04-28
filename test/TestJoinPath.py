##############################################################################
# Package: ormpy
# File:    TestJoinPath.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for :class:`lib.JoinPath.JoinPath` """

from unittest import TestCase

from lib.JoinPath import JoinPath, JoinPathException
from lib.FactType import FactType
from lib.ObjectType import ObjectType

class TestJoinPath(TestCase):
    """ Unit tests for the JoinPath class. """

    def setUp(self):
        self.obj1 = ObjectType(name="A")
        self.obj2 = ObjectType(name="B")
        self.obj3 = ObjectType(name="C")

        self.fact1 = FactType(name="AHasB")
        self.fact1.add_role(self.obj1)
        self.fact1.add_role(self.obj2)

        self.fact2 = FactType(name="BHasC")
        self.fact2.add_role(self.obj2)
        self.fact2.add_role(self.obj3)

        self.fact3 = FactType(name="ALikesA")
        self.fact3.add_role(self.obj1)
        self.fact3.add_role(self.obj1)

        self.fact4 = FactType(name="ALikesB")
        self.fact4.add_role(self.obj1)
        self.fact4.add_role(self.obj2)

    def test_incompatible_roles(self):
        """ Test an attempt to join fact types on incompatible roles."""
        join_path = JoinPath()
        
        with self.assertRaises(JoinPathException) as ex:
            join_path.add_join(self.fact1.roles[0], self.fact2.roles[0])

        msg = "join roles must be played by the same object type"
        self.assertEquals(ex.exception.message, msg) 

    def test_disconnected(self):
        """ Test that the first join role must be on a fact type already on
            the path. """
        join_path = JoinPath()
        join_path.add_join(self.fact1.roles[1], self.fact2.roles[0])

        with self.assertRaises(JoinPathException) as ex:
            join_path.add_join(self.fact3.roles[1], self.fact4.roles[0])

        msg = "first join role must already be on the join path"
        self.assertEquals(ex.exception.message, msg)  

    def test_cycle_1(self):
        """ Test that a self-join is rejected. """
        join_path = JoinPath()

        with self.assertRaises(JoinPathException) as ex:
            join_path.add_join(self.fact3.roles[0], self.fact3.roles[1])

        msg = "join would create a cycle in the join path"
        self.assertEquals(ex.exception.message, msg)

    def test_cycle_2(self):
        """ Test that a join to a fact type already in the path is rejected. """
        join_path = JoinPath()

        join_path.add_join(self.fact1.roles[1], self.fact2.roles[0])

        with self.assertRaises(JoinPathException) as ex:
            join_path.add_join(self.fact2.roles[0], self.fact1.roles[1])

        msg = "join would create a cycle in the join path"
        self.assertEquals(ex.exception.message, msg)

    def test_valid_join(self):
        """ Test that a valid join path is stored as expected. """
        join_path = JoinPath()

        join_path.add_join(self.fact1.roles[1], self.fact2.roles[0])
        join_path.add_join(self.fact1.roles[0], self.fact4.roles[0])
        join_path.add_join(self.fact4.roles[0], self.fact3.roles[1])

        self.assertEquals(join_path.fact_types, [self.fact1, self.fact2, self.fact4, self.fact3])
        self.assertEquals(join_path.joins, [(self.fact1.roles[1], self.fact2.roles[0]),
                                            (self.fact1.roles[0], self.fact4.roles[0]),
                                            (self.fact4.roles[0], self.fact3.roles[1])])
            

