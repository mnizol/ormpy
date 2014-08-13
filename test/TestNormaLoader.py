##############################################################################
# Package: ormpy
# File:    TestNormaLoader.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.NormaLoader class """

import os
from unittest import TestCase
from datetime import datetime, date, time

from lib.NormaLoader import NormaLoader
from lib.ModelElement import ModelElement
from lib.FactType import FactType

import lib.ObjectType as ObjectType
import lib.Constraint as Constraint

class TestNormaLoader(TestCase):
    """ Unit tests for the NormaLoader class. """

    def setUp(self):
        self.data_dir = os.getenv("ORMPY_TEST_DATA_DIR")

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
        self.assertIs(cons1.covers[0], cons1.subtype)
        self.assertTrue(cons1.preferred_id)

        self.assertFalse(model.constraints.get("BIsASubtypeOfC").preferred_id)        

    def test_subtype_exception(self):
        """ Confirm subtype exception fires for corrupted data. """
        with self.assertRaises(Exception) as ex:
            loader = NormaLoader(self.data_dir + "corrupted_subtype.orm")
        self.assertEquals(ex.exception.message, 
            "Cannot load subtype constraint.")
        
    def test_load_object_types(self):
        """ Test of object type load. """
        loader = NormaLoader(self.data_dir + "object_type_tests.orm")
        model = loader.model

        # No derivation rules
        self.assertItemsEqual(loader.omissions, [])
        
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
        self.assertFalse(this.independent)
        self.assertEquals(this.identifying_constraint, 
            model.constraints.get("InternalUniquenessConstraint14"))
        self.assertEquals(this.nested_fact_type, 
            "_B6D10F36-FFE2-4B86-BEA4-02F7FCA655F9")

        # Implicit Objectified (Created by ternary, should not load)
        this = model.object_types.get("V1HasDHasV2") 
        self.assertIsNone(this)

    def test_data_type_load(self):
        """ Confirm data types are loaded properly for Value Types. """
        model = NormaLoader(self.data_dir + "data_types.orm").model
        ot = model.object_types

        self.assertIsInstance(ot.get("A").data_type, int) # data type undefined
        self.assertIsInstance(ot.get("B").data_type, bool)      # True or false
        self.assertIsInstance(ot.get("C").data_type, bool)      # Yes or no
        self.assertIsInstance(ot.get("D").data_type, int)       # auto counter
        self.assertIsInstance(ot.get("E").data_type, float)     # float
        self.assertIsInstance(ot.get("F").data_type, float)     # money
        self.assertIsInstance(ot.get("G").data_type, int)       # big int
        self.assertIsInstance(ot.get("H").data_type, datetime)  # timestamp
        self.assertIsInstance(ot.get("I").data_type, date)      # date
        self.assertIsInstance(ot.get("J").data_type, time)      # time
        self.assertIsInstance(ot.get("K").data_type, str)       # text

        # Confirm scale and length are read
        special = ot.get("Special")
        self.assertIsInstance(special.data_type, float)  # float
        self.assertEquals(special.data_type_scale, "35")
        self.assertEquals(special.data_type_length, "29")

    def test_unknown_data_type(self):
        """ Confirm that data type defaults to int() if the actual type 
            is unexpected. """
        model = NormaLoader(self.data_dir + "unknown_data_types.orm").model
        self.assertIsInstance(model.object_types.get("A").data_type, int)
        self.assertIsInstance(model.object_types.get("B").data_type, int)

    def test_value_constraint_on_types(self):
        """ Confirm that value constraints on value types are loaded. """
        model = NormaLoader(
            self.data_dir + "test_value_type_value_constraint.orm").model
        cons1 = model.constraints.get("ValueConstraint1")
        
        self.assertEquals(cons1.uid, "_9F61B75E-FB59-456F-97A9-E4CF104FABE5")
        self.assertIs(cons1.covers[0], model.object_types.get("A"))

        self.assertEquals(cons1.ranges[0].min_value, "1")
        self.assertEquals(cons1.ranges[0].max_value, "2")
        self.assertFalse(cons1.ranges[0].min_open)
        self.assertFalse(cons1.ranges[0].max_open)

        self.assertEquals(cons1.ranges[1].min_value, "5")
        self.assertEquals(cons1.ranges[1].max_value, "6")
        self.assertTrue(cons1.ranges[1].min_open)
        self.assertFalse(cons1.ranges[1].max_open) 

        self.assertEquals(cons1.ranges[2].min_value, "10")
        self.assertEquals(cons1.ranges[2].max_value, "20")
        self.assertFalse(cons1.ranges[2].min_open)
        self.assertTrue(cons1.ranges[2].max_open)  

        self.assertEquals(cons1.ranges[3].min_value, "100")
        self.assertEquals(cons1.ranges[3].max_value, "200")
        self.assertTrue(cons1.ranges[3].min_open)
        self.assertTrue(cons1.ranges[3].max_open) 

    def test_load_fact_types(self):
        """ Confirm fact types load successfully. """
        loader = NormaLoader(self.data_dir + "fact_type_tests.orm")
        model = loader.model

        # Confirm reference scheme fact type loads
        ftype1 = model.fact_types.get("AHasA_id")
        self.assertEquals(ftype1.uid, "_8C96FD40-5E82-4E8F-B5EE-C6CEE8BCF74B")
        self.assertIsInstance(ftype1, FactType)  

        # Confirm derivation rule added to omissions
        self.assertItemsEqual(loader.omissions, 
            ["Fact type derivation rule for AHasB",
             "Fact type derivation rule for AHasA_id"])

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

        self.assertEquals(cons1.ranges[0].min_value, "A")
        self.assertEquals(cons1.ranges[0].max_value, "B")
        self.assertFalse(cons1.ranges[0].min_open)
        self.assertFalse(cons1.ranges[0].max_open)

        self.assertEquals(cons1.ranges[1].min_value, "C")
        self.assertEquals(cons1.ranges[1].max_value, "E")
        self.assertTrue(cons1.ranges[1].min_open)
        self.assertFalse(cons1.ranges[1].max_open) 

        self.assertEquals(cons1.ranges[2].min_value, "F")
        self.assertEquals(cons1.ranges[2].max_value, "G")
        self.assertFalse(cons1.ranges[2].min_open)
        self.assertTrue(cons1.ranges[2].max_open) 

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
        loader = NormaLoader(self.data_dir + "derivation_source.orm")
        self.assertItemsEqual(loader.omissions,
            ["Role derivation rule within AHasB"])

    def test_constraints_omitted(self):
        """ Confirm omitted constraints get saved to omissions list."""
        loader = NormaLoader(self.data_dir + "omitted_constraints.orm")
        self.assertItemsEqual(loader.omissions,
            ["Equality constraint EqualityConstraint1",
             "Exclusion constraint ExclusionConstraint1",
             "Exclusion constraint ExclusiveOrConstraint1",
             "Inclusive-or constraint InclusiveOrConstraint1",
             "Inclusive-or constraint InclusiveOrConstraint2",
             "Ring constraint RingConstraint1",
             "Value comparison constraint ValueComparisonConstraint1"])

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
        






 

        

    
        


        
        
 
        
