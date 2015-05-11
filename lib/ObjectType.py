##############################################################################
# Package: ormpy
# File:    ObjectType.py
# Author:  Matthew Nizol
##############################################################################

""" ObjectType.py provides classes for the various object types in ORM:
    entity type, value type, and objectified type.
"""

from lib.ModelElement import ModelElementSet, ModelElement
from lib.Domain import StringDomain

class ObjectTypeSet(ModelElementSet):
    """ Container for a set of object types. """

    def __init__(self, name="Object Types", *args, **kwargs):
        super(ObjectTypeSet, self).__init__(name=name, *args, **kwargs)


class ObjectType(ModelElement):
    """ Abstract class inherited by all object types. """

    def __init__(self, independent=False, data_type=None, *args, **kwargs):
        super(ObjectType, self).__init__(*args, **kwargs)

        self.independent = independent #: True for independent object types
        self.implicit = False    #: True for implicit object types
        self.roles = [] #: Roles played by this object type
        self.covered_by = [] #: Constraints that cover this object type

        #: A list of the entity type's reference roles, which must be a subset
        #: of self.roles.  This attribute is set by the identifying constraint
        #: when that constraint is committed.  The list should always be empty
        #: for value types.
        self.ref_roles = []

        # Direct subtypes and supertypes.  We do not store indirect subtypes
        # here because maintenance of the subtype graph would be too expensive
        self.direct_subtypes = [] #: Direct subtypes of this object type
        self.direct_supertypes = [] #: Direct supertypes of this object type

        # Prefix for domain values     
        prefix = self.name or '' # Empty string if name is None
        if prefix and prefix[-1].isdigit(): 
            prefix += "_"        
        
        # Raw conceptual data type, ignoring any value constraints
        self._data_type = data_type or StringDomain(prefix=prefix) 

        #: The domain from which objects for this type should be drawn. Defaults
        #: to self.data_type but may be overridden by a value constraint.
        self.domain = self._data_type

    @property
    def primitive(self):
        """ True iff object type has no supertype. """
        return len(self.direct_supertypes) == 0

    @property
    def data_type(self):
        """ The raw conceptual data type for the object type, which defaults to 
            a :class:`lib.Domain.StringDomain` prefixed by the type's name. """
        return self._data_type

    @property
    def fullname(self):
        """ Returns name that is unique within the model. """
        return "ObjectTypes." + self.name

    @property
    def non_ref_roles(self):
        """ Set of non-reference roles played by the object type. """
        return set(self.roles) - set(self.ref_roles)

    @property
    def subject_to_idmc(self):
        """ True iff object type is subject to the implicit disjunctive 
            mandatory constraint. """
        return self.primitive and not self.independent and self.non_ref_roles

    def commit(self):
        """ Commit any side effects of adding this object type to a model."""
        pass # No side effects generated when creating an ObjectType

    def rollback(self):
        """ Rollback any side effects of adding this object type to a model."""
        # I don't see a need yet to rollback an ObjectType.  Moreover, it's not
        # clear to me what the right behavior would be: should I also rollback
        # all roles/fact types/constraints/subtypes associated with this type?
        raise NotImplementedError()

class EntityType(ObjectType):
    """ An entity type is an object type that requires identification. """

    def __init__(self, identifying_constraint=None, *args, **kwargs):
        super(EntityType, self).__init__(*args, **kwargs)

        #: Reference to the (internal or external) uniqueness constraint that 
        #: provides the preferred identification scheme for this entity type.
        self.identifying_constraint = identifying_constraint
   
class ValueType(ObjectType):
    """ A value type is a self-identifying object type. """

    def __init__(self, *args, **kwargs):
        super(ValueType, self).__init__(*args, **kwargs)

class ObjectifiedType(EntityType):
    """ An objectified type is an entity type that objectifies a fact type. """

    def __init__(self, nested_fact_type=None, *args, **kwargs):
        super(ObjectifiedType, self).__init__(*args, **kwargs)

        #: Reference to the fact type that this object type objectifies.
        self.nested_fact_type = nested_fact_type
