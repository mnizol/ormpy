##############################################################################
# Package: ormpy
# File:    TestConstraint.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.TestConstraint class """

from unittest import TestCase

import lib.Constraint as Constraint
import lib.Domain as Domain
from lib.Model import Model
from lib.ObjectType import ObjectType, EntityType
from lib.FactType import FactType, Role

class TestConstraint(TestCase):
    """ Unit tests for the Constraint module. """

    def setUp(self):
        pass

    def test_add_object_type(self):
        """ Test the addition of an object type to a constraint. """
        covers = [ObjectType(uid="2", name="O1")]
        cons = Constraint.Constraint(uid="1", name="C1", covers=covers)        
        self.assertEquals(cons.covers[0].name, "O1")

    """ Removed uncover() method so this test is no longer valid.
    def test_remove_object_type(self):
        # Test the removal of an object type from a constraint.
        obj = ObjectType(uid="2", name="O1")
        cons = Constraint.Constraint(uid="1", name="C1", covers=[obj])
        
        self.assertEquals(cons.covers[0], obj)

        # Unsuccessful uncover
        cons.uncover("Dummy")
        self.assertEquals(cons.covers[0], obj)

        # Successful uncover
        cons.uncover(obj)
        self.assertItemsEqual(cons.covers, [])
    """

    def test_vc_add_enum(self):
        """ Test the addition of enumerated items to a value constraint."""
        domain = Constraint.ValueDomain()
        domain.add_range("Dog", "Dog")
        domain.add_range("Cat")
        domain.add_range(1.35)
        domain.add_range(9)
        cons = Constraint.ValueConstraint(domain, name="VC1")
        self.assertItemsEqual(cons.domain.draw(4), ["Dog","Cat", 1.35,9])
        self.assertEquals(cons.size, 4)

    def test_vc_bad_enum(self):
        """ Test invalid enumerations in value constraint. """
        domain = Constraint.ValueDomain()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            domain.add_range("Dog", max_open=True)
        self.assertEquals(ex.exception.message, 
            "Value constraints only support integer ranges")

        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            domain.add_range("Dog", min_open=True)
        self.assertEquals(ex.exception.message, 
            "Value constraints only support integer ranges")

    def test_vc_bad_ranges(self):
        """ Test a value constraint with a range of non-integers. """
        domain = Constraint.ValueDomain()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            domain.add_range("1.45", "5.6")
        self.assertEquals(ex.exception.message,
            "Value constraints only support integer ranges")

    def test_vc_int_ranges(self):
        """ Test the addition of value ranges to a value constraint 
            with default inclusion values. """
        cons = Constraint.ValueConstraint(name="VC1")
        cons.domain.add_range("1", "4")
        self.assertItemsEqual(cons.domain.draw(10), [1,2,3,4])
        self.assertEquals(cons.size, 4)
        cons.domain.add_range("3", "5")
        self.assertItemsEqual(cons.domain.draw(10), [1,2,3,4,5])

    def test_vc_int_ranges_open(self):
        """ Test the addition of value ranges to a value constraint 
            with explicit inclusion values. """
        cons = Constraint.ValueConstraint(uid="1", name="VC1")
        cons.domain.add_range("1", "2", min_open=True)
        cons.domain.add_range("5", "10", max_open=True)
        cons.domain.add_range("11", "13", min_open=True, max_open=True)
        self.assertItemsEqual(cons.domain.draw(10), [2,5,6,7,8,9,12])
        self.assertEquals(cons.size, 7)

    def test_vc_invalid_range(self):
        """ Test a value constraint with an invalid integer range. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.domain.add_range("12", "13", min_open=True, max_open=True)
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is invalid")

        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.domain.add_range("3", "2")
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is invalid")

    def test_vc_too_large(self):
        """ Test a value constraint range that is too large. """
        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.domain.add_range(0, Constraint.ValueDomain.MAX_SIZE)
        self.assertEquals(ex.exception.message,
            "The range of the value constraint is too large")

        cons = Constraint.ValueConstraint()
        with self.assertRaises(Constraint.ValueConstraintError) as ex:
            cons.domain.add_range(75, float('inf'))
        self.assertEquals(ex.exception.message,
            "Value constraints only support integer ranges")       

    def test_add_subset_roles(self):
        """ Test adding subset and superset roles to subset constraint. """
        role1 = Role(name="R1")
        role2 = Role(name="R2")
        cons = Constraint.SubsetConstraint(name="S1", subset=[role1], superset=[role2])
        
        self.assertItemsEqual(cons.covers, [role1, role2])
        self.assertEquals(cons.subset, [role1])
        self.assertEquals(cons.superset, [role2])

    def test_of_type_with_hit(self):
        """ Test of_type method with non-empty result. """
        cons_set = Constraint.ConstraintSet()
        cons1 = Constraint.SubsetConstraint(uid="1", name="S1")
        cons2 = Constraint.ValueConstraint(uid="2", name="V1")
        cons3 = Constraint.SubsetConstraint(uid="3", name="S2")

        cons_set.add(cons1)
        cons_set.add(cons2)
        cons_set.add(cons3)
        
        actual = cons_set.of_type(Constraint.SubsetConstraint)
        expect = [cons1, cons3]
        self.assertItemsEqual(actual, expect)
        
    def test_of_type_without_hit(self):
        """ Test of_type method with empty result. """
        cons_set = Constraint.ConstraintSet()
        cons1 = Constraint.SubsetConstraint(uid="1", name="S1")
        cons2 = Constraint.ValueConstraint(uid="2", name="V1")
        cons3 = Constraint.SubsetConstraint(uid="3", name="S2")

        cons_set.add(cons1)
        cons_set.add(cons2)
        cons_set.add(cons3)
        
        actual = cons_set.of_type(Constraint.MandatoryConstraint)
        expect = []
        self.assertItemsEqual(actual, expect)

    def test_mandatory_is_simple(self):
        """ Test simple property on MandatoryConstraint. """
        role1 = Role(uid="R1", name="R1")
        role2 = Role(uid="R2", name="R2")

        cons1 = Constraint.MandatoryConstraint(uid="C1",name="C1",covers=[role1])
        cons2 = Constraint.MandatoryConstraint(uid="C2",name="C2",covers=[role1,role2])

        self.assertTrue(cons1.simple)
        self.assertFalse(cons2.simple)

    def test_commit_and_rollback(self):
        """ Test committing and rolling back constraints on a model. """
        model = Model()

        obj1 = ObjectType(name="O1")
        obj2 = ObjectType(name="O2")

        role1 = Role(name="R1")
        role2 = Role(name="R2")
        fact = FactType(name="F1")
        fact.add(role1)
        fact.add(role2)

        cons1 = Constraint.MandatoryConstraint(name="M1",covers=[role1])
        cons2 = Constraint.UniquenessConstraint(name="U1",covers=[role1,role2])
        cons3 = Constraint.ValueConstraint(name="V1",covers=[obj1])
        
        for element in [obj1, obj2, fact, cons1, cons2, cons3]:
            model.add(element)

        self.assertEquals(model.constraints.get("M1").covers, [role1])
        self.assertEquals(model.constraints.get("U1").covers, [role1, role2])
        self.assertEquals(model.constraints.get("V1").covers, [obj1])
 
        self.assertEquals(role1.covered_by, [cons1, cons2])
        self.assertEquals(role2.covered_by, [cons2])
        self.assertEquals(obj1.covered_by, [cons3])

        model.remove(cons2)
        model.remove(cons3)

        self.assertEquals(model.constraints.get("M1"), cons1)
        self.assertEquals(model.constraints.get("U1"), None)
        self.assertEquals(model.constraints.get("V1"), None)

        self.assertEquals(role1.covered_by, [cons1])
        self.assertEquals(role2.covered_by, [])
        self.assertEquals(obj1.covered_by, [])

        # Test that additional rollback has no effect
        model.remove(cons3)
        self.assertEquals(model.constraints.get("M1"), cons1)
        self.assertEquals(model.constraints.get("V1"), None)
        self.assertEquals(obj1.covered_by, [])

    def test_commit_rollback_mandatory(self):
        """ Test commit and rollback of mandatory constraint. """
        role = Role(name="R1")
        cons = Constraint.MandatoryConstraint(name="M1",covers=[role])

        self.assertEquals(role.covered_by, [])
        self.assertFalse(role.mandatory)

        cons.commit()

        self.assertEquals(role.covered_by, [cons])
        self.assertTrue(role.mandatory)

        cons.rollback()

        self.assertEquals(role.covered_by, [])
        self.assertFalse(role.mandatory)

    def test_commit_rollback_ior(self):
        """ Test commit and rollback of inclusive-or constraint. """
        role1 = Role(name="R1")
        role2 = Role(name="R2")
        cons = Constraint.MandatoryConstraint(name="M1",covers=[role1,role2])

        self.assertFalse(cons.simple)

        self.assertEquals(role1.covered_by, [])
        self.assertEquals(role2.covered_by, [])
        self.assertFalse(role1.mandatory)
        self.assertFalse(role2.mandatory)

        cons.commit()

        self.assertEquals(role1.covered_by, [cons])
        self.assertEquals(role2.covered_by, [cons])
        self.assertFalse(role1.mandatory) # False because cons is not simple
        self.assertFalse(role2.mandatory) # False because cons is not simple

        cons.rollback()

        self.assertEquals(role1.covered_by, [])
        self.assertEquals(role2.covered_by, [])
        self.assertFalse(role1.mandatory)
        self.assertFalse(role2.mandatory)

    def test_commit_rollback_iuc(self):
        """ Test commit and rollback of internal uniqueness constraints."""
        role1 = Role(name="R1")
        role2 = Role(name="R2")
        obj1 = EntityType(name="O1")
        cons1 = Constraint.UniquenessConstraint(name="U1",covers=[role1],identifier_for=obj1)
        cons2 = Constraint.UniquenessConstraint(name="U2",covers=[role2],identifier_for=None)

        self.assertEquals(role1.covered_by, [])
        self.assertEquals(role2.covered_by, [])
        self.assertEquals(obj1.identifying_constraint, None)

        cons1.commit()
        cons2.commit()

        self.assertEquals(role1.covered_by, [cons1])
        self.assertEquals(role2.covered_by, [cons2])
        self.assertEquals(obj1.identifying_constraint, cons1)

        cons1.rollback()
        cons2.rollback()

        self.assertEquals(role1.covered_by, [])
        self.assertEquals(role2.covered_by, [])
        self.assertEquals(obj1.identifying_constraint, None)

    def test_commit_and_rollback_value(self):
        """ Test commit and rollback of value constraints. """
        d0 = Domain.IntegerDomain()
        role = Role(name="R1")
        obj = ObjectType(name="O1", data_type=d0)

        d1 = Constraint.ValueDomain()
        d1.add_range("Dog")

        rvc = Constraint.ValueConstraint(name="RVC", covers=[role], domain=d1)

        self.assertEquals(role.covered_by, [])
        rvc.commit()
        self.assertEquals(role.covered_by, [rvc])
        rvc.rollback()
        self.assertEquals(role.covered_by, [])

        vc = Constraint.ValueConstraint(name="VTVC", covers=[obj], domain=d1)
        
        self.assertEquals(obj.covered_by, [])
        self.assertEquals(obj.domain, obj.data_type)
        self.assertEquals(obj.domain, d0)

        vc.commit()

        self.assertEquals(obj.covered_by, [vc])
        self.assertEquals(obj.domain, d1)
        self.assertEquals(obj.data_type, d0)
        
        vc.rollback()

        self.assertEquals(obj.covered_by, [])
        self.assertEquals(obj.domain, obj.data_type)
        self.assertEquals(obj.domain, d0)

    def test_commit_and_rollback_subtype(self):
        """ Test commit and rollback of a subtype constraint. """
        obj1 = ObjectType(name="O1")
        obj2 = ObjectType(name="O2")
        cons = Constraint.SubtypeConstraint(subtype=obj1, supertype=obj2)

        self.assertEquals(obj1.covered_by, [])
        self.assertEquals(obj1.direct_subtypes, [])
        self.assertEquals(obj1.direct_supertypes, [])
        self.assertEquals(obj2.covered_by, [])
        self.assertEquals(obj2.direct_subtypes, [])
        self.assertEquals(obj2.direct_supertypes, [])

        cons.commit()

        self.assertEquals(obj1.covered_by, [cons])
        self.assertEquals(obj1.direct_subtypes, [])
        self.assertEquals(obj1.direct_supertypes, [obj2])
        self.assertEquals(obj2.covered_by, [cons])
        self.assertEquals(obj2.direct_subtypes, [obj1])
        self.assertEquals(obj2.direct_supertypes, [])

        cons.rollback()

        self.assertEquals(obj1.covered_by, [])
        self.assertEquals(obj1.direct_subtypes, [])
        self.assertEquals(obj1.direct_supertypes, [])
        self.assertEquals(obj2.covered_by, [])
        self.assertEquals(obj2.direct_subtypes, [])
        self.assertEquals(obj2.direct_supertypes, [])

