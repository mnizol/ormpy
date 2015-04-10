##############################################################################
# Package: ormpy
# File:    TestSubtypeGraph.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the SubtypeGraph module """

from unittest import TestCase
import os

from lib.NormaLoader import NormaLoader
from lib.SubtypeGraph import SubtypeGraph
import lib.TestDataLocator as TestData

class TestSubtypeGraph(TestCase):
    """ Unit tests for the SubtypeGraph module. """

    def setUp(self):
        self.basic_model = NormaLoader(TestData.path("subtypes.orm")).model

    def test_compatible_object_types(self):
        """ Test compatible() function. """
        model = self.basic_model
        graph = SubtypeGraph(model)

        w = model.object_types.get("W")
        x = model.object_types.get("X")
        y = model.object_types.get("Y")
        z = model.object_types.get("Z")
        x1 = model.object_types.get("X1")
        y1 = model.object_types.get("Y1")
        z1 = model.object_types.get("Z1")
        e1 = model.object_types.get("E1")

        self.assertTrue(graph.compatible(z, z))
        self.assertTrue(graph.compatible(z, x))
        self.assertTrue(graph.compatible(x, z))
        self.assertTrue(graph.compatible(z, w))
        self.assertTrue(graph.compatible(w, z))
        self.assertTrue(graph.compatible(z, z1))
        self.assertTrue(graph.compatible(z1, z))

        self.assertFalse(graph.compatible(z, x1))
        self.assertFalse(graph.compatible(x1, z))

        self.assertFalse(graph.compatible(z, e1))
        self.assertFalse(graph.compatible(e1, z))

        self.assertFalse(graph.compatible(y1, x))
        self.assertFalse(graph.compatible(x, y1))

    def test_subtype_graph_mult_root(self):
        """ Test subtype graph with multiple root types. """
        with self.assertRaises(ValueError) as ex:
            fname = TestData.path("subtype_graph_with_multiple_roots.orm")
            model = NormaLoader(fname).model
            graph = SubtypeGraph(model)

        self.assertEquals(ex.exception.message, \
           "Subtype graph containing ObjectTypes.F has more than one root type")  

    def test_load_basic_subtypes(self):
        """ Test that basic subtype graphs are properly loaded. """
        model = self.basic_model
        graph = SubtypeGraph(model)

        # Primitive value and entity types that belong to no subtype graph
        v1 = model.object_types.get("V1")
        self.assertTrue(v1.primitive)
        self.assertEquals(graph.root_of[v1], v1)
        self.assertItemsEqual(v1.direct_supertypes, [])
        self.assertItemsEqual(graph.supertypes_of[v1], [])
        self.assertItemsEqual(v1.direct_subtypes, [])

        e1 = model.object_types.get("E1")
        self.assertTrue(e1.primitive)
        self.assertEquals(graph.root_of[e1], e1)
        self.assertItemsEqual(e1.direct_supertypes, [])
        self.assertItemsEqual(graph.supertypes_of[e1], [])
        self.assertItemsEqual(e1.direct_subtypes, [])

        # Simple linear subtype graph
        a = model.object_types.get("A")
        b = model.object_types.get("B")
        c = model.object_types.get("C")
        self.assertTrue(a.primitive)
        self.assertEquals(graph.root_of[a], a)
        self.assertItemsEqual(a.direct_supertypes, [])
        self.assertItemsEqual(graph.supertypes_of[a], [])
        self.assertItemsEqual(a.direct_subtypes, [b])

        self.assertFalse(b.primitive)
        self.assertEquals(graph.root_of[b], a)
        self.assertItemsEqual(b.direct_supertypes, [a])
        self.assertItemsEqual(graph.supertypes_of[b], [a])
        self.assertItemsEqual(b.direct_subtypes, [c])

        self.assertFalse(c.primitive)
        self.assertEquals(graph.root_of[c], a)
        self.assertItemsEqual(c.direct_supertypes, [b])
        self.assertItemsEqual(graph.supertypes_of[c], [a,b])
        self.assertItemsEqual(c.direct_subtypes, []) 

    def test_diamond_subtype_graphs(self):
        """ Test that diamond-shaped graph is properly loaded. """
        model = self.basic_model
        graph = SubtypeGraph(model)

        # Diamond-shaped subtype graph
        w = model.object_types.get("W")
        x = model.object_types.get("X")
        y = model.object_types.get("Y")
        z = model.object_types.get("Z")
        x1 = model.object_types.get("X1")
        y1 = model.object_types.get("Y1")
        z1 = model.object_types.get("Z1")

        self.assertTrue(w.primitive)
        self.assertEquals(graph.root_of[w], w)
        self.assertItemsEqual(w.direct_supertypes, [])
        self.assertItemsEqual(graph.supertypes_of[w], [])
        self.assertItemsEqual(w.direct_subtypes, [x, y])

        self.assertFalse(x.primitive)
        self.assertEquals(graph.root_of[x], w)
        self.assertItemsEqual(x.direct_supertypes, [w])
        self.assertItemsEqual(graph.supertypes_of[x], [w])
        self.assertItemsEqual(x.direct_subtypes, [x1, z])

        self.assertFalse(x1.primitive)
        self.assertEquals(graph.root_of[x1], w)
        self.assertItemsEqual(x1.direct_supertypes, [x])
        self.assertItemsEqual(graph.supertypes_of[x1], [x, w])
        self.assertItemsEqual(x1.direct_subtypes, [])

        self.assertFalse(z.primitive)
        self.assertEquals(graph.root_of[z], w)
        self.assertItemsEqual(z.direct_supertypes, [x, y])
        self.assertItemsEqual(graph.supertypes_of[z], [w, x, y])
        self.assertItemsEqual(z.direct_subtypes, [z1])

        self.assertFalse(y1.primitive)
        self.assertEquals(graph.root_of[y1], w)
        self.assertItemsEqual(y1.direct_supertypes, [y])
        self.assertItemsEqual(graph.supertypes_of[y1], [w, y])
        self.assertItemsEqual(y1.direct_subtypes, [z1])

        self.assertFalse(z1.primitive)
        self.assertEquals(graph.root_of[z1], w)
        self.assertItemsEqual(z1.direct_supertypes, [z, y1])
        self.assertItemsEqual(graph.supertypes_of[z1], [x, y, w, z, y1])
        self.assertItemsEqual(z1.direct_subtypes, []) 

