##############################################################################
# Package: ormpy
# File:    TestModel.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for :class:`lib.Model.Model` """

import sys
from unittest import TestCase

from lib.Model import Model
from lib.ObjectType import ObjectType
from lib.FactType import FactType, Role
from lib.Constraint import Constraint

class TestModel(TestCase):
    """ Unit tests for the Model class. """

    def setUp(self):
        pass

    def test_display_empty(self):
        """ Test Display of an empty model. """
        model = Model()
        model.display()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, "Object Types:\nFact Types:\nConstraints:")


    def test_display_nonempty(self):
        """ Test Display of non-empty model. """
        model = Model()
        model.object_types.add(ObjectType(name="O1"))
        model.fact_types.add(FactType(name="F1"))
        model.fact_types.add(FactType(name="F2"))
        model.constraints.add(Constraint(name="C1"))
        model.display()

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, "Object Types:\n    O1\nFact Types:\n    F1\n    F2\nConstraints:\n    C1")

    def test_add_remove_object_type(self):
        """ Test adding and removing an object type from the model. """
        model = Model()
        obj1 = ObjectType(name="O1")
        model.add(obj1)

        self.assertEquals(model.object_types.count(), 1)
        self.assertEquals(model.object_types.get("O1"), obj1)

        with self.assertRaises(NotImplementedError):
            model.remove(obj1)

        # I decided for now to just raise a NotImplementedError for rollback,
        # since I'm not sure what the right behavior should be.
        """
        model.remove(obj1)
        self.assertEquals(model.object_types.count(), 0)
        self.assertEquals(model.object_types.get("O1"), None)
        """

    def test_add_remove_fact_type(self):
        """ Test adding and removing a fact type from the model. """
        model = Model()
        fact = FactType(name="F1")
        fact.add_role(player=ObjectType(name="O1"))
        model.add(fact)

        self.assertEquals(model.fact_types.count(), 1)
        self.assertEquals(model.fact_types.get("F1"), fact)

        model.remove(fact)
        self.assertEquals(model.fact_types.count(), 0)
        self.assertEquals(model.fact_types.get("F1"), None)

    def test_add_remove_generic_constraint(self):
        """ Test adding and removing a generic constraint from the model. """
        model = Model()
        cons1 = Constraint(name="C1")

        model.add(cons1)
        self.assertEquals(model.constraints.count(), 1)
        self.assertEquals(model.constraints.get("C1"), cons1)

        model.remove(cons1)
        self.assertEquals(model.constraints.count(), 0)
        self.assertEquals(model.constraints.get("C1"), None)

    def test_add_remove_constraint_with_side_effects(self):
        """ Test adding and removing a generic constraint from the model. """
        model = Model()
        obj1 = ObjectType(name="O1")        
        cons1 = Constraint(name="C1", covers=[obj1])
        model.add(obj1)
        model.add(cons1)

        self.assertEquals(model.constraints.count(), 1)
        self.assertEquals(model.constraints.get("C1"), cons1)
        self.assertEquals(model.constraints.get("C1").covers[0], obj1)
        self.assertEquals(model.object_types.get("O1").covered_by[0], cons1)

        model.remove(cons1)
        self.assertEquals(model.constraints.count(), 0)
        self.assertEquals(model.constraints.get("C1"), None)
        self.assertEquals(model.object_types.get("O1").covered_by, [])

    def test_add_invalid_element(self):
        """ Test adding something unexpected to the model. """
        model = Model()
        with self.assertRaises(ValueError) as ex:
            model.add("Invalid")
        self.assertEquals(ex.exception.message, "Unexpected model element type")
        


