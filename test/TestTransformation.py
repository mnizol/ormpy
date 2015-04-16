##############################################################################
# Package: ormpy
# File:    TestTransformation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Transformation module. """

from unittest import TestCase

import lib.TestDataLocator as TestData
import lib.Domain as Domain

from lib.SubtypeGraph import SubtypeGraph
from lib.NormaLoader import NormaLoader

from lib.Transformation import Transformation, ValueConstraintTransformation

##############################################################################
# Tests for generic Transformation class
##############################################################################
class TestTransformation(TestCase):
    """ Tests for generic Transformation class. """

    def setUp(self):
        pass

    def test_execute_not_implemented(self):
        """ Confirm execution of execute() raises NotImplementedError. """
        with self.assertRaises(NotImplementedError):
            Transformation().execute()
    
##############################################################################
# ValueConstraintTransformation tests for role value constraints
##############################################################################
class TestValueConstraintTransformation_RVC(TestCase):
    """ Unit tests for the ValueConstraintTransformation class that test
        the handling of role value constraints. """

    def setUp(self):
        fname = TestData.path("test_value_type_value_constraint.orm")
        self.model = NormaLoader(fname).model
        graph = SubtypeGraph(self.model)

        # Build dictionaries of model elements
        self.obj = {obj.name: obj for obj in self.model.object_types}
        self.cons = {cons.name: cons for cons in self.model.constraints}

        # Transform the model
        self.transform = ValueConstraintTransformation(model=self.model, 
                                                       subtype_graph=graph)
        self.transform.execute()

    def test_modification_lists_for_value_move(self):
        """ Check lists of modified, removed, and added elements. """
        removed = [self.cons["RVC_ET3"], 
                   self.cons["RVC_ET4"], 
                   self.cons["RVC_ET5"],
                   self.cons["RVC_VT2"]]

        modified = [self.cons["RVC_ET1"],
                    self.cons["RVC_VT1"],
                    self.cons["RVC_ET6"]]

        self.assertItemsEqual(self.transform.removed, removed)
        self.assertItemsEqual(self.transform.modified, modified)
        self.assertItemsEqual(self.transform.added, [])

        # Confirm all removed constraints are actually removed
        self.assertItemsEqual(set(self.model.constraints) & set(removed), [])

        # Confirm all modified constraints are still in model
        self.assertItemsEqual(set(self.model.constraints), 
                              set(self.model.constraints) | set(modified))


    def test_value_cons_already_on_type(self):
        """ Test case where value constraint is already on the value type. """

        # Value type A        
        vt_a = self.obj["A"]
        vc_a = self.cons["VC_A"]
        self.assertItemsEqual(vt_a.domain.draw(15), [1,2,6] + range(10,20) + [101,102])
        self.assertItemsEqual(vc_a.covers, [vt_a]) 
        self.assertItemsEqual(vt_a.covered_by, [vc_a])        

        # Value type ET2_id 
        et2 = self.obj["ET2"]
        et2_id = self.obj["ET2_id"]
        vc_et2 = self.cons["VC_ET2"]      
        self.assertItemsEqual(et2.domain.draw(3), ["ET2_0", "ET2_1", "ET2_2"])
        self.assertItemsEqual(et2_id.domain.draw(20), [1,2,3,4,5,6,7,8])
        self.assertItemsEqual(vc_et2.covers, [et2_id])
        self.assertItemsEqual(et2_id.covered_by, [vc_et2])
       

    def test_basic_entity_type_move(self):
        """ Test basic move of value constraint on entity type from identifying
            role to identifying value type. """

        et1 = self.obj["ET1"]
        et1_id = self.obj["ET1_id"]
        rvc_et1 = self.cons["RVC_ET1"] 
        self.assertItemsEqual(et1.domain.draw(3), ["ET1_0", "ET1_1", "ET1_2"])
        self.assertItemsEqual(et1_id.domain.draw(20), [1,2,3,4,5,6,7,8,9,10])
        self.assertItemsEqual(rvc_et1.covers, [et1_id])
        self.assertItemsEqual(et1_id.covered_by, [rvc_et1]) 


    def test_failed_move_due_to_shared_ref_mode(self):
        """ Test case where we cannot move the value constraint to the 
            identifying value type because that type plays more than one role."""

        et3 = self.obj["ET3"]
        et4 = self.obj["ET4"]
        usd = self.obj["USDValue"]

        self.assertItemsEqual(et3.domain.draw(3), ["ET3_0", "ET3_1", "ET3_2"])
        self.assertItemsEqual(et4.domain.draw(3), ["ET4_0", "ET4_1", "ET4_2"])
        self.assertItemsEqual(usd.domain.draw(3), [0.0, 0.1, 0.2])

        rvc_et3 = self.cons["RVC_ET3"]
        rvc_et4 = self.cons["RVC_ET4"]

        self.assertIn(rvc_et3, self.transform.removed)
        self.assertIn(rvc_et4, self.transform.removed)
        
        role3 = self.model.fact_types.get("ET3HasUSDValue").roles[1]
        role4 = self.model.fact_types.get("ET4HasUSDValue").roles[1]

        self.assertItemsEqual(usd.covered_by, [])
        self.assertNotIn(rvc_et3, role3.covered_by)
        self.assertNotIn(rvc_et4, role4.covered_by)


    def test_failed_move_due_to_entity_with_mult_roles(self):
        """ Test case where we cannot move RVC because the entity type plays
            more than one role. """

        et5 = self.obj["ET5"]
        et5_id = self.obj["ET5_Id"]
        rvc_et5 = self.cons["RVC_ET5"]

        self.assertItemsEqual(et5.domain.draw(3), ["ET5_0", "ET5_1", "ET5_2"])
        self.assertItemsEqual(et5_id.domain.draw(3), [0, 1, 2])

        self.assertIn(rvc_et5, self.transform.removed)

        self.assertItemsEqual(et5.covered_by, [])
        self.assertItemsEqual(et5_id.covered_by, [])

        role = self.model.fact_types.get("ET5Exists").roles[0]
        self.assertNotIn(rvc_et5, role.covered_by)

    def test_move_of_rvc_to_non_ref_value_type(self):
        """ Test move of rvc to non-referential value type. """

        # VT1 plays only a unary role and is not independent, so the role 
        # value constraint can cover the object type instead.
        vt1 = self.obj["VT1"]
        rvc_vt1 = self.cons["RVC_VT1"]
        self.assertItemsEqual(vt1.domain.draw(50), range(45,71))
        self.assertItemsEqual(rvc_vt1.covers, [vt1])
        self.assertItemsEqual(vt1.covered_by, [rvc_vt1])  
        self.assertIn(rvc_vt1, self.transform.modified)

    def test_failed_move_due_to_independence(self):
        """ Test failure to move rvc due to value type independence. """

        vt2 = self.obj["VT2"]
        rvc_vt2 = self.cons["RVC_VT2"]
        self.assertItemsEqual(vt2.domain.draw(10), range(0,10))
        self.assertItemsEqual(vt2.covered_by, [])

        self.assertIn(rvc_vt2, self.transform.removed)

        role = self.model.fact_types.get("VT2Exists").roles[0]
        self.assertNotIn(rvc_vt2, role.covered_by)

    def test_intersection_of_value_constraints(self):
        """ Test case where RVC can be moved but value type already is covered
            by another value constraint. """

        et6 = self.obj["ET6"]
        et6_id = self.obj["ET6_id"]
        rvc_et6 = self.cons["RVC_ET6"]
        vc_et6 = self.cons["VC_ET6"]

        self.assertItemsEqual(et6.domain.draw(3), ["ET6_0","ET6_1","ET6_2"])
        self.assertItemsEqual(et6_id.domain.draw(10), [10,11,12,13,14,15])

        self.assertItemsEqual(et6_id.covered_by, [rvc_et6, vc_et6])
        self.assertIn(rvc_et6, self.transform.modified)

