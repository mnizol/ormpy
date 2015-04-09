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
        self._elements = {}   # Dictionary of {id, element} pairs

        # Items in the .orm file omitted by NormaLoader
        self.omissions = [] #: Intentionally omitted model elements
        self.unexpected = set() #: Unexpected nodes in the XML file

        # Find root of XML tree       
        self._model_root = self._parse_norma_file(filename)

        # Load file
        self._load_data_types()
        self._load_object_types()
        self._load_fact_types() # Also loads subtypes
        self._load_constraints()

        # Post-processing
        self._fix_nested_fact_type_refs() 
        self._update_indirect_subtypes()

        # Report any issues to the user
        self._log_issues_with(filename)      
        

    ###########################################################################
    # Private Utility Functions
    ###########################################################################
    def _add(self, model_element):
        """ Add model element to the model. """
        self._elements[model_element.uid] = model_element 

        # Add to model, unless it is a role (which is added as part of its
        # containing fact type).
        if not isinstance(model_element, FactType.Role):       
            self.model.add(model_element)

    @staticmethod
    def _construct(xml_node, model_element_type, **kwargs):
        """ Construct a new model element from the XML node. """
        uid = xml_node.get("id")
        name = xml_node.get("Name")

        if name is None: # Some nodes use "_Name" instead
            name = xml_node.get("_Name")

        return model_element_type(uid=uid, name=name, **kwargs)

    def _parse_norma_file(self, filename):
        """ Parse a NORMA File and return the ORMModel node. """
        if filename.split(".")[-1].upper() != "ORM":
            raise Exception("Input filename must have .orm extension.")

        tree = xml.parse(filename)
        root = tree.getroot()

        if root.tag != NS_ROOT + "ORM2":
            raise Exception("Root of input file must be <ormRoot:ORM2>.")

        model_node = find(root, "ORMModel")

        if model_node is None:
            raise Exception("Cannot find <orm:ORMModel> in input file.")
        else:
            return model_node

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

    def _call_loader(self, loader, node, *args):
        """ Call the loader method listed in the loader map for a given node."""
        tag = local_tag(node)
        try:            
            return loader[tag](node, *args)
        except KeyError: # No loading function defined.
            self.unexpected.add(tag) 
            return None

    def _move_node_to_constraints(self, node, parent):
        """ Make an xml node a subelement of the Constraints sequence node. """
        root = self._model_root
        constraints_node = find(root, "Constraints") 

        if constraints_node == None: # Create a Constraints node if needed
            constraints_node = xml.SubElement(root, NS_CORE + "Constraints")

        node.set('_covered_element', parent.uid)
        constraints_node.append(node)

    ##########################################################################
    # Private Functions to Load Conceptual Data Types
    ##########################################################################
    def _load_data_types(self):
        """ Load the data types in the model so that we can assign the
            conceptual data type to each value type. """
        for child in node_collection(self._model_root, "DataTypes"):
            data_type = local_tag(child) # Data type node tag
            data_id = child.get("id")

            # Look-up Domain subclass corresponding to data type
            try:
                domain = DATA_TYPES[data_type]
            except KeyError:
                domain = None # Leave default Domain in place

            # Store type by ID for later retrieval
            self._elements[data_id] = domain

    ##########################################################################
    # Private Functions to Load Object Types
    ##########################################################################
    def _load_object_types(self):
        """ Load the collection of object types. """
        type_of = {
            'EntityType'      : ObjectType.EntityType,
            'ValueType'       : ObjectType.ValueType,
            'ObjectifiedType' : ObjectType.ObjectifiedType,
        }
        for node in node_collection(self._model_root, "Objects"):
            tag = local_tag(node)
            self._load_object_type(node, type_of[tag])

    def _load_object_type(self, xml_node, target_type):
        """ Loads object type rooted at xml_node into target type. """
        loader = {            
            'NestedPredicate'       : self._load_nested_fact_type,
            'SubtypeDerivationRule' : self._load_subtype_derivation,
            'PreferredIdentifier'   : self._load_preferred_identifier,
            'ConceptualDataType'    : self._load_conceptual_data_type,
            'ValueRestriction'      : self._move_node_to_constraints,
            'CardinalityRestriction': self._move_node_to_constraints,
            'Definitions'           : noop,
            'Notes'                 : noop,
            'Abbreviations'         : noop,
            'PlayedRoles'           : noop, # Captured when loading <Roles>
            'Instances'             : noop,
            'Extensions'            : noop
        }

        # Construct object type of appropriate underlying type
        object_type = self._construct(xml_node, target_type)

        object_type.independent = (xml_node.get("IsIndependent") == "true")
        object_type.implicit = (xml_node.get("IsImplicitBooleanValue") == "true")

        # Load inner xml nodes.  Note, some of these may also set implicit=true
        for node in xml_node:
            self._call_loader(loader, node, object_type)

        # Add object type the model, unless it is an implicit object type
        if object_type.implicit == False:
            self._add(object_type)

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
        domain = self._elements.get(ref)
        if domain: 
            # TODO: Temporary hack, accessing private member.  Eventually plan 
            # to have these functions set values in an attribs dictionary, and
            # then construct ObjectType at the end of _load_object_type
            object_type._data_type = domain()                
            object_type.domain = object_type.data_type 

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
    def _load_fact_types(self):
        """ Load the collection of fact types. """
        loader = {             
            'Fact'        : self._load_fact_type,
            'SubtypeFact' : self._load_subtype_fact,
            'ImpliedFact' : noop
        }
        for node in node_collection(self._model_root, "Facts"):
            self._call_loader(loader, node)   

    def _load_fact_type(self, xml_node):
        """ Load a fact type node into a fact type in the model. """
        loader = {
            'FactRoles'           : self._load_roles,
            'DerivationRule'      : self._load_facttype_derivation,
            'Definitions'         : noop,
            'Notes'               : noop,
            'ReadingOrders'       : noop,
            'InternalConstraints' : noop,  # Captured when loading <Constraints>
            'Instances'           : noop,
            'Extensions'          : noop
        }
        fact_type = self._construct(xml_node, FactType.FactType)

        for node in xml_node:
            self._call_loader(loader, node, fact_type)

        # If arity == 0, all roles were played by implicit object types
        if fact_type.arity() > 0:
            self._add(fact_type)

    def _load_facttype_derivation(self, xml_node, fact_type):
        """ Load a fact type derivation rule. """
        self.omissions.append("Fact type derivation rule for " + fact_type.name)

    def _load_roles(self, xml_node, fact_type):
        """ Load a list of roles of a fact type. """
        loader = {'Role': self._load_role}
        for node in xml_node:
            self._call_loader(loader, node, fact_type)

    def _load_role(self, xml_node, fact_type):
        """ Load a role in a fact type. """
        loader = {
            'RolePlayer'            : self._load_role_player,            
            'DerivationSource'      : self._load_role_derivation,            
            'ValueRestriction'      : self._move_node_to_constraints, 
            'CardinalityRestriction': self._move_node_to_constraints,
            'RoleInstances'         : noop,
            'Extensions'            : noop
        }
        # Note: NOT using self._construct because we may generate name
        uid = xml_node.get("id")
        name = xml_node.get("Name")

        # Unnamed role.  Find a unique name within the fact type.
        if name is None or name == "":
            name = self._next_role_name(fact_type)

        role = FactType.Role(uid=uid, name=name)
        role.fact_type = fact_type

        for node in xml_node:
            self._call_loader(loader, node, role)

        # Only add role if the role player exists (e.g. we do not want a role
        # played by an implicit object type).  For example, NORMA binarizes 
        # unary roles; this check reverts the fact type to unary.
        if role.player is not None:
            self._add(role)
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


    def _load_subtype_fact(self, xml_node):
        """ Load a subtype fact, which indicates a subtype constraint.  Note,
            we chose not to move this node under <Constraints>, because it must
            be loaded prior to any associated XOR/IOR constraints. """
        cons = self._construct(xml_node, Constraint.SubtypeConstraint)

        # Get super and sub type XML nodes
        factroles = find(xml_node, "FactRoles")
        super_node = find(factroles, "SupertypeMetaRole")
        sub_node = find(factroles, "SubtypeMetaRole")
        supertype_node = find(super_node, "RolePlayer")
        subtype_node = find(sub_node, "RolePlayer")

        # Look-up the corresponding object types
        try:
            cons.supertype = self._elements[supertype_node.get("ref")]
            cons.subtype = self._elements[subtype_node.get("ref")]
        except KeyError:
            raise Exception("Cannot load subtype constraint.")

        cons.covers = [cons.subtype, cons.supertype]

        # Does this subtype constraint provide a path to the preferred ID?
        cons.idpath = (xml_node.get("PreferredIdentificationPath") == "true")

        # Update corresponding object types
        cons.supertype.direct_subtypes.append(cons.subtype)
        cons.subtype.direct_supertypes.append(cons.supertype)

        # If there are additional constraints on the subtype (e.g. XOR or IOR),
        # their role sequence will consist of the subtype fact's roles. We will
        # redirect the id for those roles to this constraint, so that the covers 
        # attribute is a list of SubtypeConstraints for constraints on subtypes.
        self._elements[super_node.get("id")] = cons
        self._elements[sub_node.get("id")] = cons

        self._add(cons) # Add subtype constraint to model

    ##########################################################################
    # Private Functions to Load Constraints
    ##########################################################################
    def _load_constraints(self):
        """ Load the collection of contraints. """
        loader = {
            'EqualityConstraint'        : self._load_equality_constraint,
            'ExclusionConstraint'       : self._load_exclusion_constraint,
            'SubsetConstraint'          : self._load_subset_constraint,
            'FrequencyConstraint'       : self._load_frequency_constraint,
            'MandatoryConstraint'       : self._load_mandatory_constraint,
            'UniquenessConstraint'      : self._load_uniqueness_constraint,
            'RingConstraint'            : self._load_ring_constraint,
            'ValueComparisonConstraint' : self._load_value_comp_constraint,
            'ValueRestriction'          : self._load_value_constraint,
            'CardinalityRestriction'    : self._load_cardinality_constraint
        }
        for node in node_collection(self._model_root, "Constraints"):
            cons = self._call_loader(loader, node)
            if cons != None and cons.covers != None:
                self._add(cons)

    def _init_constraint(self, xml_node, constraint_type, **kwargs):
        """ Initialize a constraint from an xml_node. """
        cons = self._construct(xml_node, constraint_type, **kwargs)
        cons.alethic = (xml_node.get("Modality") != "Deontic")
        return cons

    def _load_equality_constraint(self, xml_node):
        """ Load equality constraint. """
        self.omissions.append("Equality constraint " + xml_node.get("Name"))
        return None

    def _load_exclusion_constraint(self, xml_node):
        """ Load exclusion constraint. """
        attribs, name = get_basic_attribs(xml_node)
        kind = "Exclusion constraint"

        seq_node = find(xml_node, "RoleSequences")
        first_seq = self._load_role_sequence(seq_node[0], name)
        if isinstance(first_seq[0], Constraint.SubtypeConstraint):
            kind = "Subtype " + kind.lower()

        self.omissions.append(kind + " " + name)
        return None

    def _load_subset_constraint(self, xml_node):
        """ Load subset constraint. """
        attribs, name = get_basic_attribs(xml_node)

        sequences_node = find(xml_node, "RoleSequences")

        if len(sequences_node) != 2:
            msg = "Constraint {0} does not have exactly two role sequences"
            raise Exception(msg.format(name))

        # Load subset and superset role sequences
        attribs['subset'] = self._load_role_sequence(sequences_node[0], name)
        attribs['superset'] = self._load_role_sequence(sequences_node[1], name)

        return Constraint.SubsetConstraint(**attribs)

    def _load_frequency_constraint(self, xml_node):
        """ Load frequency constraint. """
        attribs, name = get_basic_attribs(xml_node)

        # Parse frequency attributes
        min_freq = int(xml_node.get("MinFrequency"))
        max_freq = int(xml_node.get("MaxFrequency"))

        # Build attribute dictionary
        attribs['min_freq'] = min_freq
        attribs['max_freq'] = max_freq if max_freq > 0 else float('inf')
        attribs['covers'] = self._load_role_sequence(xml_node, name)

        return Constraint.FrequencyConstraint(**attribs)

    def _load_mandatory_constraint(self, xml_node):
        """ Load mandatory constraint. """
        attribs, name = get_basic_attribs(xml_node)

        implied = (xml_node.get("IsImplied") == "true")
        covers = self._load_role_sequence(xml_node, name)

        # Lambda functions to decide if constraint covers a subtype or is simple
        subtype = lambda x: x and isinstance(x[0], Constraint.SubtypeConstraint)
        simple = lambda x: x and len(x) == 1 and isinstance(x[0], FactType.Role)

        if simple(covers) and not(implied):
            return Constraint.MandatoryConstraint(covers=covers, **attribs)
        else:
            if not(implied) and len(covers or []) > 1: 
                kind = "Inclusive-or constraint"
                if subtype(covers): kind = "Subtype " + kind.lower()
                self.omissions.append(kind + " " + name)
            return None

    def _load_uniqueness_constraint(self, xml_node):
        """ Load uniqueness constraint. """
        attribs, name = get_basic_attribs(xml_node)

        # Get object type that this constraint is a preferred id for
        pref_node = find(xml_node, "PreferredIdentifierFor")
        if pref_node is not None:
            uid = pref_node.get("ref")
            attribs['identifier_for'] = self._elements.get(uid)

        # Get sequence of covered roles
        covers = self._load_role_sequence(xml_node, name)

        if covers and isinstance(covers[0], Constraint.SubtypeConstraint):
            return None # Covers a role in an implicit subtype fact
        else:
            return Constraint.UniquenessConstraint(covers=covers, **attribs)

    def _load_ring_constraint(self, xml_node):
        """ Load ring constraint. """
        self.omissions.append("Ring constraint " + xml_node.get("Name"))
        return None

    def _load_value_comp_constraint(self, xml_node):
        """ Load value comparison constraint. """
        name = xml_node.get("Name")
        self.omissions.append("Value comparison constraint " + name)
        return None

    def _load_value_constraint(self, parent_node):
        """ Load value constraint. """
        node = parent_node[0] # parent_node is <ValueRestriction>    

        types = ['ValueConstraint', 'RoleValueConstraint']
        if len(parent_node) != 1 or local_tag(node) not in types:
            raise ValueError("Unexpected value constraint format")

        attribs, name = get_basic_attribs(node)
        attribs['covers'] = covers = self._get_covered_element(parent_node)

        data_type = covers[0].data_type if covers else None

        try:
            domain = Constraint.ValueDomain()
            for value_range in node_collection(node, "ValueRanges"):
                domain.add_range(
                    min_value=value_range.get("MinValue"),
                    max_value=value_range.get("MaxValue"),
                    min_open=(value_range.get("MinInclusion") == "Open"),
                    max_open=(value_range.get("MaxInclusion") == "Open"),
                    data_type=data_type
                )
        except Constraint.ValueConstraintError as ex:
            reason = ex.message.lower()
            mesg = "Value constraint {0} because {1}".format(name, reason)
            self.omissions.append(mesg)
            return None

        return Constraint.ValueConstraint(domain, **attribs)

    def _load_cardinality_constraint(self, parent_node):
        """ Load cardinality constraint. """
        node = parent_node[0]

        types = ["CardinalityConstraint", "UnaryRoleCardinalityConstraint"]
        if len(parent_node) != 1 or local_tag(node) not in types: 
            raise ValueError("Unexpected cardinality constraint format")
        
        cons = self._init_constraint(node, Constraint.CardinalityConstraint)   
        cons.covers = self._get_covered_element(parent_node)
        cons.ranges = self._load_cardinality_ranges(node)

        return cons

    def _load_cardinality_ranges(self, parent_node):
        """ Load a list of cardinality ranges. """
        ranges = []
        isrange = lambda x: local_tag(x) == 'CardinalityRange'

        for node in filter(isrange, node_collection(parent_node, "Ranges")):
            lower = int(node.get("From")) # "From" attribute is mandatory
            upper = node.get("To")   # "To" attribute is optional
            upper = int(upper) if upper else None
            ranges.append(Constraint.CardinalityRange(lower, upper))
        return ranges

    def _get_covered_element(self, node):
        """ Returns element covered by a constraint. Used by ValueConstraint
            and CardinalityConstraint, which have been moved from their parent
            nodes to the Constraints node. """
        try:
            # _covered_element is added via _move_node_to_constraints()
            uid = node.get("_covered_element")
            return [self._elements[uid]]
        except KeyError:
            return None

    def _load_role_sequence(self, xml_node, constraint_name):
        """ Returns a sequence of roles covered by a constraint.
            xml_node points to the RoleSequence node. """

        if local_tag(xml_node) != 'RoleSequence':
            xml_node = find(xml_node, 'RoleSequence')

        name = constraint_name
        role_sequence = FactType.RoleSequence()
        implied_roles = 0 # Number of implied roles in the sequence

        for node in xml_node:
            if local_tag(node) == "Role":
                role = self._load_constraint_role(node, name)
                implied_roles += (role is None)
                role_sequence.append(role)
            elif local_tag(node) == "JoinRule":
                self._load_join_rule(node, name, role_sequence)
            else:
                msg = "Constraint {0} has unexpected role sequence."
                raise Exception(msg.format(name))

        if 0 < implied_roles < len(xml_node):
            msg = "Constraint {0} because it covers implied and explicit roles"               
            self.omissions.append(msg.format(name))
            return None
        elif implied_roles == len(xml_node): # Implied constraint 
            return None
        else:
            return role_sequence

    def _load_constraint_role(self, xml_node, constraint_name):
        """ Returns a Role element within the RoleSequence of a constraint. """

        # Confirm deprecated path data is not present
        if find(xml_node, "ProjectedFrom") is not None:
            msg = "Constraint " + constraint_name +" has deprecated join rule."
            raise Exception(msg)

        try:
            uid = xml_node.get("ref")
            return self._elements[uid]
        except KeyError:
            return None # Role not in elements[] if part of implied fact type


    def _load_join_rule(self, xml_node, constraint_name, role_sequence):
        """ Loads a join rule. """
        self.omissions.append("Join path for " + constraint_name + ".")
        role_sequence.join_path = "" # Just so that it is not None, for now.

###############################################################################
# Utility Functions
###############################################################################
def noop(*args, **kwargs):
    """ Do nothing. """
    pass

def local_tag(xml_node):
    """ Strips namespace from a node's tag. """
    return xml_node.tag.replace(NS_CORE, "")

def find(xml_node, name):
    """ Fine a node under a parent xml node. """
    return xml_node.find(NS_CORE + name)

def node_collection(xml_node, name):
    """ Return the collection of nodes named 'name' under a parent xml node. """
    return find(xml_node, name) or []

def get_basic_attribs(xml_node):
    """ Return a dictionary of commonly needed attributes from an xml_node. """
    attribs = {}
    attribs['uid'] = xml_node.get("id")
    attribs['name'] = xml_node.get("Name") or xml_node.get("_Name")

    alethic = xml_node.get("Modality")
    if alethic is not None:
        attribs['alethic'] = (alethic != "Deontic")

    return attribs, attribs['name']




