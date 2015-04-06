##############################################################################
# Package: ormpy
# File:    NormaLoader.py
# Author:  Matthew Nizol
##############################################################################

""" Module for importing .orm files produced by the NORMA_ modeling tool,
    which is a plugin for Visual Studio.

    .. _NORMA: http://sourceforge.net/projects/orm

    NormaLoader.py has been tested on the .orm file format that utilizes the
    following namespaces:

    * ormRoot: http://schemas.neumont.edu/ORM/2006-04/ORMRoot
    * orm: http://schemas.neumont.edu/ORM/2006-04/ORMCore

    **Omissions:** NormaLoader intentionally ignores much of the .orm file
    structure when loading the file into a :class:`lib.Model.Model` object
    (much of the .orm file is not relevant to the analyses performed by ORMPY).
    All information outside of the <orm:ORMModel> node is ignored, which
    includes things like diagram (shape) data and extensions.  NormaLoader
    also ignores the following (not necessarily exhaustive) list of items:

    * Sample (instance) data
    * Model elements not explicitly modeled by the modeler (implicit elements)
    * Model errors reported by NORMA
    * Informal model notes
    * Multiple readings for a fact type
    * Derivation rules for subtypes, fact types, and roles
    * Constraints outside the scope of ORM-- or its extensions
    * Culture-invariant form of value constraints

    A list of important model elements (such as derivations
    and constraints) that are ignored by NormaLoader is contained in the
    *omissions* attribute after loading the input file.

    **Data Types:** NormaLoader maps each data type specified in the .orm file
    to a subclass of :class:`lib.Domain.Domain`. NormaLoader ignores the 
    length and scale facets specified in the .orm file.
"""

import xml.etree.cElementTree as xml
import logging
import os
from datetime import datetime, date, time

from lib.Model import Model
import lib.ObjectType as ObjectType
import lib.FactType as FactType
import lib.Constraint as Constraint
import lib.Domain as Domain

# Constants
NS_ROOT = "{http://schemas.neumont.edu/ORM/2006-04/ORMRoot}"
NS_CORE = "{http://schemas.neumont.edu/ORM/2006-04/ORMCore}"

# Mapping from XML types defined in ORMCore namespace to Domains.  The default
# domain, used when the value is None, is a StringDomain whose prefix is the
# object type's name (e.g. values for Person default to Person1, Person2, etc.)
DATA_TYPES = {
    "UnspecifiedDataType"                        : None,
    "FixedLengthTextDataType"                    : None,
    "VariableLengthTextDataType"                 : None,
    "LargeLengthTextDataType"                    : None,
    "SignedIntegerNumericDataType"               : Domain.IntegerDomain,
    "SignedSmallIntegerNumericDataType"          : Domain.IntegerDomain,
    "SignedLargeIntegerNumericDataType"          : Domain.IntegerDomain,
    "UnsignedIntegerNumericDataType"             : Domain.IntegerDomain,
    "UnsignedTinyIntegerNumericDataType"         : Domain.IntegerDomain,
    "UnsignedSmallIntegerNumericDataType"        : Domain.IntegerDomain,
    "UnsignedLargeIntegerNumericDataType"        : Domain.IntegerDomain,
    "AutoCounterNumericDataType"                 : Domain.IntegerDomain,
    "FloatingPointNumericDataType"               : Domain.FloatDomain,
    "SinglePrecisionFloatingPointNumericDataType": Domain.FloatDomain,
    "DoublePrecisionFloatingPointNumericDataType": Domain.FloatDomain,
    "DecimalNumericDataType"                     : Domain.FloatDomain,
    "MoneyNumericDataType"                       : Domain.FloatDomain,
    "FixedLengthRawDataDataType"                 : None,
    "VariableLengthRawDataDataType"              : None,
    "LargeLengthRawDataDataType"                 : None,
    "PictureRawDataDataType"                     : None,
    "OleObjectRawDataDataType"                   : None,
    "AutoTimestampTemporalDataType"              : Domain.DateTimeDomain,
    "TimeTemporalDataType"                       : Domain.TimeDomain,
    "DateTemporalDataType"                       : Domain.DateDomain, 
    "DateAndTimeTemporalDataType"                : Domain.DateTimeDomain,
    "TrueOrFalseLogicalDataType"                 : Domain.BoolDomain,
    "YesOrNoLogicalDataType"                     : Domain.BoolDomain,
    "RowIdOtherDataType"                         : Domain.IntegerDomain,
    "ObjectIdOtherDataType"                      : Domain.IntegerDomain
}