##############################################################################
# ValueConstraintTransformation class tests for subtypes
##############################################################################
class TestValueConstraintTransformation_Subtypes(TestCase):
    """ Unit tests for the ValueConstraintTransformation class that test
        the handling of subtype value constraints. """

    def setUp(self):
        self.maxDiff = None

        fname = TestData.path("value_constraints_on_subtypes.orm")
        self.model = NormaLoader(fname).model
        graph = SubtypeGraph(self.model)

        # Build dictionaries of model elements
        self.obj = {obj.name: obj for obj in self.model.object_types}
        self.cons = {cons.name: cons for cons in self.model.constraints}

        # Transform the model
        self.transform = ValueConstraintTransformation(model=self.model, 
                                                       subtype_graph=graph)
        self.transform.execute()

    def test_contents_of_modification_lists(self):
        """ Test contents of modified, removed, added lists. """
        removed = [self.cons["VC_R"],
                   self.cons["VC_S"],
                   self.cons["VC_F"]]
        modified = [self.cons["VC_I"],
                    self.cons["VC_K"],
                    self.cons["VC_P"],
                    self.cons["VC_Q"],
                    self.cons["VC_W"],
                    self.cons["VC_Z"]]

        self.assertItemsEqual(self.transform.added, [])
        self.assertItemsEqual(self.transform.removed, removed)
        self.assertItemsEqual(self.transform.modified, modified)

        # Confirm all removed constraints are actually removed
        self.assertItemsEqual(set(self.model.constraints) & set(removed), [])

        # Confirm all modified constraints are still in model
        self.assertItemsEqual(set(self.model.constraints), 
                              set(self.model.constraints) | set(modified))

    def test_subtype_with_only_root_constraint(self):
        """ Test case where the only element with a value constraint
            is the root. """
        a = self.obj["A"]
        vc_a = self.cons["VC_A"]
        self.assertItemsEqual(a.domain.draw(20), range(50, 61))
        self.assertEquals(a.domain, vc_a.domain)
        self.assertIn(vc_a, a.covered_by)

    def test_subtype_with_one_subtype_value_constraint(self):
        """ Test case where only one subtype has a value constraint. """
        i = self.obj["I"]
        k = self.obj["K"]
        vc_i = self.cons["VC_I"]
        vc_k = self.cons["VC_K"]

        self.assertItemsEqual(i.domain.draw(30), range(30,51))
        self.assertItemsEqual(k.domain.draw(30), range(30,41))
        self.assertEquals(i.domain, vc_i.domain)
        self.assertEquals(k.domain, vc_k.domain)
        self.assertIn(vc_i, i.covered_by)
        self.assertIn(vc_k, k.covered_by)

    def test_deletion_of_extra_value_constraints(self):
        """ Confirm that only one value constraint is kept per subtype graph
            (not counting the root)."""
        p = self.obj["P"]
        q = self.obj["Q"]
        r = self.obj["R"]
        s = self.obj["S"]
        vc_p = self.cons["VC_P"]
        vc_q = self.cons["VC_Q"]
        vc_r = self.cons["VC_R"]
        vc_s = self.cons["VC_S"]

        self.assertEquals(p.domain, vc_p.domain)
        self.assertIn(vc_p, p.covered_by)

        self.assertEquals(q.domain, vc_q.domain)
        self.assertIn(vc_q, q.covered_by)

        self.assertNotEquals(r.domain, vc_r.domain)
        self.assertEquals(r.covered_by, [self.cons["RIsASubtypeOfQ"]])

        self.assertNotEquals(s.domain, vc_s.domain)
        self.assertEquals(s.covered_by, [self.cons["SIsASubtypeOfQ"]])

        self.assertTrue(isinstance(r.domain, Domain.IntegerDomain))
        self.assertTrue(isinstance(s.domain, Domain.IntegerDomain))

    def test_deletion_of_value_cons_when_root_has_no_vc(self):
        """ Test when root has no value constraint but subtype does. """
        e = self.obj["E"]
        f = self.obj["F"]
        vc_f = self.cons["VC_F"]
        sub_cons = self.cons["FIsASubtypeOfE"]

        self.assertTrue(isinstance(e.domain, Domain.IntegerDomain))
        self.assertEquals(e.covered_by, [sub_cons])

        self.assertNotEquals(f.domain, vc_f.domain)
        self.assertTrue(isinstance(f.domain, Domain.IntegerDomain))
        self.assertEquals(f.covered_by, [sub_cons])

    def test_intersection_and_reordering_of_value_constraints(self):
        """ Confirm that subtype value constraint is forced to be a subset of
            the root, and that the root's value constraint is reordered so that
            the subtype's elements come first. """

        w = self.obj["W"]
        z = self.obj["Z"]

        vc_w = self.cons["VC_W"]
        vc_z = self.cons["VC_Z"]

        self.assertEquals(w.domain, vc_w.domain)
        self.assertEquals(z.domain, vc_z.domain)

        # Use assert equals to check order
        self.assertEquals(w.domain.draw(30), [20,21,22] + range(1, 20))
        self.assertEquals(z.domain.draw(30), [20,21,22])



