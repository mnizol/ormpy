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
        cons1 = model.constraints.get("VC_A")
        
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
                   ["INFO: Ignored " + expected[0]]

        self.assertItemsEqual(self.log.formatLogRecords(), expected)

        self.log.afterTest(None)

    def test_constraints_omitted(self):
        """ Confirm omitted constraints get saved to omissions list."""
        self.log.beforeTest(None)
        loader = NormaLoader(self.data_dir + "omitted_constraints.orm")

        expected = [
             "Exclusion constraint ExclusionConstraint1",
             "Exclusion constraint ExclusiveOrConstraint1",
             "Ring constraint RingConstraint1",
             "Value comparison constraint ValueComparisonConstraint1"]

        # Check omissions array
        self.assertItemsEqual(loader.omissions, expected)

        # Check log contents
        expected = ["WARNING: 4 model elements were ignored while loading omitted_constraints.orm."] + \
                   ["INFO: Ignored " + msg for msg in expected]

        self.assertItemsEqual(self.log.formatLogRecords(), expected)

        self.log.afterTest(None)

    def test_subset_constraint(self):
        """ Confirm subset constraints load correctly. """
        fname = TestDataLocator.path("subset_constraint.orm")
        loader = NormaLoader(fname, deontic=True)
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
        self.assertEquals(len(cons3.superset), 3)
        self.assertEquals(len(cons3.subset), 3)
        self.assertIs(cons3.subset[0].fact_type, aplus)
        self.assertIs(cons3.superset[2].fact_type, aand)
        self.assertIs(cons3.subset[2].player, cons3.subset[2].player)

        self.assertItemsEqual(loader.omissions, [])

    def test_partial_subset(self):
        """ Confirm exception fires for invalid subset constraints. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "partial_subset.orm")
        self.assertEquals(ex.exception.message, 
            "Subset constraint SubsetConstraint1 does not have exactly two role sequences")

    def test_implicit_role(self):
        """ Confirm constraint that covers implicit role is removed. """
        model = NormaLoader(self.data_dir + "test_implicit_roles.orm").model
        self.assertIsNone(model.constraints.get("SubsetConstraint1"))

    def test_deprecated_join(self):
        """ Confirm exception fires for models containing deprecated join constraint. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "deprecated_join.orm")
        self.assertEquals(ex.exception.message, 
            "Subset constraint SubsetConstraint1 has deprecated join rule.")

    def test_join_subset_omission(self):
        """ Confirm that join subset constraints are (for now) omitted. """
        loader = NormaLoader(self.data_dir + "join_subset_omission.orm")
        self.assertItemsEqual(loader.omissions, 
            ["Subset constraint SubsetConstraint1 because its join path does not have exactly one JoinPath node."])

        cons = loader.model.constraints.get("SubsetConstraint1")
        self.assertIsNone(cons)

    def test_uniqueness_constraint(self):
        """ Confirm uniqueness constraints load properly. """
        fname = TestDataLocator.path("uniqueness_constraints.orm")
        model = NormaLoader(fname, deontic=True).model

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
        self.assertEquals(ex.exception.message, "Uniqueness constraint " +
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
        self.assertEquals(model.constraints.count(), 9)

        # Check loaded mandatories
        cons = model.constraints.of_type(Constraint.MandatoryConstraint)
        self.assertEquals(len(cons), 3)
        
        s1 = model.constraints.get("SimpleMandatoryConstraint1")
        s2 = model.constraints.get("SimpleMandatoryConstraint2")
        i1 = model.constraints.get("InclusiveOrConstraint1")

        fact_type1 = model.fact_types.get("EHasEId")
        self.assertTrue(s1.simple)
        self.assertEquals(len(s1.covers), 1)
        self.assertIs(s1.covers[0], fact_type1.roles[0])
        self.assertTrue(fact_type1.roles[0].mandatory)
        self.assertFalse(fact_type1.roles[1].mandatory)

        fact_type2 = model.fact_types.get("EHasB")
        self.assertTrue(s2.simple)
        self.assertEquals(len(s2.covers), 1)
        self.assertIs(s2.covers[0], fact_type2.roles[0])
        self.assertTrue(fact_type2.roles[0].mandatory)
        self.assertFalse(fact_type2.roles[1].mandatory)

        role1 = model.fact_types.get("EHasB").roles[1]
        role2 = model.fact_types.get("BIsCool").roles[0]
        self.assertFalse(i1.simple)
        self.assertEquals(len(i1.covers), 2)
        self.assertItemsEqual(i1.covers, [role1, role2])
        
        # For inclusive-or, neither covered role should have "mandatory" true
        self.assertFalse(role1.mandatory)
        self.assertFalse(role2.mandatory)
        
        # Confirm nothing ignored
        self.assertItemsEqual(loader.omissions, [])
      

    def test_role_names(self):
        """ Confirm role names are generated properly. """
        model = NormaLoader(self.data_dir + "role_names.orm").model

        ahasb = model.fact_types.get("AHasB")
        self.assertEquals(ahasb.roles[0].name, "A")
        self.assertEquals(ahasb.roles[1].name, "B")

        alikesb = model.fact_types.get("ALikesB")
        self.assertEquals(alikesb.roles[0].name, "A")
        self.assertEquals(alikesb.roles[1].name, "Likee")

        tern = model.fact_types.get("AAndALikeB")
        self.assertEquals(tern.roles[0].name, "R2")
        self.assertEquals(tern.roles[1].name, "A")
        self.assertEquals(tern.roles[2].name, "B")
        
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
        fname = TestDataLocator.path("test_cardinality_constraint.orm")
        loader = NormaLoader(fname, deontic=True)
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
            "Unexpected cardinality constraint format")

    def test_bad_cardinality_constraint_2(self):
        """ Test loading of file with badly named cardinality constraint node. """

        loader = NormaLoader(self.data_dir + "bad_cardinality_constraint_2.orm")
        self.assertItemsEqual(loader.unexpected, ["BadCardinalityConstraint"])

    def test_bad_cardinality_constraint_3(self):
        """ Test loading of file with badly named ranges node. """

        loader = NormaLoader(self.data_dir + "bad_cardinality_constraint_3.orm")
        model = loader.model
        cons = model.constraints.get("C1")
        self.assertEquals(cons.ranges, [])

    def test_bad_value_constraint(self):
        """ Test loading of file with badly named value constraint node. """
        
        loader = NormaLoader(self.data_dir + "bad_value_constraint.orm")
        self.assertItemsEqual(loader.unexpected, ["BadValueConstraint"])

    def test_card_and_value_constraint_on_implicit_type(self):
        """ Confirm that cardinality and value constraints on implicit types
            are ignored. This model contains one of each on an implicit 
            boolean object type. """
        loader = NormaLoader(self.data_dir + "constraint_on_implicit_type.orm")
        model = loader.model
        self.assertEquals(model.constraints.count(), 1)
        self.assertIsNotNone(model.constraints.get("IUC1"))

    def test_unexpected_constraint_node(self):
        """ Confirm the loader catches an unexpected constraint node. """
        self.log.beforeTest(None)

        loader = NormaLoader(self.data_dir + "unexpected_constraint_node.orm")
        self.assertItemsEqual(loader.unexpected, ["NewConstraint"])

        # Check log contents
        expected = ["WARNING: 1 XML node was unexpected while loading unexpected_constraint_node.orm."] + \
                   ["INFO: Unexpected NewConstraint"]

        self.assertItemsEqual(self.log.formatLogRecords(), expected)

        self.log.afterTest(None)

    def test_constraint_covers_both_implied_and_explicit_role(self):
        """ Test a constraint that covers both an implied and an explicit  
            role, which is a VERY UNLIKELY scenario. """
        loader = NormaLoader(self.data_dir + \
            "constraint_covers_both_implied_and_regular_roles.orm.orm")
        model = loader.model

        expected = ["Uniqueness constraint EUC1 because it covers implied and explicit roles"]

        self.assertIsNone(model.constraints.get("EUC1"))
        self.assertEquals(model.constraints.count(), 2)
        self.assertItemsEqual(loader.omissions, expected) 

    def test_deontic_constraints(self):
        """ Test that deontic constraints are correctly ignored. """
        fname = TestDataLocator.path("deontic_constraints.orm")
        loader = NormaLoader(fname, deontic=False)
        model = loader.model

        self.assertEquals(model.constraints.count(), 2)
        self.assertIsNotNone(model.constraints.get("IUC1"))
        self.assertIsNotNone(model.constraints.get("IUC_unary"))
        self.assertEquals(loader.omissions, [])

        loader = NormaLoader(fname, deontic=True)
        model = loader.model

        self.assertEquals(model.constraints.count(), 3)
        self.assertIsNotNone(model.constraints.get("IUC2d"))
        self.assertItemsEqual(loader.omissions, ["Exclusion constraint EXC1"])

    def test_deontic_cardinality(self):
        """ Test that deontic modality is recognized for cardinality constraints."""
        fname = TestDataLocator.path("deontic_cardinality.orm")
        loader = NormaLoader(fname, deontic=False)
        model = loader.model

        # Only the unary IUC should not be ignored
        self.assertEquals(model.constraints.count(), 1)
        self.assertIsNotNone(model.constraints.get("IUC_unary"))

    def test_join_rule_with_no_join_path(self):
        """ Test <JoinRule> not followed by a <JoinPath>. """
        fname = TestDataLocator.path("join_rule_no_join_path.orm")
        loader = NormaLoader(fname)
        model = loader.model
    
        cons = model.constraints.get("ExternalUniquenessConstraint1") 
        self.assertIsNone(cons)

        expected = "Uniqueness constraint ExternalUniquenessConstraint1 because its join path does not have exactly one JoinPath node."
        self.assertEquals(loader.omissions, [expected])

    def test_join_rule_with_subquery(self):
        """ Test <JoinRule> that contains a <SubQueries> node. """
        fname = TestDataLocator.path("join_rule_with_subquery.orm")
        loader = NormaLoader(fname)
        model = loader.model
    
        cons = model.constraints.get("FC1_with_subquery") 
        self.assertIsNone(cons)

        expected = "Frequency constraint FC1_with_subquery because its join path has a JoinPath node with an unsupported child node: Subqueries."
        self.assertEquals(loader.omissions, [expected])

    def test_join_rule_with_no_role_path(self):
        """ Test <JoinRule> that contains no <RolePath> node. """
        fname = TestDataLocator.path("join_rule_no_role_path.orm")
        loader = NormaLoader(fname)
        model = loader.model
    
        cons = model.constraints.get("FrequencyConstraint1") 
        self.assertIsNone(cons)

        expected = "Frequency constraint FrequencyConstraint1 because its join path does not have exactly one RolePath node."
        self.assertEquals(loader.omissions, [expected])

    def test_join_rule_with_unsupported_splits(self):
        """ Test <JoinRule> that contains negated split paths and combination
            operators other than AND. """
        fname = TestDataLocator.path("join_rule_negated_split.orm")
        loader = NormaLoader(fname)
        model = loader.model
    
        cons_neg = model.constraints.get("EUC_negated") 
        cons_or  = model.constraints.get("EUC_or")

        self.assertIsNone(cons_neg)
        self.assertIsNone(cons_or)

        expected = ["Uniqueness constraint EUC_negated because its join path has a negated path split.",
                    "Uniqueness constraint EUC_or because its join path combines paths with an operator other than AND."]
        self.assertEquals(loader.omissions, expected)

    def test_subpath_with_bad_child_node(self):
        """ Test <SubPath> node with bad child node. Specifically, this test
            case has a nested <SubPaths> node under a <SubPath>, which we do 
            not support. """
        fname = TestDataLocator.path("bad_subpath_child_node.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("EUC1")
        self.assertIsNone(cons)

        expected = ["Uniqueness constraint EUC1 because its join path has a SubPaths node with an unsupported child node: BadSubPath."]
        self.assertEquals(loader.omissions, expected)

    def test_pathed_roles_with_bad_child_node(self):
        """ Test <PathedRoles> node with bad child node. """
        fname = TestDataLocator.path("join_rule_pathed_roles_bad_child.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")
        self.assertIsNone(cons)

        expected = ["Frequency constraint FrequencyConstraint1 because its join path has a PathedRoles node with an unsupported child node: PathedRole2."]
        self.assertEquals(loader.omissions, expected)

    def test_join_rule_covering_implicit_roles(self):
        """ Test <PathedRoles> node that include implicit roles. """
        fname = TestDataLocator.path("join_rule_covering_implicit_roles.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("EUC1")
        self.assertIsNone(cons) # Not loaded because it covers implicit roles

        expected = ["Uniqueness constraint EUC1 because its join path includes an implicit role."]
        self.assertEquals(loader.omissions, expected)

    def test_pathed_role_with_value_restriction_child_node(self):
        """ Test <PathedRole> node with bad child node. """
        fname = TestDataLocator.path("join_rule_pathed_role_with_value_restriction.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")
        self.assertIsNone(cons)

        expected = ["Frequency constraint FrequencyConstraint1 because its join path has a PathedRole node with an unsupported child node: ValueRestriction."]
        self.assertEquals(loader.omissions, expected)

    def test_pathed_role_with_outer_join(self):
        """ Test <PathedRole> node with outer join. """
        fname = TestDataLocator.path("join_rule_pathed_role_with_outer_join.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")
        self.assertIsNone(cons)

        expected = ["Frequency constraint FrequencyConstraint1 because its join path includes an outer join."]
        self.assertEquals(loader.omissions, expected)

    def test_pathed_role_with_negated_join(self):
        """ Test <PathedRole> node with negated join. """
        fname = TestDataLocator.path("join_rule_pathed_role_with_negated_join.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")
        self.assertIsNone(cons)

        expected = ["Frequency constraint FrequencyConstraint1 because its join path includes a negated role."]
        self.assertEquals(loader.omissions, expected)

    def test_valid_linear_join_path(self):
        """ Test valid linear join path. """
        fname = TestDataLocator.path("join_rule_valid_linear_path.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")

        self.assertIsNotNone(cons)
        self.assertIsNotNone(cons.covers.join_path)
        self.assertEquals(loader.omissions, [])

        path = cons.covers.join_path
        f1 = model.fact_types.get("AHasB")
        f2 = model.fact_types.get("BHasC")
        f3 = model.fact_types.get("CHasD")

        self.assertEquals(path.fact_types, [f1, f2, f3])
        self.assertEquals(path.joins, [ (f1.roles[1], f2.roles[0]),
                                        (f2.roles[1], f3.roles[0]) ])

    def test_role_path_unexpected_child(self):
        """ Test <RolePath> node with unexpected child node. """
        fname = TestDataLocator.path("join_rule_with_subquery_parameter_inputs.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("FrequencyConstraint1")
        self.assertIsNone(cons)

        expected = ["Frequency constraint FrequencyConstraint1 because its join path has " \
            "a RolePath node with an unsupported child node: SubqueryParameterInputs."]
        self.assertEquals(loader.omissions, expected)

    def test_valid_branching_join_path(self):
        """ Test valid branching join path. """
        fname = TestDataLocator.path("join_rule_valid_branching_path.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("EUC1")

        self.assertIsNotNone(cons)
        self.assertIsNotNone(cons.covers.join_path)
        self.assertEquals(loader.omissions, [])

        path = cons.covers.join_path
        f1 = model.fact_types.get("AHasD")
        f2 = model.fact_types.get("BHasC")
        f3 = model.fact_types.get("CHasD")
        f4 = model.fact_types.get("EHasD")

        self.assertEquals(path.fact_types, [f1, f3, f2, f4])
        self.assertEquals(path.joins, [ (f1.roles[1], f3.roles[1]),
                                        (f3.roles[0], f2.roles[1]),
                                        (f1.roles[1], f4.roles[1]) ])

    def test_valid_complex_branching_join_path(self):
        """ Test valid complex branching join path. """
        fname = TestDataLocator.path("join_rule_valid_complex_branching_path.orm")
        loader = NormaLoader(fname)
        model = loader.model

        cons = model.constraints.get("EUC1")

        self.assertIsNotNone(cons)
        self.assertIsNotNone(cons.covers.join_path)
        self.assertEquals(loader.omissions, [])

        path = cons.covers.join_path
        DHasE = model.fact_types.get("DHasE")
        EHasB = model.fact_types.get("EHasB")
        BHasC = model.fact_types.get("BHasC")
        FHasG = model.fact_types.get("FHasG")
        GHasB = model.fact_types.get("GHasB")
        HHasG = model.fact_types.get("HHasG")

        self.assertEquals(path.fact_types, [DHasE, EHasB, GHasB, FHasG, HHasG, BHasC])
        self.assertEquals(path.joins, [ (DHasE.roles[1], EHasB.roles[0]),
                                        (EHasB.roles[1], GHasB.roles[1]),
                                        (GHasB.roles[0], FHasG.roles[1]),
                                        (GHasB.roles[0], HHasG.roles[1]),
                                        (EHasB.roles[1], BHasC.roles[0]) ])
         
    def test_load_equality_constraint(self):
        """ Test loading of equality constraint. """
        fname = TestDataLocator.path("equality_four_role.orm")
        loader = NormaLoader(fname)
        model = loader.model       

        self.assertItemsEqual(loader.omissions, [])

        cons_list = model.constraints.of_type(Constraint.EqualityConstraint)

        self.assertEquals(3, len(cons_list))

        eq1 = model.constraints.get("EQ")
        eq2 = model.constraints.get("EQ2")
        eq3 = model.constraints.get("EQ3")

        self.assertTrue(isinstance(eq1, Constraint.EqualityConstraint))
        self.assertTrue(isinstance(eq2, Constraint.EqualityConstraint))
        self.assertTrue(isinstance(eq3, Constraint.EqualityConstraint))

        obj = model.object_types.get("A")

        self.assertEquals(eq1.superset, [obj.roles[0]])
        self.assertEquals(eq1.subset, [obj.roles[1]])
        self.assertEquals(eq1.covers, eq1.subset + eq1.superset)

        self.assertEquals(eq2.superset, [obj.roles[0]])
        self.assertEquals(eq2.subset, [obj.roles[2]])
        self.assertEquals(eq2.covers, eq2.subset + eq2.superset)
        
        self.assertEquals(eq3.superset, [obj.roles[0]])
        self.assertEquals(eq3.subset, [obj.roles[3]])
        self.assertEquals(eq3.covers, eq3.subset + eq3.superset)
