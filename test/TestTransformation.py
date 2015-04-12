##############################################################################
# Package: ormpy
# File:    TestTransformation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Transformation module. """

from unittest import TestCase

import lib.TestDataLocator as TestData
from lib.SubtypeGraph import SubtypeGraph
from lib.NormaLoader import NormaLoader

from lib.Transformation import ValueConstraintTransformation

class TestValueConstraintTransformation(TestCase):
    """ Unit tests for the ValueConstraintTransformation class. """

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
