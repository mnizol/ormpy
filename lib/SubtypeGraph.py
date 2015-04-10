##############################################################################
# Package: ormpy
# File:    SubtypeGraph.py
# Author:  Matthew Nizol
##############################################################################

""" SubtypeGraph.py provides a class that generates the (possibly disjoint) 
    subtype graph of an ORM model.
"""

class SubtypeGraph(object):
    """ Subtype graph of an ORM model. 

        .. warning:: If the subtype constraints in the associated model change
           after the creation of the SubtypeGraph, the SubtypeGraph *will not*
           automatically update and thus will reflect incorrect information. """

    def __init__(self, model, *args, **kwargs):
        super(SubtypeGraph, self).__init__(*args, **kwargs)

        primitive = lambda x: x.primitive

        #: List of subtype graph roots (i.e. primitive object types)
        self.roots = filter(primitive, model.object_types)

        self.root_of = {}       #: Dictionary from object type to its root
        self.supertypes_of = {} #: Dictionary from object type to the set of
                                #: its direct and indirect supertypes.

        # Populate self.root_of and self.supertypes_of.  Raise a ValueError if
        # an object type has  more than one root (which is illegal in ORM), but
        # don't bother checking for cycles (they aren't permitted by NORMA).
        for root in self.roots:
            self.supertypes_of[root] = set([])
            self.root_of[root] = root

            for child in root.direct_subtypes:
                self._populate_supertypes_dict(child, root, root)

    def _populate_supertypes_dict(self, this, parent, root):
        """ Populate self.root_of and self.supertypes_of for this subtype and
            recursively for each of its subtypes.  """

        if self.root_of.get(this) != None and self.root_of.get(this) != root:
            msg = "Subtype graph containing {0} has more than one root type"
            raise ValueError(msg.format(this.fullname))

        self.root_of[this] = root

        # Update the known supertypes of this node with those of its parent
        known = self.supertypes_of.get(this, set(this.direct_supertypes))
        self.supertypes_of[this] = known | self.supertypes_of[parent]

        for child in this.direct_subtypes:
            self._populate_supertypes_dict(child, this, root)

    def compatible(self, first, second):
        """ Returns true iff first == second, first is a supertype of second,
            or second is a supertype of first."""
        return (first == second) or \
               (first in self.supertypes_of[second]) or \
               (second in self.supertypes_of[first])           