class NormaLoader(object):
    """ Loads an .orm file produced by the NORMA modeling tool into a
        :class:`lib.Model.Model`.  There are no public methods in this class.
        An .orm file can be loaded via the constructor.  For example: ::

            loader = NormaLoader("/path/to/file/example.orm")
            model = loader.model
    """

    ###########################################################################
    # Constructor: Only public method!
    ###########################################################################
    def __init__(self, filename):
        """ Initialize object and load *filename*. """

        #: The ORM model (:class:`lib.Model.Model`) loaded from the .orm file.
        self.model = Model()

        # Items in the .orm file omitted by NormaLoader
        self.omissions = [] #: Intentionally omitted model elements
        self.unexpected = set() #: Unexpected nodes in the XML file

        # Private attributes
        self._elements = {}   # Dictionary of {id, element} pairs

        # Stack of elements to add to model.  Some items are generated (e.g.
        # value constraints) before we are certain that the parent element will
        # be added to the model.  Thus, we add tentative elements to the stack.
        self._element_stack = []

        self._loader = {}

        # Executable part of constructor: build mappings and load file
        self._build_mappings()
        self._load(filename)
        self._log_issues_with(filename)      
        

    ###########################################################################
    # Private Utility Functions
    ###########################################################################
    def _build_mappings(self):
        """ Build mappings used by instances of the class.
        """
        # Mapping from XML node tag to loader functions
        self._loader = {
            'EntityType'            : self._load_entity_type,
            'ValueType'             : self._load_value_type,
            'ObjectifiedType'       : self._load_objectified_type,
            'NestedPredicate'       : self._load_nested_fact_type,
            'SubtypeDerivationRule' : self._load_subtype_derivation,
            'PreferredIdentifier'   : self._load_preferred_identifier,
            'ConceptualDataType'    : self._load_conceptual_data_type,
            'ValueRestriction'      : self._load_child_nodes,
            'ValueConstraint'       : self._load_value_restriction,
            'RoleValueConstraint'   : self._load_value_restriction,
            'Fact'                  : self._load_fact,
            'FactRoles'             : self._load_child_nodes,
            'Role'                  : self._load_role,
            'RolePlayer'            : self._load_role_player,
            'DerivationRule'        : self._load_facttype_derivation,
            'DerivationSource'      : self._load_role_derivation,
            'SubtypeFact'           : self._load_subtype_fact,
            'CardinalityRestriction': self._load_cardinality_constraint
        }

    def _add(self, model_element):
        """ Add model element to the model. """
        self._elements[model_element.uid] = model_element 

        # Add to model, unless it is a role (which is added as part of its
        # containing fact type).
        if not isinstance(model_element, FactType.Role):       
            self.model.add(model_element)

    def _push(self, element):
        """ Push an item to the element stack. """
        self._element_stack.append(element)

    def _pop(self):
        """ Pop an item from the element stack. """
        return self._element_stack.pop()

    def _add_from_stack(self, condition=True, guard=None):
        """ If condition is True, add items in the stack to the
            model until we reach the guard item. """
        while len(self._element_stack) > 0:
            item = self._pop()
            if condition:
                self._add(item)
            if item == guard:
                break

    @staticmethod
    def _construct(xml_node, model_element_type):
        """ Construct a new model element from the XML node. """
        uid = xml_node.get("id")
        name = xml_node.get("Name")

        if name is None: # Some nodes use "_Name" instead
            name = xml_node.get("_Name")

        return model_element_type(uid=uid, name=name)

    def _load(self, filename):
        """ Loads the .orm file named *filename* into *self.model* """
        root = self._parse_norma_file(filename)

        # Load file
        self._load_data_types(root)
        self._load_object_types(root)
        self._load_fact_types(root)
        self._load_constraints(root)

        # Post-processing
        self._fix_nested_fact_type_refs()
        self._fix_value_constraints()
        self._update_domains()
        self._update_indirect_subtypes()

    def _log_issues_with(self, filename):
        """ Log any model element omissions. """
        logger = logging.getLogger(__name__)
        size = len(self.omissions)
        if size > 0:
            text = "elements were" if size > 1 else "element was"
            logger.warning("%d model %s ignored while loading %s.", 
                           size, text, os.path.basename(filename))
            for omission in self.omissions:
                logger.info("Ignoring %s", omission)

    def _parse_norma_file(self, filename):
        """ Parse a NORMA File and return the ORMModel node. """
        if filename.split(".")[-1].upper() != "ORM":
            raise Exception("Input filename must have .orm extension.")

        tree = xml.parse(filename)
        root = tree.getroot()

        if root.tag != NS_ROOT + "ORM2":
            raise Exception("Root of input file must be <ormRoot:ORM2>.")

        model_node = root.find(NS_CORE + "ORMModel")

        if model_node is None:
            raise Exception("Cannot find <orm:ORMModel> in input file.")
        else:
            return model_node

    def _load_data_types(self, parent):
        """ Load the data types in the model so that we can assign the
            conceptual data type to each value type. """
        data_type_node = parent.find(NS_CORE + "DataTypes") or []

        for child in data_type_node:
            data_type = local_tag(child) # Data type node tag
            data_id = child.get("id")

            # Look-up Domain subclass corresponding to data type
            try:
                domain = DATA_TYPES[data_type]
            except KeyError:
                domain = None # Leave default Domain in place

            # Store type by ID for later retrieval
            self._elements[data_id] = domain


    def _load_child_nodes(self, parent, target):
        """ Call the loader function associated with each child node of the
            *parent* node.  *target* is the object into which the XML data
            will be loaded.
        """
        if parent is None:
            return

        for child in parent:
            tag = local_tag(child) # Get current node's tag

            try:
                self._loader[tag](child, target) # Call loader function
            except KeyError:
                pass # No loading function defined.

    def _call_loader(self, loader, node, *args):
        """ Call the loader method listed in the loader map for a given node."""
        tag = local_tag(node)
        try:            
            loader[tag](node, *args)
        except KeyError: # No loading function defined.
            self.unexpected.add(tag) 

    ##########################################################################
    # Private Functions to Load Object Types
    ##########################################################################
    def _load_object_types(self, xml_node):
        """ Load the collection of object types. """
        object_types_node = xml_node.find(NS_CORE + "Objects")
        self._load_child_nodes(object_types_node, self.model)

    def _load_entity_type(self, xml_node, target):
        """ Loads an entity type rooted at xml_node """
        self._load_object_type(xml_node, ObjectType.EntityType)

    def _load_value_type(self, xml_node, target):
        """ Loads a value type rooted at xml_node """
        self._load_object_type(xml_node, ObjectType.ValueType)

    def _load_objectified_type(self, xml_node, target):
        """ Loads an objectified type rooted at xml_node """
        self._load_object_type(xml_node, ObjectType.ObjectifiedType)

    def _load_object_type(self, xml_node, target_type):
        """ Loads object type rooted at xml_node into target type. """

        # Construct object type of appropriate underlying type
        object_type = self._construct(xml_node, target_type)
        self._push(object_type)

        object_type.independent = (xml_node.get("IsIndependent") == "true")
        object_type.implicit = (xml_node.get("IsImplicitBooleanValue") == "true")

        # Load inner xml nodes.  Note, some of these may also set implicit=true
        self._load_child_nodes(xml_node, object_type)

        # Add object type the model, unless it is an implicit object type
        explicit = (not object_type.implicit)
        self._add_from_stack(condition=explicit, guard=object_type)

    @staticmethod
    def _load_nested_fact_type(xml_node, object_type):
        """ Loads NestedPredicate xml_node into object_type. """
        if xml_node.get("IsImplied") == "true":
            object_type.implicit = True
        object_type.nested_fact_type = xml_node.get("ref") # GUID of fact type

    def _fix_nested_fact_type_refs(self):
        """ Updates objectified type's nested_fact_type attribute to point to
            the actual fact type and not just the GUID.  MUST be called after
            both object types and fact types are loaded. """
        for object_type in self.model.object_types:
            if isinstance(object_type, ObjectType.ObjectifiedType):
                guid = object_type.nested_fact_type 
                object_type.nested_fact_type = self._elements[guid]

    def _load_subtype_derivation(self, xml_node, object_type):
        """ Loads SubtypeDerivationRule into object_type. """
        self.omissions.append("Subtype derivation rule for " + object_type.name)

    @staticmethod
    def _load_preferred_identifier(xml_node, object_type):
        """ Loads PreferredIdentifier into object_type. """
        # GUID for uniq constraint corresponding to preferred reference scheme
        object_type.identifying_constraint = xml_node.get("ref")

    def _load_conceptual_data_type(self, xml_node, object_type):
        """ Load ConceptualDataType for a ValueType. """
        ref = xml_node.get("ref")  # GUID for data type

        try: # Look-up pre-loaded data type
            domain = self._elements[ref]
        except KeyError:
            domain = None  # Leave default domain in place

        if domain: 
            object_type.domain = domain()

    def _load_value_restriction(self, xml_node, element):
        """ Load value constraint. """
        cons = self._construct(xml_node, Constraint.ValueConstraint)
        cons.covers = [element]

        for value_range in xml_node.find(NS_CORE + "ValueRanges"):
            try:
                cons.add_range(
                    min_value=value_range.get("MinValue"),
                    max_value=value_range.get("MaxValue"),
                    min_open=(value_range.get("MinInclusion") == "Open"),
                    max_open=(value_range.get("MaxInclusion") == "Open")
                )
            except Constraint.ValueConstraintError as ex:
                self.omissions.append("Value constraint " + cons.name + 
                    " because " + ex.message.lower())
                return # Return prematurely so constraint is ignored    

        self._push(cons) # Add constraint to stack

    def _fix_value_constraints(self):
        """ Move value constraints on roles played by an object type that 
            plays no other roles to instead cover the object type. """

        # Per McGill, ORM- cannot support role value constraints, only value
        # constraints on types.  However, if the value constraint covers a 
        # role for an object type that plays no other roles and either
        # 1) The type is not independent (i.e. the role is implicitly mandatory) 
        # 2) The role is covered by an explicit mandatory constraint
        # then the value constraint can be treated as a object type value
        # constraint.

        for cons in self.model.constraints.of_type(Constraint.ValueConstraint):
            element = cons.covers[0]

            if isinstance(element, FactType.Role):
                role = element
                obj = role.player
            
                if len(obj.roles) == 1: # Object type plays exactly 1 role,
                    # which is implicitly or explicitly mandatory
                    if not obj.independent or role.mandatory:
                        self.model.remove(cons) # Rollback side effects
                        cons.covers = [obj]     # Cover object type instead
                        self.model.add(cons)    # Add back to model                   

    def _update_domains(self):
        """ For each value constraint that covers an object type, set that
            object type's domain to the value constraint's domain.  This 
            MUST be called after _fix_value_constraints.  """

        for cons in self.model.constraints.of_type(Constraint.ValueConstraint):
            element = cons.covers[0]

            if isinstance(element, ObjectType.ObjectType):
                object_type = element
                object_type.domain = cons.domain

    def _update_indirect_subtypes(self):
        """ Starting at each root type, build a list of indirect 
            supertypes for each subtype of the root. """

        # NOTE: I do not check for cycles in the subtype graph.  I could, but
        # (a) They are illegal in ORM, and (b) NORMA doesn't permit adding them
        # so I don't think its worth the computational effort.

        for object_type in self.model.object_types:
            if object_type.primitive: # Is a root type
                for child in object_type.direct_subtypes:
                    self._update_subtype(child, object_type, object_type)

                # A primitive type is its own root type
                object_type.root_type = object_type
                                                 
    def _update_subtype(self, this, parent, root):
        """ Update the list of indirect supertypes of this subtype. """

        # Check for multiple root types, which are illegal
        if this.root_type != None and this.root_type != root:
            raise ValueError("Subtype graph containing " + this.fullname + \
                             " has more than one root type")

        this.root_type = root
        this.indirect_supertypes.update(parent.direct_supertypes)
        this.indirect_supertypes.update(parent.indirect_supertypes)

        for child in this.direct_subtypes:
            self._update_subtype(child, this, root)
                   

    ##########################################################################
    # Private Functions to Load Fact Types
    ##########################################################################
    def _load_fact_types(self, xml_node):
        """ Load the collection of fact types. """
        fact_types_node = xml_node.find(NS_CORE + "Facts")
        self._load_child_nodes(fact_types_node, self.model)

    def _load_fact(self, xml_node, fact_type_set):
        """ Load a fact node into a fact type in the model. """
        fact_type = self._construct(xml_node, FactType.FactType)
        self._push(fact_type)

        self._load_child_nodes(xml_node, fact_type)

        # Add fact type and children from stack, unless arity == 0, which
        # means it must be an entirely implicit fact type:
        self._add_from_stack(condition=fact_type.arity() > 0, guard=fact_type)

    def _load_facttype_derivation(self, xml_node, fact_type):
        """ Load a fact type derivation rule. """
        self.omissions.append("Fact type derivation rule for " + fact_type.name)

    def _load_role(self, xml_node, fact_type):
        """ Load a role in a fact type. """
        # Note: NOT using self._construct because we may generate name
        uid = xml_node.get("id")
        name = xml_node.get("Name")

        # Unnamed role.  Find a unique name within the fact type.
        if name is None or name == "":
            name = self._next_role_name(fact_type)

        role = FactType.Role(uid=uid, name=name)
        self._push(role)

        role.fact_type = fact_type

        self._load_child_nodes(xml_node, role)

        # Only add role if the role player exists (i.e. if it was an implicit
        # object type, we do not want the associated role).  For example,
        # NORMA binarizes unary roles; this check reverts the fact type to
        # unary.
        self._add_from_stack(condition=role.player is not None, guard=role)

        if role.player is not None:
            role.player.roles.append(role) # Add to roles played by object type 
            fact_type.add(role) # Need to explicitly add role to fact_type

    def _next_role_name(self, fact_type):
        """ Get next available unique name for a role in a fact type. """
        names = set([role.name for role in fact_type.roles])
        i = fact_type.arity() + 1
        while "R" + str(i) in names:
            i = i + 1
        return "R" + str(i)

    def _load_role_player(self, xml_node, role):
        """ Add the role player to the role. """
        uid = xml_node.get("ref")

        try:
            object_type = self._elements[uid]
        except KeyError:
            object_type = None  # Object type must have been implicit.

        role.player = object_type

    def _load_role_derivation(self, xml_node, role):
        """ Load a role derivation rule. """
        name = role.fact_type.name
        self.omissions.append("Role derivation rule within " + name)


    def _load_subtype_fact(self, xml_node, fact_type_set):
        """ Load a subtype fact, which indicates a subtype constraint. """
        cons = self._construct(xml_node, Constraint.SubtypeConstraint)

        # Get super and sub type XML nodes
        super_node = xml_node.find(NS_CORE + "FactRoles/" +
            NS_CORE + "SupertypeMetaRole")
        sub_node = xml_node.find(NS_CORE + "FactRoles/" +
            NS_CORE + "SubtypeMetaRole")

        superrole = self._construct(super_node, FactType.SubtypeRole)
        subrole = self._construct(sub_node, FactType.SubtypeRole)

        supertype_node = super_node.find(NS_CORE + "RolePlayer")
        subtype_node = sub_node.find(NS_CORE + "RolePlayer")

        # Look-up the corresponding object types
        try:
            cons.supertype = self._elements[supertype_node.get("ref")]
            cons.subtype = self._elements[subtype_node.get("ref")]
        except KeyError:
            raise Exception("Cannot load subtype constraint.")

        cons.covers = [cons.subtype, cons.supertype]

        # Does this subtype constraint provide a path to the preferred ID?
        pref = (xml_node.get("PreferredIdentificationPath") == "true")
        cons.idpath = pref

        # Update corresponding object types
        cons.supertype.direct_subtypes.append(cons.subtype)
        cons.subtype.direct_supertypes.append(cons.supertype)

        self._add(cons) # Add subtype constraint to model

        # Add supertype and subtype roles to _elements dictionary, so that
        # constraints can test whether they constrain a subtype.
        #
        # IMPORTANT: These roles will be in self._elements but will NOT
        # be part of any fact type in the model.
        self._add(superrole)
        self._add(subrole)

    ##########################################################################
    # Private Functions to Load Constraints
    ##########################################################################
    def _load_constraints(self, parent_node):
        """ Load the collection of contraints. """
        loader = {
            'EqualityConstraint'        : self._load_equality_constraint,
            'ExclusionConstraint'       : self._load_exclusion_constraint,
            'SubsetConstraint'          : self._load_subset_constraint,
            'FrequencyConstraint'       : self._load_frequency_constraint,
            'MandatoryConstraint'       : self._load_mandatory_constraint,
            'UniquenessConstraint'      : self._load_uniqueness_constraint,
            'RingConstraint'            : self._load_ring_constraint,
            'ValueComparisonConstraint' : self._load_value_comp_constraint
        }
        constraints_node = parent_node.find(NS_CORE + "Constraints") or []
        for constraint_node in constraints_node:
            self._call_loader(loader, constraint_node)

    def _load_equality_constraint(self, xml_node):
        """ Load equality constraint. """
        self.omissions.append("Equality constraint " + xml_node.get("Name"))

    def _load_exclusion_constraint(self, xml_node):
        """ Load exclusion constraint. """
        # NOTE: THIS CONSTRAINT IS NOT IMPLEMENTED.  CODE BELOW SIMPLY CHECKS
        # WHETHER CONSTRAINT IS USED IN A SUBTYPE.

        cons = self._init_constraint(xml_node, Constraint.ExclusionConstraint)

        seq_node = xml_node.find(NS_CORE + "RoleSequences/" +
            NS_CORE + "RoleSequence")
        first_seq = self._load_role_sequence(seq_node, cons)

        if isinstance(first_seq[0], FactType.SubtypeRole):
            preamble = "Subtype exclusion constraint"
        else:
            preamble = "Exclusion constraint"

        self.omissions.append(preamble + " " + xml_node.get("Name"))

    def _load_subset_constraint(self, xml_node):
        """ Load subset constraint. """
        cons = self._init_constraint(xml_node, Constraint.SubsetConstraint)

        # Find RoleSequences node (should have exactly 2 RoleSequence children)
        sequences_node = xml_node.find(NS_CORE + "RoleSequences")

        if len(sequences_node) != 2:
            raise Exception("Constraint " + cons.name +
                " does not have exactly two role sequences (sub and super).")

        # Load subset and superset role sequences
        cons.subset = self._load_role_sequence(sequences_node[0], cons)
        cons.superset = self._load_role_sequence(sequences_node[1], cons)

        # Role sequence will be None if sequence has unsupported feature
        if cons.subset is not None and cons.superset is not None:
            cons.covers = cons.subset + cons.superset # All covered roles

            if len(cons.subset) <= 2 and len(cons.superset) <= 2:
                self._add(cons)
            else:
                msg = "Subset constraint " + cons.name + " (due to arity > 2)"
                self.omissions.append(msg)

    def _load_frequency_constraint(self, xml_node):
        """ Load frequency constraint. """
        cons = self._construct(xml_node, Constraint.FrequencyConstraint)

        # Parse frequency attributes
        cons.min_freq = int(xml_node.get("MinFrequency"))
        cons.max_freq = int(xml_node.get("MaxFrequency"))

        if cons.max_freq == 0: # Unbounded
            cons.max_freq = float('inf')

        # Get sequence of covered roles
        seq_node = xml_node.find(NS_CORE + "RoleSequence")
        cons.covers = self._load_role_sequence(seq_node, cons)
     
        if cons.covers is not None: # None indicates constraint is unsupported
            # Detect whether frequency constraint is internal
            fact_types = set()
            for role in cons.covers:
                fact_types.add(role.fact_type)
            cons.internal = (len(fact_types) == 1)

            # Add to model
            self._add(cons)

    def _load_mandatory_constraint(self, xml_node):
        """ Load mandatory constraint. """
        cons = self._construct(xml_node, Constraint.MandatoryConstraint)

        # Ignore implied mandatory (do not even add to omissions)
        if xml_node.get("IsImplied") == "true":
            return

        seq_node = xml_node.find(NS_CORE + "RoleSequence")
        cons.covers = self._load_role_sequence(seq_node, cons)

        if cons.covers is None:
            return # Unsupported or implicit
        elif len(cons.covers) > 1: # Part of XOR or inclusive-or constraint
            if isinstance(cons.covers[0], FactType.SubtypeRole):
                preamble = "Subtype inclusive-or constraint"
            else:
                preamble = "Inclusive-or constraint"
            self.omissions.append(preamble + " " + cons.name)
        elif isinstance(cons.covers[0], FactType.SubtypeRole):
            return # Simple mandatory on implicit subtype fact type
        else: # Simple mandatory on regular role
            role = cons.covers[0]
            role.mandatory = True

            self._add(cons)

    def _load_uniqueness_constraint(self, xml_node):
        """ Load uniqueness constraint. """
        cons = self._init_constraint(xml_node, Constraint.UniquenessConstraint)

        cons.internal = (xml_node.get("IsInternal") == "true")

        # Get object type that this constraint is a preferred id for
        pref_node = xml_node.find(NS_CORE + "PreferredIdentifierFor")
        if pref_node is not None:
            self._load_identifier_for(pref_node, cons)

        # Get sequence of covered roles
        seq_node = xml_node.find(NS_CORE + "RoleSequence")
        cons.covers = self._load_role_sequence(seq_node, cons)

        # Confirm constraint is supported and not on an implicit subtype fact
        supported = (cons.covers is not None)
        if supported:
            implicit_subtype = isinstance(cons.covers[0], FactType.SubtypeRole)
        
        # Add to model
        if supported and not implicit_subtype:
            self._add(cons)

    def _load_identifier_for(self, xml_node, constraint):
        """ Loads the object type that a uniqueness constraint is a preferred
            identifier for. """
        uid = xml_node.get("ref")
        try:
            object_type = self._elements[uid]
            constraint.identifier_for = object_type
            object_type.identifying_constraint = constraint
        except KeyError:
            pass # An implicit object?

    def _load_ring_constraint(self, xml_node):
        """ Load ring constraint. """
        self.omissions.append("Ring constraint " + xml_node.get("Name"))

    def _load_value_comp_constraint(self, xml_node):
        """ Load value comparison constraint. """
        self.omissions.append("Value comparison constraint " +
            xml_node.get("Name"))

    def _load_cardinality_constraint(self, xml_node, parent):
        """ Load cardinality constraint. """
        types = ["CardinalityConstraint", "UnaryRoleCardinalityConstraint"]
        valid_type = lambda x: local_tag(x) in types

        if len(xml_node) != 1:
            raise ValueError("CardinalityRestriction should have only 1 child node")
        
        for node in filter(valid_type, xml_node):          
            cons = self._init_constraint(node, Constraint.CardinalityConstraint)   
            cons.covers = [parent]

            range_node = node.find(NS_CORE + "Ranges")
            cons.ranges = self._load_cardinality_ranges(range_node)

            self._add(cons)

    def _load_cardinality_ranges(self, xml_node):
        """ Load a list of cardinality ranges. """
        ranges = []
        for node in xml_node:
            if local_tag(node) == 'CardinalityRange':
                lower = int(node.get("From")) # "From" attribute is mandatory
                upper = node.get("To")   # "To" attribute is optional
                upper = int(upper) if upper else None
                ranges.append(Constraint.CardinalityRange(lower, upper))
        return ranges

    def _init_constraint(self, xml_node, constraint_type):
        """ Initialize a constraint from an xml_node. """
        cons = self._construct(xml_node, constraint_type)
        cons.alethic = (xml_node.get("Modality") != "Deontic")
        return cons

    def _load_role_sequence(self, xml_node, constraint):
        """ Returns a sequence of roles covered by the constraint.
            xml_node points to the RoleSequence node. """

        role_sequence = FactType.RoleSequence()
        ignore = False # Whether to ignore this role sequence

        for node in xml_node:
            if local_tag(node) == "Role":
                role = self._load_constraint_role(node, constraint)
                ignore = (role is None) # Constraint covers implied role
                role_sequence.append(role)
            elif local_tag(node) == "JoinRule":
                self._load_join_rule(node, constraint, role_sequence)
            else:
                raise Exception("Constraint " + constraint.name +
                    " has unexpected role sequence.")

        return None if ignore else role_sequence

    def _load_constraint_role(self, xml_node, constraint):
        """ Returns a Role element within the RoleSequence of a constraint. """

        # Confirm deprecated path data is not present
        if xml_node.find(NS_CORE + "ProjectedFrom") is not None:
            msg = "Constraint " + constraint.name +" has deprecated join rule."
            raise Exception(msg)

        try:
            uid = xml_node.get("ref")
            return self._elements[uid]
        except KeyError:
            return None # Role not in elements[] if part of implied fact type


    def _load_join_rule(self, xml_node, constraint, role_sequence):
        """ Loads a join rule. """
        self.omissions.append("Join path for " + constraint.name + ".")
        role_sequence.join_path = "" # Just so that it is not None, for now.

###############################################################################
# Utility Functions
###############################################################################
def local_tag(xml_node):
    """ Strips namespace from a node's tag. """
    return xml_node.tag.replace(NS_CORE, "")




