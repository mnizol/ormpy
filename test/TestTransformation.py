##############################################################################
# Package: ormpy
# File:    TestTransformation.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Transformation module. """

from unittest import TestCase

import lib.TestDataLocator as TestData
import lib.Domain as Domain
import lib.Model as Model

from lib.FactType import FactType, RoleSequence
from lib.ObjectType import ObjectType
from lib.SubtypeGraph import SubtypeGraph
from lib.NormaLoader import NormaLoader
from lib.Constraint import UniquenessConstraint, MandatoryConstraint, \
                           FrequencyConstraint, SubsetConstraint

from lib.Transformation import Transformation, ValueConstraintTransformation, \
                               AbsorptionTransformation, \
                               DisjunctiveRefTransformation, \
                               OverlappingIFCTransformation, \
                               EUCStrengtheningTransformation, \
                               UnsupportedSubsetRemoval, \
                               TupleSubsetTransformation, \
                               RootRoleTransformation, \
                               direct_subsets

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

##############################################################################
# AbsorptionTransformation tests
##############################################################################
class TestAbsorptionTransformation(TestCase):
    """ Unit tests for the AbsorptionTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_pattern_not_matched(self):
        """ Test that EUCs which don't match the pattern are ignored."""
        fname = TestData.path("absorption_no_matching_euc.orm")
        loader = NormaLoader(fname)
        model = loader.model

        self.assertEquals(loader.omissions, [])

        # EUCs before transformation
        eucs = filter(lambda x: not x.internal, model.constraints.of_type(UniquenessConstraint))
        self.assertEquals(len(eucs), 8)

        trans = AbsorptionTransformation(model)
        trans.execute()

        # Same number of EUCs after transformation
        eucs = filter(lambda x: not x.internal, model.constraints.of_type(UniquenessConstraint))
        self.assertEquals(len(eucs), 8)

        self.assertItemsEqual(trans.added, [])
        self.assertItemsEqual(trans.removed, [])
        self.assertItemsEqual(trans.modified, [])

    def test_simple_absorption(self):
        """ Test simple absorption transformation. """
        fname = TestData.path("absorption_valid_simple.orm")
        loader = NormaLoader(fname)
        model = loader.model

        self.assertEquals(loader.omissions, [])

        # Before transformation
        a = model.object_types.get("A")
        b = model.object_types.get("B")
        c = model.object_types.get("C")
        euc = model.constraints.get("EUC1")
        AHasB = model.fact_types.get("AHasB")
        AHasC = model.fact_types.get("AHasC")
        old_cons = [cons for cons in model.constraints]

        self.assertIsNotNone(euc)
        self.assertIsNotNone(AHasB)
        self.assertIsNotNone(AHasC)

        # Transformation
        trans = AbsorptionTransformation(model)
        trans.execute()

        # After transformation
        self.assertIsNone(model.constraints.get("EUC1"))
        self.assertIsNone(model.fact_types.get("AHasB"))
        self.assertIsNone(model.fact_types.get("AHasC"))

        # Constraint count of 3: 1 mandatory, 2 IUC
        self.assertEquals(model.constraints.count(), 3)
        self.assertEquals(model.fact_types.count(), 1)
        
        absorb_fact = model.fact_types.get("EUC1")
        self.assertIsNotNone(absorb_fact)

        self.assertEquals(absorb_fact.arity(), 3)

        self.assertIs(absorb_fact.root_role.player, a)

        role0 = absorb_fact.roles[0]
        self.assertIs(role0.player, a)
        self.assertEquals(len(role0.covered_by), 2)

        self.assertTrue(isinstance(role0.covered_by[0], UniquenessConstraint))
        self.assertEquals(len(role0.covered_by[0].covers), 1)

        self.assertTrue(isinstance(role0.covered_by[1], MandatoryConstraint))
        self.assertTrue(role0.covered_by[1].simple)

        role1 = absorb_fact.roles[1]
        role2 = absorb_fact.roles[2]

        self.assertIs(role1.player, b)
        self.assertIs(role2.player, c)

        self.assertEquals(len(role1.covered_by), 1)
        self.assertEquals(len(role2.covered_by), 1)
        self.assertEquals(role1.covered_by, role2.covered_by)
        self.assertTrue(isinstance(role1.covered_by[0], UniquenessConstraint))
        self.assertIs(role1.covered_by[0], role2.covered_by[0])

        # Check ref roles
        idcons = role1.covered_by[0]
        self.assertIs(a.identifying_constraint, idcons)
        self.assertIs(idcons.identifier_for, a)
        self.assertEquals(a.ref_roles, [role0])

        # Check absorb_fact.fact_type_names
        expected = {'B': "FactTypes.AHasB", 'C': "FactTypes.AHasC"}
        self.assertDictEqual(absorb_fact.fact_type_names, expected)

        # Check contents of added, removed, modified
        self.assertItemsEqual(trans.added, [absorb_fact] + list(model.constraints))
        self.assertItemsEqual(trans.removed, [AHasB, AHasC] + old_cons)
        self.assertItemsEqual(trans.modified, [])
        
    def test_four_part_absorption(self):
        """ Test absorption transformation involving four fact types. """
        fname = TestData.path("absorption_valid_four_facts.orm")
        loader = NormaLoader(fname)
        model = loader.model

        self.assertEquals(loader.omissions, [])

        # Before transformation
        a = model.object_types.get("A")
        b = model.object_types.get("B")
        c = model.object_types.get("C")
        d = model.object_types.get("D")
        e = model.object_types.get("E")
        old_fact = [fact for fact in model.fact_types]
        old_cons = [cons for cons in model.constraints]

        # Transformation
        trans = AbsorptionTransformation(model)
        trans.execute()

        # After transformation
        self.assertEquals(model.constraints.count(), 4)
        self.assertEquals(model.fact_types.count(), 1)
        
        absorb_fact = model.fact_types.get("EUC1")
        self.assertIsNotNone(absorb_fact)

        self.assertEquals(absorb_fact.arity(), 5)

        self.assertIs(absorb_fact.root_role.player, a)

        role0 = absorb_fact.roles[0]
        self.assertIs(role0.player, a)
        self.assertEquals(len(role0.covered_by), 2)

        self.assertTrue(isinstance(role0.covered_by[0], UniquenessConstraint))
        self.assertEquals(len(role0.covered_by[0].covers), 1)

        self.assertTrue(isinstance(role0.covered_by[1], MandatoryConstraint))
        self.assertTrue(role0.covered_by[1].simple)

        role1 = absorb_fact.roles[1]
        role2 = absorb_fact.roles[2]
        role3 = absorb_fact.roles[3]
        role4 = absorb_fact.roles[4]

        self.assertIs(role1.player, b)
        self.assertIs(role2.player, c)
        self.assertIs(role3.player, d)
        self.assertIs(role4.player, e)

        self.assertEquals(len(role1.covered_by), 2)
        self.assertTrue(isinstance(role1.covered_by[0], MandatoryConstraint))
        self.assertTrue(role1.covered_by[0].simple)

        uniq = role1.covered_by[1]
        self.assertEquals(len(uniq.covers), 4)

        self.assertTrue(isinstance(uniq, UniquenessConstraint))

        self.assertEquals(role2.covered_by, [uniq])
        self.assertEquals(role3.covered_by, [uniq])
        self.assertEquals(role4.covered_by, [uniq])  

        # Confirm that new uniqueness constraint is the identifier for "A"
        self.assertIs(a.identifying_constraint, uniq)
        self.assertIs(uniq.identifier_for, a)
        self.assertItemsEqual(a.ref_roles, [role0])      
        
        # Check absorb_fact.fact_type_names
        expected = {'B':"FactTypes.AHasB", 'C':"FactTypes.AHasC", 'D':"FactTypes.AHasD", 'E':"FactTypes.AHasE"}
        self.assertDictEqual(absorb_fact.fact_type_names, expected)

        # Check contents of added, removed, modified
        self.assertItemsEqual(trans.added, [absorb_fact] + list(model.constraints))
        self.assertItemsEqual(trans.removed, old_fact + old_cons)
        self.assertItemsEqual(trans.modified, [])

