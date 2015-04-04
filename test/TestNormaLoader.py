##############################################################################
# Package: ormpy
# File:    TestNormaLoader.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.NormaLoader class """

import os
from unittest import TestCase
from datetime import datetime, date, time
from nose.plugins.logcapture import LogCapture

import lib.TestDataLocator as TestDataLocator

from lib.NormaLoader import NormaLoader
from lib.ModelElement import ModelElement
from lib.FactType import FactType

import lib.ObjectType as ObjectType
import lib.Constraint as Constraint
import lib.Domain as Domain

class TestNormaLoader(TestCase):
    """ Unit tests for the NormaLoader class. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir() + os.sep
        self.maxDiff = None

        # Log capturing
        self.log = LogCapture()
        self.log.logformat = '%(levelname)s: %(message)s'
        self.log.begin()

    def test_add_from_empty_stack(self):
        """ Check behavior of add_from_stack when empty. """
        loader = NormaLoader(self.data_dir + "empty_model.orm")
        self.assertEquals(loader.model.object_types.count(), 0)
        loader._add_from_stack()
        self.assertEquals(loader.model.object_types.count(), 0)                

    def test_bad_filename_extension(self):
        """ Confirm that exception is raised when input file has .txt extension 
            rather than .orm extension. """
        with self.assertRaises(Exception) as ex:
            NormaLoader("test.txt")
        self.assertEqual(ex.exception.message, 
            "Input filename must have .orm extension.")

    def test_bad_root_element(self):
        """ Confirm that exception is raised when the root element of the
            XML is not <ormRoot:ORM2>. """
        with self.assertRaises(Exception) as ex:
            NormaLoader(self.data_dir + "bad_root_element.orm")
        self.assertEqual(ex.exception.message, 
            "Root of input file must be <ormRoot:ORM2>.")

    def test_no_model_element(self):
        """ Confirm that exception is raised when the XML does not contain an
            ORMModel element. 
        """
        with self.assertRaises(Exception) as ex:
            NormaLoader(self.data_dir + "no_model_element.orm")
        self.assertEqual(ex.exception.message, 
            "Cannot find <orm:ORMModel> in input file.")

    def test_empty_model(self):
        """ Confirm a successful parse on a small input file. """
        model = NormaLoader(self.data_dir + "empty_model.orm").model
        self.assertEqual(model.object_types.count(), 0)
        self.assertEqual(model.fact_types.count(), 0)
        self.assertEqual(model.constraints.count(), 0)

    def test_adding_invalid_element(self):
        """ Confirm exception is raised if an invalid object is passed to
            the _add() method."""
        loader = NormaLoader(self.data_dir + "empty_model.orm")
        with self.assertRaises(Exception) as ex:
            loader._add(ModelElement(uid="123", name="ABC"))
        self.assertEqual(ex.exception.message, "Unexpected model element type")
        
    def test_subtypes(self):
        """ Confirm that subtype derivation rule omission note
            is added to self.omissions and that subtype constraints load 
            properly. Also confirm that if inclusive-or or XOR constraints
            are present on a subtype, they are reported in the omissions. """
        loader = NormaLoader(self.data_dir + "subtype_with_derivation.orm")
        model = loader.model

        self.assertItemsEqual(loader.omissions, 
            ["Subtype derivation rule for B", 
             "Subtype exclusion constraint ExclusiveOrConstraint1",
             "Subtype inclusive-or constraint InclusiveOrConstraint1",
             "Subtype inclusive-or constraint InclusiveOrConstraint2"])

        cons1 = model.constraints.get("BIsASubtypeOfA")
        self.assertIs(cons1.subtype, model.object_types.get("B"))
        self.assertIs(cons1.supertype, model.object_types.get("A"))
        self.assertEquals(cons1.covers, [cons1.subtype, cons1.supertype])
        self.assertTrue(cons1.idpath)

        self.assertFalse(model.constraints.get("BIsASubtypeOfC").idpath)        

    def test_subtypefact_constraints(self):
        """ Confirm IUC and mandatory constraints on implicit subtype fact types
            are ignored, because those fact types are ignored. """
        loader = NormaLoader(self.data_dir + "subtype_with_derivation.orm")
        model = loader.model
 
        # Note: the mandatory and uniqueness constraints below are on the 
        # reference fact types (e.g. ZHasZId)
        expected = ['CIsASubtypeOfZ', 'AIsASubtypeOfZ', 'BIsASubtypeOfC',
                    'BIsASubtypeOfA', 
                    'SimpleMandatoryConstraint7',
                    'InternalUniquenessConstraint13',
                    'InternalUniquenessConstraint14',
                    'SimpleMandatoryConstraint1',
                    'InternalUniquenessConstraint1',
                    'InternalUniquenessConstraint2',                    
                    'SimpleMandatoryConstraint3',
                    'InternalUniquenessConstraint5',
                    'InternalUniquenessConstraint6']
        actual = [cons.name for cons in model.constraints]

        self.assertItemsEqual(actual, expected)                   


    def test_subtype_exception(self):
        """ Confirm subtype exception fires for corrupted data. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "corrupted_subtype.orm")
        self.assertEquals(ex.exception.message, 
            "Cannot load subtype constraint.")
        
    def test_load_object_types(self):
        """ Test of object type load. """
        self.log.beforeTest(None)
        loader = NormaLoader(self.data_dir + "object_type_tests.orm")
        model = loader.model

        # No derivation rules
        self.assertItemsEqual(loader.omissions, [])
        self.assertItemsEqual(self.log.formatLogRecords(), [])

        # Overall count
        self.assertEqual(model.object_types.count(), 10)

        # Independent Entity
        this = model.object_types.get("D") 
        self.assertTrue(this.independent)
        self.assertIs(this.identifying_constraint, 
            model.constraints.get("InternalUniquenessConstraint7"))
        self.assertIsInstance(this, ObjectType.EntityType)

        # Non-independent Entity
        this = model.object_types.get("C")
        self.assertFalse(this.independent)

        # Independent value
        this = model.object_types.get("V2")
        self.assertTrue(this.independent)
        self.assertEquals(this.uid, "_FD295AC2-D845-48E4-9E09-2E48EC99E3F3")
        self.assertIsInstance(this, ObjectType.ValueType)

        # Non-independent value
        this = model.object_types.get("V1")
        self.assertFalse(this.independent)

        # Implicit value (created by unary fact type): should not be loaded
        this = model.object_types.get("A exists")
        self.assertIsNone(this)

        # Objectified Independent
        this = model.object_types.get("CHasV1")
        self.assertTrue(this.independent)
        self.assertIsInstance(this, ObjectType.ObjectifiedType)

        # Objectified Non-independent
        this = model.object_types.get("V1HasV2")
        nested = model.fact_types.get("V1HasV2")
        self.assertFalse(this.independent)
        self.assertIs(this.identifying_constraint, 
            model.constraints.get("InternalUniquenessConstraint14"))
        self.assertIs(this.nested_fact_type, nested)

        # Implicit Objectified (Created by ternary, should not load)
        this = model.object_types.get("V1HasDHasV2") 
        self.assertIsNone(this)

        self.log.afterTest(None)

    def test_played_roles(self):
        """ Confirm that object types know the list of roles they play. """
        model = NormaLoader(self.data_dir + "object_type_tests.orm").model

        obj_type0 = model.object_types.get("B")
        obj_type1 = model.object_types.get("V1HasV2")
        obj_type2 = model.object_types.get("D")

        self.assertItemsEqual(obj_type0.roles, [])  

        r1 = model.fact_types.get("V1HasV2Exists").roles[0]
        
        self.assertItemsEqual(obj_type1.roles, [r1])

        r1 = model.fact_types.get("V1HasDHasV2").roles[1]
        r2 = model.fact_types.get("DHasDId").roles[0]

        self.assertItemsEqual(obj_type2.roles, [r1, r2])      

    def test_data_type_load(self):
        """ Confirm data types are loaded properly for Value Types. """
        model = NormaLoader(self.data_dir + "data_types.orm").model
        ot = model.object_types

        self.assertIsInstance(ot.get("A").domain, Domain.StringDomain)   # data type undefined
        self.assertIsInstance(ot.get("B").domain, Domain.BoolDomain)     # True or false
        self.assertIsInstance(ot.get("C").domain, Domain.BoolDomain)     # Yes or no
        self.assertIsInstance(ot.get("D").domain, Domain.IntegerDomain)  # auto counter
        self.assertIsInstance(ot.get("E").domain, Domain.FloatDomain)    # float
        self.assertIsInstance(ot.get("Special").domain, Domain.FloatDomain)  # float
        self.assertIsInstance(ot.get("F").domain, Domain.FloatDomain)    # money
        self.assertIsInstance(ot.get("G").domain, Domain.IntegerDomain)  # big int
        self.assertIsInstance(ot.get("H").domain, Domain.DateTimeDomain) # timestamp
        self.assertIsInstance(ot.get("I").domain, Domain.DateDomain)     # date
        self.assertIsInstance(ot.get("J").domain, Domain.TimeDomain)     # time
        self.assertIsInstance(ot.get("K").domain, Domain.StringDomain)   # text

        # Confirm for A and K that prefix is 'A' and 'K'
        obj = ot.get("A")
        actual = obj.domain.draw(2)
        expect = ['A0', 'A1']
        self.assertItemsEqual(actual, expect)

        obj = ot.get("K")
        actual = obj.domain.draw(2)
        expect = ['K0', 'K1']
        self.assertItemsEqual(actual, expect)        


    def test_unknown_data_type(self):
        """ Confirm that domain defaults to StringDomain() if the actual type 
            is unexpected. """
        model = NormaLoader(self.data_dir + "unknown_data_types.orm").model

        obj = model.object_types.get("A") 
        self.assertIsInstance(obj.domain, Domain.StringDomain)
        self.assertItemsEqual(obj.domain.draw(1), ["A0"])

        obj = model.object_types.get("B")
        self.assertIsInstance(obj.domain, Domain.StringDomain)
        self.assertItemsEqual(obj.domain.draw(1), ["B0"])

    def test_value_constraint_on_types(self):
        """ Confirm that value constraints on value types are loaded. """
        model = NormaLoader(
            self.data_dir + "test_value_type_value_constraint.orm").model
        cons1 = model.constraints.get("ValueConstraint1")
        
        self.assertEquals(cons1.uid, "_9F61B75E-FB59-456F-97A9-E4CF104FABE5")
        self.assertIs(cons1.covers[0], model.object_types.get("A"))

        expected = set([1,2,6] + range(10,20) + range(101, 200))
        self.assertItemsEqual(cons1.domain.draw(112), expected)
        self.assertEquals(cons1.size, 112)

    def test_load_fact_types(self):
        """ Confirm fact types load successfully. """
        loader = NormaLoader(self.data_dir + "fact_type_tests.orm")
        model = loader.model

        # Confirm reference scheme fact type loads
        ftype1 = model.fact_types.get("AHasAId")
        self.assertEquals(ftype1.uid, "_8C96FD40-5E82-4E8F-B5EE-C6CEE8BCF74B")
        self.assertIsInstance(ftype1, FactType)  

        # Confirm derivation rule added to omissions
        self.assertItemsEqual(loader.omissions, 
            ["Fact type derivation rule for AHasB",
             "Fact type derivation rule for AHasAId"])

        # Check role player
        typea = model.object_types.get("A")
        typeb = model.object_types.get("B")
        ahasb = model.fact_types.get("AHasB")
        self.assertIs(ahasb.roles[0].player, typea)
        self.assertIs(ahasb.roles[1].player, typeb)

        # Check role fact type
        self.assertIs(ahasb.roles[0].fact_type, ahasb)
        self.assertIs(ahasb.roles[1].fact_type, ahasb)

        # Check that implicit role added to unary is removed
        aexists = model.fact_types.get("AExists")
        self.assertIs(aexists.roles[0].player, typea)
        self.assertEquals(aexists.arity(), 1)

        # Test role value constraint
        cons1 = model.constraints.get("RoleValueConstraint1")

        expected = ['A', 'Dog', '3.567', '12/23/2014']
        self.assertItemsEqual(cons1.domain.draw(4), expected)


    def test_forced_implicit(self):
        """ Exercise branch in _load_fact_types when arity() = 0. """
        loader = NormaLoader(self.data_dir + "forced_implicit_binary.orm")
        model = loader.model
        
        # The object types are both marked implicit so the corresponding
        # fact type should not load either.
        self.assertEquals(model.object_types.count(), 0)
        self.assertEquals(model.fact_types.count(), 0)
      
    def test_derivation_source(self):
        """ Confirm depricated DerivationSource element is ignored. """
        self.log.beforeTest(None)
        loader = NormaLoader(self.data_dir + "derivation_source.orm")

        expected = ["Role derivation rule within AHasB"]

        # Check omissions array
        self.assertItemsEqual(loader.omissions, expected)

        # Check log contents
        expected = ["WARNING: 1 model element was ignored while loading derivation_source.orm."] + \
                   ["INFO: Ignoring " + expected[0]]

        self.assertItemsEqual(self.log.formatLogRecords(), expected)

        self.log.afterTest(None)

    def test_constraints_omitted(self):
        """ Confirm omitted constraints get saved to omissions list."""
        self.log.beforeTest(None)
        loader = NormaLoader(self.data_dir + "omitted_constraints.orm")

        expected = ["Equality constraint EqualityConstraint1",
             "Exclusion constraint ExclusionConstraint1",
             "Exclusion constraint ExclusiveOrConstraint1",
             "Inclusive-or constraint InclusiveOrConstraint1",
             "Inclusive-or constraint InclusiveOrConstraint2",
             "Ring constraint RingConstraint1",
             "Value comparison constraint ValueComparisonConstraint1"]

        # Check omissions array
        self.assertItemsEqual(loader.omissions, expected)

        # Check log contents
        expected = ["WARNING: 7 model elements were ignored while loading omitted_constraints.orm."] + \
                   ["INFO: Ignoring " + msg for msg in expected]

        self.assertItemsEqual(self.log.formatLogRecords(), expected)

        self.log.afterTest(None)

    def test_subset_constraint(self):
        """ Confirm subset constraints load correctly. """
        loader = NormaLoader(self.data_dir + "subset_constraint.orm")
        model = loader.model

        cons1 = model.constraints.get("SubsetConstraint1")
        cons2 = model.constraints.get("SubsetConstraint2")
        cons3 = model.constraints.get("SubsetConstraint3")
        cons4 = model.constraints.get("SubsetConstraint4")

        obj_a = model.object_types.get("A")
        obj_b = model.object_types.get("B")
        ahasb = model.fact_types.get("AHasB")
        alikesb = model.fact_types.get("ALikesB")
        aplus = model.fact_types.get("CPlusAPlusB")
        aand = model.fact_types.get("AAndBAndC")
        
        # Check modality
        self.assertTrue(cons1.alethic)
        self.assertFalse(cons2.alethic)

        # Check unary subset
        self.assertEquals(len(cons1.superset), 1)
        self.assertEquals(len(cons1.subset), 1)
        self.assertIs(cons1.subset[0].player, obj_a)
        self.assertIs(cons1.superset[0].player, obj_a)
        self.assertIs(cons1.subset[0].fact_type, ahasb)
        self.assertIs(cons1.superset[0].fact_type, alikesb)
        self.assertItemsEqual(cons1.covers, cons1.subset + cons1.superset)

        # Check binary subset
        self.assertEquals(len(cons4.superset), 2)
        self.assertEquals(len(cons4.subset), 2)
        self.assertIs(cons4.subset[0].fact_type, aplus)
        self.assertIs(cons4.superset[1].fact_type, aand)
        self.assertIs(cons4.subset[0].player, cons4.superset[0].player)
        self.assertIs(cons4.subset[1].player, cons4.superset[1].player)
        self.assertIs(cons4.subset[1].player, obj_b)

        # Check ternary subset
        self.assertIsNone(cons3) # Not loaded
        self.assertItemsEqual(loader.omissions, 
            ["Subset constraint SubsetConstraint3 (due to arity > 2)"])


    def test_partial_subset(self):
        """ Confirm exception fires for invalid subset constraints. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "partial_subset.orm")
        self.assertEquals(ex.exception.message, 
            "Constraint SubsetConstraint1 does not have exactly two role sequences (sub and super).")

    def test_implicit_role(self):
        """ Confirm constraint that covers implicit role is removed. """
        model = NormaLoader(self.data_dir + "test_implicit_roles.orm").model
        self.assertIsNone(model.constraints.get("SubsetConstraint1"))

    def test_deprecated_join(self):
        """ Confirm exception fires for models containing deprecated join constraint. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "deprecated_join.orm")
        self.assertEquals(ex.exception.message, 
            "Constraint SubsetConstraint1 has deprecated join rule.")

    def test_join_subset_omission(self):
        """ Confirm that join subset constraints are (for now) omitted. """
        loader = NormaLoader(self.data_dir + "join_subset_omission.orm")
        self.assertItemsEqual(loader.omissions, 
            ["Join path for SubsetConstraint1."])

        cons = loader.model.constraints.get("SubsetConstraint1")
        self.assertIsNotNone(cons.superset.join_path)

    def test_uniqueness_constraint(self):
        """ Confirm uniqueness constraints load properly. """
        model = NormaLoader(self.data_dir + "uniqueness_constraints.orm").model

        int_cons1 = model.constraints.get("InternalUniquenessConstraint4")
        int_cons2 = model.constraints.get("InternalUniquenessConstraint1")
        int_cons3 = model.constraints.get("InternalUniquenessConstraint9")
        ext_cons1 = model.constraints.get("ExternalUniquenessConstraint1")
        ext_cons2 = model.constraints.get("ExternalUniquenessConstraint2")

        obj_a = model.object_types.get("A")
        obj_b = model.object_types.get("B")
        obj_z = model.object_types.get("Z")
        ahasb = model.fact_types.get("AHasB")
        alikesb = model.fact_types.get("ALikesB")
        tern = model.fact_types.get("AAndAHoldsB")

        # Check uid
        self.assertEquals(int_cons1.uid, "_22FD96ED-BE72-4859-8DA0-1A0C98381FEF")

        # Check internal attribute
        self.assertTrue(int_cons1.internal)
        self.assertFalse(ext_cons1.internal)

        # Check modality
        self.assertTrue(int_cons1.alethic)
        self.assertFalse(ext_cons2.alethic)

        # Check Covers sequence
        self.assertEquals(len(int_cons1.covers), 1)
        self.assertIs(int_cons1.covers[0].player, obj_a)
        self.assertIs(int_cons1.covers[0].fact_type, ahasb)

        self.assertEquals(len(ext_cons2.covers), 3)
        self.assertIs(ext_cons2.covers[0].player, obj_a)
        self.assertIs(ext_cons2.covers[1].player, obj_b)
        self.assertIs(ext_cons2.covers[2].player, obj_b)
        self.assertIs(ext_cons2.covers[1].fact_type, tern)
        self.assertIs(ext_cons2.covers[2].fact_type, alikesb)

        # Confirm implicit constraints excluded
        self.assertIsNone(model.constraints.get("InternalUniquenessConstraint2"))
        self.assertEquals(model.constraints.count(), 8)

        # Test preferred identifier.
        self.assertIsNone(int_cons2.identifier_for) # implicit object type

        # Test preferred identifier
        self.assertIs(int_cons3.identifier_for, obj_z)
        self.assertIs(obj_z.identifying_constraint, int_cons3)

    def test_frequency_constraint(self):
        """ Confirm frequency constraints load properly. """
        model = NormaLoader(self.data_dir + "frequency_constraint.orm").model

        cons1 = model.constraints.get("FrequencyConstraint1")
        cons2 = model.constraints.get("FrequencyConstraint2")
        cons3 = model.constraints.get("FrequencyConstraint3")

        obj_a = model.object_types.get("A")
        obj_b = model.object_types.get("B")
        ahasb = model.fact_types.get("AHasB")
        alikesb = model.fact_types.get("ALikesB")

        # Check frequencies
        self.assertEquals(cons1.min_freq, 1)
        self.assertEquals(cons1.max_freq, 3)

        self.assertEquals(cons2.min_freq, 2)
        self.assertEquals(cons2.max_freq, 2)

        self.assertEquals(cons3.min_freq, 3)
        self.assertEquals(cons3.max_freq, float('inf'))

        # Check covered roles
        self.assertEquals(len(cons1.covers), 1)
        self.assertIs(cons1.covers[0].player, obj_b)
        self.assertIs(cons1.covers[0].fact_type, ahasb)

        self.assertEquals(len(cons2.covers), 2)

        self.assertEquals(len(cons3.covers), 2)
        self.assertIs(cons3.covers[0].fact_type, alikesb)
        self.assertIs(cons3.covers[1].fact_type, ahasb)

        # Check internal property
        self.assertTrue(cons1.internal)
        self.assertTrue(cons2.internal)
        self.assertFalse(cons3.internal)


    def test_bad_role_sequence_node(self):
        """ Confirm exception fires for invalid node in RoleSequence. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "bad_role_sequence.orm")
        self.assertEquals(ex.exception.message, "Constraint " +
            "ExternalUniquenessConstraint1 has unexpected role sequence.")

    def test_freq_on_unary(self):
        """ Confirm loader ignores frequency constraint on unary.  
            it ignores the constraint because NORMA moves the constraint
            to the implicit role of the implicit binarized fact type. """
        loader = NormaLoader(self.data_dir + "implicit_freq_constraint.orm")
        model = loader.model
        self.assertIsNone(model.constraints.get("FrequencyConstraint2"))

        # The 1 constraint is the internal UC on the unary (implicit)
        self.assertEquals(model.constraints.count(), 1)
        
        self.assertEquals(model.fact_types.get("AExists").arity(), 1)

    def test_mandatory(self):
        """ Confirm mandatory constraints are successfully loaded. """
        loader = NormaLoader(self.data_dir + "mandatory_constraint.orm")
        model = loader.model

        # Test implied
        cons1 = model.constraints.get("ImpliedMandatoryConstraint2") 
        self.assertIsNone(cons1) # Implied due to disjunctive mandatory

        cons2 = model.constraints.get("SimpleMandatoryConstraint4")
        self.assertIsNone(cons2) # Implied due to objectification

        # Confirm constraint count
        self.assertEquals(model.constraints.count(), 8)

        # Confirm all mandatories are simple
        i = 0
        for cons in model.constraints:
            if isinstance(cons, Constraint.MandatoryConstraint):
                i = i+1
                self.assertTrue(cons.simple)
                self.assertEquals(len(cons.covers), 1)

        self.assertEquals(i, 2)

        # Confirm inclusive-or ignored
        self.assertItemsEqual(loader.omissions,
            ["Inclusive-or constraint InclusiveOrConstraint1"])

        # Check assignment of mandatory to roles
        fact_type = model.fact_types.get("EHasEId")
        r1 = fact_type.roles[0]
        r2 = fact_type.roles[1]

        self.assertTrue(r1.mandatory)
        self.assertFalse(r2.mandatory)

    def test_role_names(self):
        """ Confirm role names are generated properly. """
        model = NormaLoader(self.data_dir + "role_names.orm").model

        ahasb = model.fact_types.get("AHasB")
        self.assertEquals(ahasb.roles[0].name, "R1")
        self.assertEquals(ahasb.roles[1].name, "R2")

        alikesb = model.fact_types.get("ALikesB")
        self.assertEquals(alikesb.roles[0].name, "R1")
        self.assertEquals(alikesb.roles[1].name, "Likee")

        tern = model.fact_types.get("AAndALikeB")
        self.assertEquals(tern.roles[0].name, "R2")
        self.assertEquals(tern.roles[1].name, "R3")
        self.assertEquals(tern.roles[2].name, "R4")

    def test_value_constraint_move(self):
        """ Confirm value constraints on (implicitly or explicitly) mandatory
            roles are moved to the object type. """
        loader = NormaLoader(self.data_dir + "test_value_type_value_constraint.orm")
        model = loader.model

        # Constraint directly on value type should cover value type
        cons1 = model.constraints.get("ValueConstraint1")
        obj1 = model.object_types.get("A")
        self.assertItemsEqual(cons1.covers, [obj1]) 

        # Constraint on entity type covers role played by the reference type.
        # If the ref type plays no other roles, the constraint should cover the
        # type.
        cons2 = model.constraints.get("RoleValueConstraint1")
        obj2 = model.object_types.get("ET1_id")
        self.assertItemsEqual(cons2.covers, [obj2]) 

        # Value type value constraint --- directly covers value type
        cons3 = model.constraints.get("ValueTypeValueConstraint1")
        obj3 = model.object_types.get("ET2_id")
        self.assertItemsEqual(cons3.covers, [obj3])

        # In the next two tests, the constraints are on entity types with a 
        # shared reference mode (USDValue).  Those value constraints
        # cannot be moved to the object type and thus remain on the roles. 
        cons4 = model.constraints.get("RoleValueConstraint2")
        role4 = model.fact_types.get("ET3HasUSDValue").roles[1]
        self.assertItemsEqual(cons4.covers, [role4])

        cons5 = model.constraints.get("RoleValueConstraint3")
        role5 = model.fact_types.get("ET4HasUSDValue").roles[1]
        self.assertItemsEqual(cons5.covers, [role5])

        # ET5 plays two roles: the reference role and the unary.  Thus, the 
        # role value constraint cannot be moved.
        cons6 = model.constraints.get("RoleValueConstraint4")
        role6 = model.fact_types.get("ET5Exists").roles[0]
        self.assertItemsEqual(cons6.covers, [role6]) 

        # VT1 plays only a unary role and is not independent, so the role 
        # value constraint can cover the object type instead.
        cons7 = model.constraints.get("RoleValueConstraint5")
        obj7 = model.object_types.get("VT1")
        self.assertItemsEqual(cons7.covers, [obj7])  

        # VT2 is independent, so the role value constraint cannot be moved.
        cons8 = model.constraints.get("RoleValueConstraint6")
        role8 = model.fact_types.get("VT2Exists").roles[0]
        self.assertItemsEqual(cons8.covers, [role8])             


    def test_domain_move(self):
        """ Test that domain is properly moved for value constraints on types. """
        loader = NormaLoader(self.data_dir + "test_value_type_value_constraint.orm")
        model = loader.model

        et1 = model.object_types.get("ET1")
        self.assertItemsEqual(et1.domain.draw(3), ["ET1_0", "ET1_1", "ET1_2"])

        et1_id = model.object_types.get("ET1_id")
        self.assertItemsEqual(et1_id.domain.draw(20), [1,2,3,4,5,6,7,8,9,10])

        # USDValue should not have the value constraints transferred to the 
        # object type since there are two played roles.
        usd = model.object_types.get("USDValue")
        self.assertItemsEqual(usd.domain.draw(3), [0.0,0.1,0.2])

        # VT1 has the value constraint moved over
        vt1 = model.object_types.get("VT1")
        self.assertItemsEqual(vt1.domain.draw(50), range(45,71))

    def test_invalid_value_constraint(self):
        """ Test that invalid value constraint is ignored. """
        loader = NormaLoader(self.data_dir + "invalid_value_constraint.orm")
        model = loader.model

        actual = loader.omissions
        expected = ["Value constraint VC1 because value constraints only support integer ranges"]
        self.assertItemsEqual(actual, expected)

        actual = [cons.name for cons in model.constraints]
        expected = ["VC2"]
        self.assertItemsEqual(actual, expected)

    def test_cardinality_constraints(self):
        """ Test loading of cardinality constraints. """
        loader = NormaLoader(self.data_dir + "test_cardinality_constraint.orm")
        model = loader.model

        cons1 = model.constraints.get("CC1")
        self.assertTrue(cons1.alethic)
        self.assertEquals(cons1.ranges[0].lower, 0)
        self.assertEquals(cons1.ranges[0].upper, 4)
        self.assertItemsEqual(cons1.covers, [model.object_types.get("A")])

        cons2 = model.constraints.get("CC2")
        self.assertTrue(cons2.alethic)
        self.assertEquals(cons2.ranges[0].lower, 2)
        self.assertEquals(cons2.ranges[0].upper, None)
        self.assertItemsEqual(cons2.covers, [model.object_types.get("B")])

        cons3 = model.constraints.get("CC3")
        role = model.fact_types.get("AExists").roles[0]
        self.assertTrue(cons3.alethic)
        self.assertEquals(cons3.ranges[0].lower, 4)
        self.assertEquals(cons3.ranges[0].upper, 7)
        self.assertItemsEqual(cons3.covers, [role])

        cons4 = model.constraints.get("CC4")
        role = model.fact_types.get("BHopes").roles[0]
        self.assertFalse(cons4.alethic)
        self.assertEquals(cons4.ranges[0].lower, 4)
        self.assertEquals(cons4.ranges[0].upper, 4)
        self.assertItemsEqual(cons4.covers, [role]) 

        cons5 = model.constraints.get("CC5")
        role = model.fact_types.get("BDances").roles[0]
        self.assertTrue(cons5.alethic)
        self.assertEquals(len(cons5.ranges), 4)

        self.assertEquals(cons5.ranges[0].lower, 0)
        self.assertEquals(cons5.ranges[0].upper, 2)
        self.assertEquals(cons5.ranges[1].lower, 5)
        self.assertEquals(cons5.ranges[1].upper, 5)
        self.assertEquals(cons5.ranges[2].lower, 8)
        self.assertEquals(cons5.ranges[2].upper, 10) 
        self.assertEquals(cons5.ranges[3].lower, 12)
        self.assertEquals(cons5.ranges[3].upper, None) 
      
        self.assertItemsEqual(cons5.covers, [role]) 

    def test_bad_cardinality_constraint_1(self):
        """ Test loading of file with two cardinality constraints in one node. """

        with self.assertRaises(ValueError) as ex:
            NormaLoader(self.data_dir + "bad_cardinality_constraint_1.orm")

        self.assertEquals(ex.exception.message,
            "CardinalityRestriction should have only 1 child node")

    def test_bad_cardinality_constraint_2(self):
        """ Test loading of file with badly named cardinality constraint node. """

        loader = NormaLoader(self.data_dir + "bad_cardinality_constraint_2.orm")
        model = loader.model
        self.assertEquals(model.constraints.count(), 0)

    def test_bad_cardinality_constraint_3(self):
        """ Test loading of file with badly named ranges node. """

        loader = NormaLoader(self.data_dir + "bad_cardinality_constraint_3.orm")
        model = loader.model
        cons = model.constraints.get("C1")
        self.assertEquals(cons.ranges, [])

class TestSubtypes(TestCase):
    """ Unit tests for the NormaLoader class regarding subtypes. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir() + os.sep
        self.maxDiff = None
        self.basic_model = NormaLoader(self.data_dir + "subtypes.orm").model

    def test_load_basic_subtypes(self):
        """ Test that basic subtype graphs are properly loaded. """
        model = self.basic_model
    
        # Primitive value and entity types that belong to no subtype graph
        v1 = model.object_types.get("V1")
        self.assertTrue(v1.primitive)
        self.assertEquals(v1.root_type, v1)
        self.assertItemsEqual(v1.direct_supertypes, [])
        self.assertItemsEqual(v1.indirect_supertypes, [])
        self.assertItemsEqual(v1.direct_subtypes, [])

        e1 = model.object_types.get("E1")
        self.assertTrue(e1.primitive)
        self.assertEquals(e1.root_type, e1)
        self.assertItemsEqual(e1.direct_supertypes, [])
        self.assertItemsEqual(e1.indirect_supertypes, [])
        self.assertItemsEqual(e1.direct_subtypes, [])

        # Simple linear subtype graph
        a = model.object_types.get("A")
        b = model.object_types.get("B")
        c = model.object_types.get("C")
        self.assertTrue(a.primitive)
        self.assertEquals(a.root_type, a)
        self.assertItemsEqual(a.direct_supertypes, [])
        self.assertItemsEqual(a.indirect_supertypes, [])
        self.assertItemsEqual(a.direct_subtypes, [b])

        self.assertFalse(b.primitive)
        self.assertEquals(b.root_type, a)
        self.assertItemsEqual(b.direct_supertypes, [a])
        self.assertItemsEqual(b.indirect_supertypes, [])
        self.assertItemsEqual(b.direct_subtypes, [c])

        self.assertFalse(c.primitive)
        self.assertEquals(c.root_type, a)
        self.assertItemsEqual(c.direct_supertypes, [b])
        self.assertItemsEqual(c.indirect_supertypes, [a])
        self.assertItemsEqual(c.direct_subtypes, []) 

    def test_diamond_subtype_graphs(self):
        """ Test that diamond-shaped graph is properly loaded. """
        model = self.basic_model

        # Diamond-shaped subtype graph
        w = model.object_types.get("W")
        x = model.object_types.get("X")
        y = model.object_types.get("Y")
        z = model.object_types.get("Z")
        x1 = model.object_types.get("X1")
        y1 = model.object_types.get("Y1")
        z1 = model.object_types.get("Z1")

        self.assertTrue(w.primitive)
        self.assertEquals(w.root_type, w)
        self.assertItemsEqual(w.direct_supertypes, [])
        self.assertItemsEqual(w.indirect_supertypes, [])
        self.assertItemsEqual(w.direct_subtypes, [x, y])

        self.assertFalse(x.primitive)
        self.assertEquals(x.root_type, w)
        self.assertItemsEqual(x.direct_supertypes, [w])
        self.assertItemsEqual(x.indirect_supertypes, [])
        self.assertItemsEqual(x.direct_subtypes, [x1, z])

        self.assertFalse(x1.primitive)
        self.assertEquals(x1.root_type, w)
        self.assertItemsEqual(x1.direct_supertypes, [x])
        self.assertItemsEqual(x1.indirect_supertypes, [w])
        self.assertItemsEqual(x1.direct_subtypes, [])

        self.assertFalse(z.primitive)
        self.assertEquals(z.root_type, w)
        self.assertItemsEqual(z.direct_supertypes, [x, y])
        self.assertItemsEqual(z.indirect_supertypes, [w])
        self.assertItemsEqual(z.direct_subtypes, [z1])

        self.assertFalse(y1.primitive)
        self.assertEquals(y1.root_type, w)
        self.assertItemsEqual(y1.direct_supertypes, [y])
        self.assertItemsEqual(y1.indirect_supertypes, [w])
        self.assertItemsEqual(y1.direct_subtypes, [z1])

        self.assertFalse(z1.primitive)
        self.assertEquals(z1.root_type, w)
        self.assertItemsEqual(z1.direct_supertypes, [z, y1])
        self.assertItemsEqual(z1.indirect_supertypes, [x, y, w])
        self.assertItemsEqual(z1.direct_subtypes, [])

    def test_subtype_graph_mult_root(self):
        """ Test subtype graph with multiple root types. """
        with self.assertRaises(ValueError) as ex:
            model = NormaLoader(self.data_dir + \
                                "subtype_graph_with_multiple_roots.orm").model
        self.assertEquals(ex.exception.message, \
           "Subtype graph containing ObjectTypes.F has more than one root type")

        
            

    
        


        
        
 
        