##############################################################################
# DisjunctiveRefTransformation tests
##############################################################################
class TestDisjunctiveRefTransformation(TestCase):
    """ Unit tests for the DisjunctiveRefTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_disjunctive_ref_no_ior(self):
        """ Test a disjunctive reference scheme with no IOR constraint. """
        fname = TestData.path("disjunctive_reference_scheme.orm")
        loader = NormaLoader(fname)
        model = loader.model

        mand = model.constraints.of_type(MandatoryConstraint)
        self.assertEquals(len(mand), 1)

        a = model.object_types.get("A")
        role1 = model.fact_types.get("AHasB").roles[0]
        role2 = model.fact_types.get("AHasC").roles[0]

        self.assertItemsEqual(a.ref_roles, [role1, role2])
        self.assertTrue(role1.mandatory)
        self.assertFalse(role2.mandatory)
    
        # Execute the transformation
        trans = DisjunctiveRefTransformation(model=model)
        self.assertTrue(trans.execute())

        mand = model.constraints.of_type(MandatoryConstraint)
        self.assertEquals(len(mand), 2)

        # Both ref roles now mandatory
        self.assertTrue(role1.mandatory)
        self.assertTrue(role2.mandatory)

    def test_disjunctive_ref_with_ior(self):
        """ Test a disjunctive reference scheme WITH an IOR constraint. """
        fname = TestData.path("disjunctive_reference_scheme_2.orm")
        loader = NormaLoader(fname)
        model = loader.model

        mand = model.constraints.of_type(MandatoryConstraint)
        self.assertEquals(len(mand), 1)
        self.assertFalse(mand[0].simple) # IOR constraint

        a = model.object_types.get("A")
        role1 = model.fact_types.get("AHasB").roles[0]
        role2 = model.fact_types.get("AHasC").roles[0]

        self.assertItemsEqual(a.ref_roles, [role1, role2])
        self.assertFalse(role1.mandatory)
        self.assertFalse(role2.mandatory)
    
        # Execute the transformation
        trans = DisjunctiveRefTransformation(model=model)
        self.assertTrue(trans.execute())

        mand = model.constraints.of_type(MandatoryConstraint)
        self.assertEquals(len(mand), 2)
        self.assertTrue(mand[0].simple)
        self.assertTrue(mand[1].simple)

        # Both ref roles now mandatory
        self.assertTrue(role1.mandatory)
        self.assertTrue(role2.mandatory)

##############################################################################
# OverlappingIFCTransformation tests
##############################################################################
class TestOverlappingIFCTransformation(TestCase):
    """ Unit tests for the OverlappingIFCTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_non_overlapping(self):
        """ Test case where IUCs don't overlap. """
        fname = TestData.path("uniqueness_constraints.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        get = model.constraints.get
        self.assertEquals(len(get("InternalUniquenessConstraint5").covers), 2)
        self.assertEquals(len(get("InternalUniquenessConstraint1").covers), 2)
        self.assertEquals(len(get("InternalUniquenessConstraint4").covers), 1)
        self.assertEquals(len(get("InternalUniquenessConstraint9").covers), 1)
        self.assertEquals(len(get("InternalUniquenessConstraint10").covers), 1)

        # Run transformation and confirm return value is false
        self.assertFalse(OverlappingIFCTransformation(model).execute())

        # Assert that nothing changed.
        self.assertEquals(len(get("InternalUniquenessConstraint5").covers), 2)
        self.assertEquals(len(get("InternalUniquenessConstraint1").covers), 2)
        self.assertEquals(len(get("InternalUniquenessConstraint4").covers), 1)
        self.assertEquals(len(get("InternalUniquenessConstraint9").covers), 1)
        self.assertEquals(len(get("InternalUniquenessConstraint10").covers), 1)

    def test_overlap_but_cannot_transform(self):
        """ Test case where there is overlap but due to properties of the 
            constraints we can't transform them. """
        fname = TestData.path("overlapping_iuc_no_transform.orm")
        loader = NormaLoader(fname)
        model = loader.model 
        get = model.constraints.get

        old_cons = model.constraints.of_type(FrequencyConstraint)

        self.assertEquals(len(old_cons), 6)

        # Run transformation and confirm return value is false
        self.assertFalse(OverlappingIFCTransformation(model).execute())

        # Confirm nothing changed
        self.assertEquals(len(old_cons), 6)

        fc1 = get("FC1")
        self.assertEquals(fc1.min_freq, 1)
        self.assertEquals(fc1.max_freq, 3)
        self.assertEquals(len(fc1.covers), 3)

        fc2 = get("FC2")
        self.assertEquals(fc2.min_freq, 2)
        self.assertEquals(fc2.max_freq, 4)
        self.assertEquals(len(fc2.covers), 3)

        fc3 = get("FC3")
        self.assertEquals(fc3.min_freq, 2)
        self.assertEquals(fc3.max_freq, 2)
        self.assertEquals(len(fc3.covers), 2)

        self.assertEquals(len(get("IUC1").covers), 1)

        fc4 = get("FC4")
        self.assertEquals(fc4.min_freq, 2)
        self.assertEquals(fc4.max_freq, 2)
        self.assertEquals(len(fc4.covers), 2)
        
        fc5 = get("FC5")
        self.assertEquals(fc5.min_freq, 2)
        self.assertEquals(fc5.max_freq, 2)
        self.assertEquals(len(fc5.covers), 2)

    def test_ifc_transforms(self):
        """ Test successful application of IFC transformations."""
        fname = TestData.path("overlapping_iuc_transform.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        obj = model.object_types.get
        cons = model.constraints.get
        fact = model.fact_types.get

        # Check AHasBC
        role1, role2, role3 = fact("AHasBC").roles
        self.assertItemsEqual(cons("IUC_AB").covers, [role1, role2])
        self.assertItemsEqual(cons("IUC_B").covers, [role2])
        self.assertItemsEqual(cons("IUC_BC").covers, [role2, role3])

        # Check DHasEF
        role1, role2, role3 = fact("DHasEF").roles
        self.assertItemsEqual(cons("IUC_DE").covers, [role1, role2])
        self.assertItemsEqual(cons("IUC_EF").covers, [role2, role3])

        # Check GHasH
        role1, role2 = fact("GHasH").roles
        self.assertItemsEqual(cons("IUC_G").covers, [role1])
        self.assertItemsEqual(cons("IUC_GH").covers, [role1, role2])

        # Check IHasIJJ
        role1, role2, role3, role4 = fact("IHasIJJ").roles
        self.assertItemsEqual(cons("IUC_II").covers, [role1, role2])
        self.assertItemsEqual(cons("IUC_IJ").covers, [role2, role3])
        self.assertItemsEqual(cons("IUC_JJ").covers, [role3, role4])

        # Check KHasLM
        role1, role2, role3 = fact("KHasLM").roles
        self.assertItemsEqual(cons("IUC_KLM").covers, [role1, role2, role3])
        self.assertItemsEqual(cons("IUC_KL").covers, [role1, role2])
        self.assertItemsEqual(cons("IUC_LM").covers, [role2, role3])

        # Check NHasO
        role1, role2 = fact("NHasO").roles
        self.assertItemsEqual(cons("FC_NO").covers, [role1, role2])
        self.assertEquals(cons("FC_NO").min_freq, 1)
        self.assertEquals(cons("FC_NO").max_freq, 3)
        self.assertItemsEqual(cons("FC_O").covers, [role2])
        self.assertEquals(cons("FC_O").min_freq, 2)
        self.assertEquals(cons("FC_O").max_freq, 4)

        # Check PHasQ
        role1, role2 = fact("PHasQ").roles
        self.assertItemsEqual(cons("FC_PQ").covers, [role1, role2])
        self.assertEquals(cons("FC_PQ").min_freq, 1)
        self.assertEquals(cons("FC_PQ").max_freq, 2)
        self.assertItemsEqual(cons("FC_Q").covers, [role2])
        self.assertEquals(cons("FC_Q").min_freq, 1)
        self.assertEquals(cons("FC_Q").max_freq, 2)

        # Check RHasST
        role1, role2, role3 = fact("RHasST").roles
        self.assertItemsEqual(cons("IUC_RS").covers, [role1, role2])
        self.assertItemsEqual(cons("FC_ST").covers, [role2, role3])
        self.assertEquals(cons("FC_ST").min_freq, 1)
        self.assertEquals(cons("FC_ST").max_freq, 2)

        # Check UHasVW
        role1, role2, role3 = fact("UHasVW").roles
        self.assertItemsEqual(cons("IUC_UV").covers, [role1, role2])
        self.assertItemsEqual(cons("FC_VW").covers, [role2, role3])
        self.assertEquals(cons("FC_VW").min_freq, 2)
        self.assertEquals(cons("FC_VW").max_freq, float('inf'))

        # Assert that transformation does something
        trans = OverlappingIFCTransformation(model)
        self.assertTrue(trans.execute())
        #####################################################################

        # Check AHasBC after transformation
        role1, role2, role3 = fact("AHasBC").roles
        self.assertIsNone(cons("IUC_AB")) # REMOVED
        self.assertItemsEqual(cons("IUC_B").covers, [role2])
        self.assertIsNone(cons("IUC_BC")) # REMOVED

        # Check DHasEF after transformation
        role1, role2, role3 = fact("DHasEF").roles
        self.assertItemsEqual(cons("IUC_DE").covers, [role1])
        self.assertItemsEqual(cons("IUC_EF").covers, [role2, role3])

        # Check GHasH after transformation
        role1, role2 = fact("GHasH").roles
        self.assertItemsEqual(cons("IUC_G").covers, [role1])
        self.assertIsNone(cons("IUC_GH"))

        # Check IHasIJJ after transformation
        role1, role2, role3, role4 = fact("IHasIJJ").roles
        self.assertItemsEqual(cons("IUC_II").covers, [role1])
        self.assertItemsEqual(cons("IUC_IJ").covers, [role2])
        self.assertItemsEqual(cons("IUC_JJ").covers, [role3, role4])

        # Check KHasLM after transformation
        role1, role2, role3 = fact("KHasLM").roles
        self.assertIsNone(cons("IUC_KLM"))
        self.assertItemsEqual(cons("IUC_KL").covers, [role1])
        self.assertItemsEqual(cons("IUC_LM").covers, [role2, role3])

        # Check NHasO after transformation
        role1, role2 = fact("NHasO").roles
        self.assertItemsEqual(cons("FC_NO").covers, [role1])
        self.assertEquals(cons("FC_NO").min_freq, 1)
        self.assertEquals(cons("FC_NO").max_freq, 1)
        self.assertItemsEqual(cons("FC_O").covers, [role2])
        self.assertEquals(cons("FC_O").min_freq, 2)
        self.assertEquals(cons("FC_O").max_freq, 4)

        # Check PHasQ after transformation
        role1, role2 = fact("PHasQ").roles
        self.assertIsNone(cons("FC_PQ"))
        self.assertItemsEqual(cons("FC_Q").covers, [role2])
        self.assertEquals(cons("FC_Q").min_freq, 1)
        self.assertEquals(cons("FC_Q").max_freq, 1)

        # Check RHasST after transformation
        role1, role2, role3 = fact("RHasST").roles
        self.assertItemsEqual(cons("IUC_RS").covers, [role1, role2])
        self.assertItemsEqual(cons("FC_ST").covers, [role3])
        self.assertEquals(cons("FC_ST").min_freq, 1)
        self.assertEquals(cons("FC_ST").max_freq, 1)

        # Check UHasVW after transformation
        role1, role2, role3 = fact("UHasVW").roles
        self.assertItemsEqual(cons("IUC_UV").covers, [role1])
        self.assertItemsEqual(cons("FC_VW").covers, [role2, role3])
        self.assertEquals(cons("FC_VW").min_freq, 2)
        self.assertEquals(cons("FC_VW").max_freq, float('inf'))

        # Check added, modified, removed
        self.assertItemsEqual(trans.added, [])
        self.assertItemsEqual(["IUC_AB", "IUC_BC", "IUC_GH", "IUC_KLM", "FC_PQ"], 
                              [cons.name for cons in trans.removed])
        self.assertItemsEqual(["IUC_DE", "IUC_II", "IUC_IJ", "IUC_KL", "FC_NO", "FC_Q", "FC_ST", "IUC_UV"], 
                              [cons.name for cons in trans.modified])
        
    def test_preservation_of_ref_roles(self):
        """ Test that removing an identifying constraint does not change the 
            list of ref roles for an object type. """
        fname = TestData.path("fact_type_tests.orm")
        loader = NormaLoader(fname)
        model = loader.model        

        a = model.object_types.get("A")
        role0 = model.fact_types.get("AHasB").roles[0]
        role1 = model.fact_types.get("AExists").roles[0]
        role2 = model.fact_types.get("AHasAId").roles[0]

        self.assertItemsEqual(a.roles, [role0, role1, role2])
        self.assertItemsEqual(a.ref_roles, [role2])

        ident = model.constraints.get("Ident_A")

        self.assertIs(a.identifying_constraint, ident)
        self.assertIs(ident.identifier_for, a)

        # Add a constraint which will sort before Ident_A by name
        model.add(UniquenessConstraint(name="__A", covers=ident.covers))

        trans = OverlappingIFCTransformation(model)
        self.assertTrue(trans.execute())

        self.assertItemsEqual(trans.removed, [ident])
        self.assertIsNone(model.constraints.get("Ident_A"))

        # A no longer has an identifying constraint
        self.assertIs(a.identifying_constraint, None)

        # However, its reference role hasn't changed
        self.assertItemsEqual(a.ref_roles, [role2])

##############################################################################
# EUCStrengtheningTransformation tests
##############################################################################
class TestEUCStrengtheningTransformation(TestCase):
    """ Unit tests for the EUCStrengtheningTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_simple_linear_path(self):
        """ Test EUC strengthening on simple linear path. """
        fname = TestData.path("join_rule_valid_linear_path_euc.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        euc = model.constraints.get("EUC")
        self.assertEquals(len(euc.covers), 2)

        # Assert that transformation does something
        trans = EUCStrengtheningTransformation(model)
        self.assertTrue(trans.execute())

        # Confirm EUC no longer in model
        self.assertIsNone(model.constraints.get("EUC"))

        # Get new uniqueness constraints
        root_cons = model.fact_types.get("AHasB").roles[0].covered_by[0]
        self.assertTrue(isinstance(root_cons, UniquenessConstraint))
        self.assertEquals(len(root_cons.covers), 1)

        new_cons1 = model.fact_types.get("BHasC").roles[0].covered_by[1]
        self.assertTrue(isinstance(new_cons1, UniquenessConstraint))
        self.assertEquals(len(new_cons1.covers), 1)

        # First role of CHasD already covered by a simple IUC, so there should
        # not be a new one added
        role = model.fact_types.get("CHasD").roles[0]
        cons = model.constraints.get("IUC_C")
        self.assertEquals(role.covered_by, [cons])
        self.assertEquals(len(cons.covers), 1)

        # Check added, modified, removed lists
        self.assertItemsEqual(trans.added, [root_cons, new_cons1])
        self.assertItemsEqual(trans.removed, [euc])
        self.assertItemsEqual(trans.modified, [])

    def test_compound_ref_scheme(self):
        """ Test using EUC strengthening for compound ref scheme. """
        fname = TestData.path("absorption_valid_four_facts.orm")
        loader = NormaLoader(fname)
        model = loader.model

        euc = model.constraints.get("EUC1")
        a = model.object_types.get("A")

        self.assertEquals(len(euc.covers), 4)
        self.assertIs(euc.identifier_for, a)
        self.assertIs(a.identifying_constraint, euc)
        self.assertItemsEqual(a.ref_roles, a.roles)

        trans = EUCStrengtheningTransformation(model)
        self.assertTrue(trans.execute())

        # Confirm EUC removed
        self.assertIsNone(model.constraints.get("EUC1"))

        # Assert a has no identifying constraint but ref roles haven't changed
        self.assertIsNone(a.identifying_constraint)
        self.assertItemsEqual(a.ref_roles, a.roles)

        # Confirm constraints the same on ref roles
        self.assertEquals(len(a.roles[0].covered_by), 2)
        self.assertEquals(len(a.roles[1].covered_by), 2)
        self.assertEquals(len(a.roles[2].covered_by), 2)
        self.assertEquals(len(a.roles[3].covered_by), 2)

        # Confirm role played by B now covered by IUC
        role = a.roles[0].fact_type.roles[1]
        new_cons = role.covered_by[1]

        self.assertEquals(len(role.covered_by), 2)
        self.assertTrue(isinstance(new_cons, UniquenessConstraint))
        self.assertTrue(role.unique)

        self.assertEquals(model.constraints.count(), 10)

        # Check added, removed, modified lists
        self.assertItemsEqual(trans.modified, [])
        self.assertItemsEqual(trans.removed, [euc])
        self.assertItemsEqual(trans.added, [new_cons])

    def test_skipped_due_to_no_join_path(self):
        """ Test that EUC is skipped because it has no join path. """
        model = Model.Model()
        fact1 = FactType("AHasB")
        fact1.add_role(ObjectType("A"))
        fact1.add_role(ObjectType("B"))
        model.add(fact1)

        fact2 = FactType("AHasC")
        fact2.add_role(ObjectType("A"))
        fact2.add_role(ObjectType("C"))
        model.add(fact2)

        covers = RoleSequence()
        covers.extend([fact1.roles[1], fact2.roles[1]])
        
        euc = UniquenessConstraint(name="EUC", covers=covers)
        model.add(euc)

        self.assertFalse(euc.internal)
        self.assertIsNone(euc.covers.join_path)

        self.assertFalse(EUCStrengtheningTransformation(model).execute())

        self.assertIs(euc, model.constraints.get("EUC"))

    def test_skipped_due_to_join_path_out_of_order(self):
        """ EUC skipped because it doesn't cover a role on the first fact type
            along the join path. """
        fname = TestData.path("join_rule_join_path_defined_out_of_order.orm")
        loader = NormaLoader(fname)
        model = loader.model

        self.assertIsNotNone(model.constraints.get("EUC"))
        self.assertFalse(EUCStrengtheningTransformation(model).execute())
        self.assertIsNotNone(model.constraints.get("EUC"))

    def test_euc_on_branching_path(self):
        """ Test strengthening of complex branching path. """
        fname = TestData.path("join_rule_valid_complex_branching_path.orm")
        loader = NormaLoader(fname)
        model = loader.model

        euc = model.constraints.get("EUC1")

        self.assertEquals(len(euc.covers), 4)

        trans = EUCStrengtheningTransformation(model)
        self.assertTrue(trans.execute())

        # Confirm EUC removed
        self.assertIsNone(model.constraints.get("EUC1"))

        # Confirm a new IUC is on role played by D
        new_iuc = model.object_types.get("D").roles[0].covered_by[0]
        
        # Confirm all expected constraints added
        ehasb = model.fact_types.get("EHasB").roles[0].covered_by[1]
        bhasc = model.fact_types.get("BHasC").roles[0].covered_by[1]
        ghasb = model.fact_types.get("GHasB").roles[1].covered_by[1]
        fhasg = model.fact_types.get("FHasG").roles[1].covered_by[1]
        hhasg = model.fact_types.get("HHasG").roles[1].covered_by[1]

        new_cons = [new_iuc, ehasb, bhasc, ghasb, fhasg, hhasg]

        for cons in new_cons:
            self.assertTrue(isinstance(cons, UniquenessConstraint))
            self.assertTrue(cons.simple)

        # Check lists of added, modified, and removed constraints
        self.assertItemsEqual(trans.added, new_cons)
        self.assertItemsEqual(trans.removed, [euc])
        self.assertItemsEqual(trans.modified, [])   

##############################################################################
# Unsupported Subset Removal tests
##############################################################################
class TestUnsupportedSubsetRemoval(TestCase):
    """ Unit tests for the UnsupportedSubsetRemoval class. """

    def setUp(self):
        self.maxDiff = None

    def test_removed_constraints(self):
        """ Test that unsupported constraints are removed. """
        fname = TestData.path("subset_variety.orm")
        loader = NormaLoader(fname)
        model = loader.model

        sub_ok = model.constraints.get("SUB_OK")
        sub_ok2 = model.constraints.get("SUB_OK2")
        sub_ok3 = model.constraints.get("SUB_OK3")

        sub_join = model.constraints.get("SUB_JOIN")
        sub_join2 = model.constraints.get("SUB_JOIN2")

        sub_incompat = model.constraints.get("SUB_INCOMPAT")

        sub_superset_ref = model.constraints.get("SUB_SUPERSET_REF")
        sub_superset_subtype = model.constraints.get("SUB_SUPERSET_SUBTYPE")

        sub_cycle = model.constraints.get("SUB_CYCLE")

        # Assert these are all subset constraints
        self.assertTrue(isinstance(sub_ok, SubsetConstraint))
        self.assertTrue(isinstance(sub_ok2, SubsetConstraint))
        self.assertTrue(isinstance(sub_ok3, SubsetConstraint))
        self.assertTrue(isinstance(sub_join, SubsetConstraint))
        self.assertTrue(isinstance(sub_join2, SubsetConstraint))
        self.assertTrue(isinstance(sub_incompat, SubsetConstraint))
        self.assertTrue(isinstance(sub_superset_ref, SubsetConstraint))
        self.assertTrue(isinstance(sub_superset_subtype, SubsetConstraint))
        self.assertTrue(isinstance(sub_cycle, SubsetConstraint))

        # Execute transformation
        trans = UnsupportedSubsetRemoval(model)
        self.assertTrue(trans.execute())
    
        # OK constraints still in model        
        self.assertIsNotNone(model.constraints.get("SUB_OK"))
        self.assertIsNotNone(model.constraints.get("SUB_OK2"))
        self.assertIsNotNone(model.constraints.get("SUB_OK3"))

        # Unsupported constraints removed
        self.assertIsNone(model.constraints.get("SUB_JOIN"))
        self.assertIsNone(model.constraints.get("SUB_JOIN2"))
        self.assertIsNone(model.constraints.get("SUB_INCOMPAT"))
        self.assertIsNone(model.constraints.get("SUB_SUPERSET_REF"))
        self.assertIsNone(model.constraints.get("SUB_SUPERSET_SUBTYPE"))
        self.assertIsNone(model.constraints.get("SUB_CYCLE"))

        # Check lists of added, modified, and removed constraints
        self.assertItemsEqual(trans.added, [])
        self.assertItemsEqual(trans.removed, 
                              [sub_join, sub_join2, sub_incompat, sub_superset_ref,
                               sub_superset_subtype, sub_cycle])
        self.assertItemsEqual(trans.modified, []) 

    def test_direct_subsets_function(self):
        """ Test direct_subsets function that returns subset roles adjacent to a role. """
        fname = TestData.path("subset_variety.orm")
        loader = NormaLoader(fname)
        model = loader.model

        role = model.fact_types.get("ALikesC").roles[1]
        role2 = model.fact_types.get("BHasC").roles[1]

        #trans = UnsupportedSubsetRemoval(model)

        actual = [(r, c.name) for (r,c) in direct_subsets(role)]

        expected = [(role2, "SUB_OK3"), (role2, "SUB_JOIN")]

        self.assertItemsEqual(actual, expected) 

    def test_cycle_detection_1(self):
        """ Test cycle detection #1. """
        fname = TestData.path("subset_variety.orm")
        loader = NormaLoader(fname)
        model = loader.model

        sub_cycle = model.constraints.get("SUB_CYCLE")
        self.assertIsNotNone(sub_cycle)

        trans = UnsupportedSubsetRemoval(model)
        trans._remove_subset_cycles()

        self.assertIsNone(model.constraints.get("SUB_CYCLE"))
        self.assertItemsEqual(trans.removed, [sub_cycle])   

    def test_cycle_detection_no_cycle(self):
        """ Model has undirected cycle but not a directed cycle. """
        fname = TestData.path("subset_no_cycle.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        trans = UnsupportedSubsetRemoval(model)
        self.assertFalse(trans.execute())

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

    def test_simple_cycle_detection(self):
        """ Model has a simple directed cycle. """
        fname = TestData.path("subset_simple_cycle.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        trans = UnsupportedSubsetRemoval(model)
        self.assertTrue(trans.execute())

        self.assertEquals(3, len(model.constraints.of_type(SubsetConstraint)))

        # Transformation does nothing now that cycles are removed
        self.assertFalse(UnsupportedSubsetRemoval(model).execute())

    def test_simple_cycle_detection_2(self):
        """ Model has a simple directed cycle requiring deletion of 2 constraints. """
        fname = TestData.path("subset_simple_cycle_2.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        self.assertEquals(6, len(model.constraints.of_type(SubsetConstraint)))

        trans = UnsupportedSubsetRemoval(model)
        self.assertTrue(trans.execute())

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        # Transformation does nothing now that cycles are removed
        self.assertFalse(UnsupportedSubsetRemoval(model).execute())

    def test_simple_cycle_detection_3(self):
        """ Model has a simple directed cycle requiring deletion of 2 
            constraints on the same fact type. """
        fname = TestData.path("subset_simple_cycle_3.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        trans = UnsupportedSubsetRemoval(model)
        self.assertTrue(trans.execute())

        self.assertTrue(1 <= len(model.constraints.of_type(SubsetConstraint)) <= 2)

        # Transformation does nothing now that cycles are removed
        self.assertFalse(UnsupportedSubsetRemoval(model).execute())

##############################################################################
# Tuple Subset Transformation tests
##############################################################################
class TestTupleSubsetTransformation(TestCase):
    """ Unit tests for the TupleSubsetTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_ternary_subset(self):
        """ Test transformation of ternary subset. """
        fname = TestData.path("subset_tuple.orm")
        loader = NormaLoader(fname)
        model = loader.model 

        subset = model.constraints.get("SUB1")
        uniq = model.constraints.get("IUC1")

        self.assertIsNotNone(subset)
        self.assertIsNotNone(uniq)

        self.assertEquals(1, len(model.constraints.of_type(SubsetConstraint)))
        self.assertEquals(2, len(model.constraints.of_type(UniquenessConstraint)))

        # Transform model
        trans = TupleSubsetTransformation(model)
        self.assertTrue(trans.execute())

        # Confirm tuple subset is still present
        self.assertIsNotNone(model.constraints.get("SUB1"))
        self.assertIsNotNone(model.constraints.get("IUC1"))

        # Confirm new simple subsets added
        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))
        self.assertEquals(4, len(model.constraints.of_type(UniquenessConstraint)))

        fact_type = model.fact_types.get("AHasBCD")

        # Check constraints on role played by A
        sc0 = fact_type.roles[0].covered_by[0]
        sc1 = fact_type.roles[0].covered_by[1]
        uc1 = fact_type.roles[0].covered_by[2]

        self.assertIs(sc0, subset)
        self.assertTrue(isinstance(sc1, SubsetConstraint))
        self.assertEquals(len(sc1.subset), 1)
        self.assertTrue(isinstance(uc1, UniquenessConstraint))
        self.assertTrue(len(uc1.covers), 1)

        # Check constraints on role played by B
        uc2 = fact_type.roles[1].covered_by[0]
        sc0 = fact_type.roles[1].covered_by[1]
        sc2 = fact_type.roles[1].covered_by[2]

        self.assertIs(sc0, subset)
        self.assertIs(uc2, uniq)
        self.assertTrue(isinstance(sc2, SubsetConstraint))
        self.assertEquals(len(sc2.subset), 1)

        # Check constraints on role played by C
        self.assertEquals(fact_type.roles[2].covered_by, [])

        # Check constraints on role played by D
        sc0 = fact_type.roles[3].covered_by[0]
        sc3 = fact_type.roles[3].covered_by[1]
        uc3 = fact_type.roles[3].covered_by[2]

        self.assertIs(sc0, subset)
        self.assertTrue(isinstance(sc3, SubsetConstraint))
        self.assertEquals(len(sc3.subset), 1)
        self.assertTrue(isinstance(uc3, UniquenessConstraint))
        self.assertTrue(len(uc3.covers), 1)

        # Check contents of added, removed, modified
        self.assertItemsEqual(trans.added, [sc1, sc2, sc3, uc1, uc3])
        self.assertItemsEqual(trans.removed, [])
        self.assertItemsEqual(trans.modified, [])

##############################################################################
# Root Role Transformation tests
##############################################################################
class TestRootRoleTransformation(TestCase):
    """ Unit tests for the RootRoleTransformation class. """

    def setUp(self):
        self.maxDiff = None

    def test_subset_single_root(self):
        """ Subset graph has a single root. """
        fname = TestData.path("subset_no_cycle.orm")
        loader = NormaLoader(fname)
        model = loader.model

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        # Execute transformation
        trans = RootRoleTransformation(model)
        self.assertFalse(trans.execute())

        # Confirm no change in constraints
        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        expected_root = model.fact_types.get("ASmokes").roles[0]

        # KEY: Confirm all roles played by A have expected root
        roles = [r for r in model.object_types.get("A").roles if r != expected_root]

        self.assertEquals(3, len(roles))

        for role in roles:
            self.assertIs(role.root_role, expected_root)

        # Confirm roles played by B have no root
        b = model.object_types.get("B")
        self.assertFalse(hasattr(b.roles[0], "root_role"))
        self.assertFalse(hasattr(b.roles[1], "root_role"))

        # Check contents of added, removed, modified
        self.assertItemsEqual(trans.added, [])
        self.assertItemsEqual(trans.removed, [])
        self.assertItemsEqual(trans.modified, [])     

    def test_subset_multiple_roots(self):
        """ Subset graph has multiple roots. """
        fname = TestData.path("subset_multiple_roots.orm")
        loader = NormaLoader(fname)
        model = loader.model
  
        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        # Execute transformation
        trans = RootRoleTransformation(model)
        self.assertTrue(trans.execute())

        # Confirm addition of two new subset constraints
        self.assertEquals(6, len(model.constraints.of_type(SubsetConstraint)))

        a = model.object_types.get("A")
        asmokes = model.fact_types.get("ASmokes")
        aexists = model.fact_types.get("AExists")
        alikesb = model.fact_types.get("ALikesB")

        sub1 = asmokes.roles[0].covered_by[2] # covered_by[0] is an IUC

        self.assertTrue(isinstance(sub1, SubsetConstraint))
        self.assertItemsEqual(sub1.subset, [asmokes.roles[0]])
        self.assertItemsEqual(sub1.superset, [alikesb.roles[0]])

        sub2 = aexists.roles[0].covered_by[3] # covered_by[0] is IUC, [1] is subset, [2] is cardinality
        self.assertTrue(isinstance(sub2, SubsetConstraint))
        self.assertItemsEqual(sub2.subset, [aexists.roles[0]])
        self.assertItemsEqual(sub2.superset, [alikesb.roles[0]])

        # Confirm all of A's roles roots are the A likes B role
        expected_root = alikesb.roles[0]
        roles = [r for r in a.roles if r != expected_root]

        self.assertEquals(len(roles), 4)

        for role in roles:
            self.assertIs(role.root_role, expected_root)        

        # Confirm A's A likes B role has no root
        self.assertFalse(hasattr(expected_root, "root_role"))

        # Confirm B's subset role has correct root_role        
        b = model.object_types.get("B")
        b1 = model.fact_types.get("AHasB").roles[1]
        b2 = model.fact_types.get("ALikesB").roles[1]

        self.assertTrue(hasattr(b1, "root_role"))
        self.assertFalse(hasattr(b2, "root_role"))
        self.assertIs(b1.root_role, b2)

        # Confirm C's role has no root_role attribute
        c = model.object_types.get("C")
        self.assertFalse(hasattr(c.roles[0], "root_role"))

        # Check contents of added, removed, modified
        self.assertItemsEqual(trans.added, [sub1, sub2])
        self.assertItemsEqual(trans.removed, [])
        self.assertItemsEqual(trans.modified, [])

    def test_root_on_subtype_and_supertype(self):
        """ Subset graph has multiple roots, where one is a subtype and
            one is a supertype. """
        fname = TestData.path("subset_root_role_test.orm")
        loader = NormaLoader(fname)
        model = loader.model
  
        self.assertEquals(3, len(model.constraints.of_type(SubsetConstraint)))

        # Execute transformation
        trans = RootRoleTransformation(model)
        self.assertTrue(trans.execute())

        self.assertEquals(4, len(model.constraints.of_type(SubsetConstraint)))

        root1 = model.fact_types.get("AExists").roles[0]
        root2 = model.fact_types.get("BExists").roles[0]

        self.assertFalse(hasattr(root1, "root_role"))
        self.assertIs(root2.root_role, root1)
        
