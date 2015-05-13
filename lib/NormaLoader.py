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
from lib.JoinPath import JoinPath, JoinPathException

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
    def __init__(self, filename, deontic=False):
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
        self._load_constraints(deontic)

        # Post-processing
        self._fix_nested_fact_type_refs() 

        # Report any issues to the user
        self._log_issues(filename, self.omissions, "model element", "ignored")      
        self._log_issues(filename, self.unexpected, "XML node", "unexpected")

    ###########################################################################
    # Private Utility Functions
    ###########################################################################
    def _add(self, model_element):
        """ Add model element to the model. """
        self._elements[model_element.uid] = model_element 
        self.model.add(model_element)

    @staticmethod
    def _construct(xml_node, model_element_type, **kwargs):
        """ Construct a new model element from the XML node. """
        uid = xml_node.get("id")
        name = xml_node.get("Name") or xml_node.get("_Name")
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

    def _log_issues(self, filename, issue_list, subject, issue_type):
        """ Log issues reported in an issues list. """
        logger = logging.getLogger(__name__)
        size = len(issue_list)

        if size > 0:
            subject = ("{0}s were" if size > 1 else "{0} was").format(subject)
            filename = os.path.basename(filename)
            template = "%d %s %s while loading %s."

            logger.warning(template, size, subject, issue_type, filename)

            for issue in issue_list:
                logger.info("%s %s", issue_type.capitalize(), issue)

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

        tag = local_tag(node)

        # Special handling for ValueRestriction and CardinalityRestriction:
        # we move the node that is 1 level down instead (e.g. ValueConstraint)
        special = {'ValueRestriction'       : 'value constraint', 
                   'CardinalityRestriction' : 'cardinality constraint'}
        
        if tag in special.keys():
            if len(node) != 1: 
                raise ValueError("Unexpected {0} format".format(special[tag]))
            node = node[0] # Move 1 level down
                            
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
            object_type._data_type = domain()                
            object_type.domain = object_type.data_type 

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
            'RolePlayer'            : noop, # We call _load_role_player directly           
            'DerivationSource'      : self._load_role_derivation,            
            'ValueRestriction'      : self._move_node_to_constraints, 
            'CardinalityRestriction': self._move_node_to_constraints,
            'RoleInstances'         : noop,
            'Extensions'            : noop
        }
        attribs, name = get_basic_attribs(xml_node)
        uid = attribs['uid']
        player = self._load_role_player(xml_node)

        # Add the role if the role player exists (i.e. we do not want a role
        # played by an implicit object type).  For example, NORMA binarizes 
        # unary roles; this check reverts the fact type to unary.
        if player is not None:                         
            role = fact_type.add_role(player, name, uid)
            self._elements[role.uid] = role

            for node in xml_node: # Process any remaining child nodes
                self._call_loader(loader, node, role)        

    def _load_role_player(self, xml_node):
        """ Return the player of the role. """
        uid = find(xml_node, 'RolePlayer').get("ref")
        return self._elements.get(uid)

    def _load_role_derivation(self, xml_node, role):
        """ Load a role derivation rule. """
        name = role.fact_type.name
        self.omissions.append("Role derivation rule within " + name)

    def _load_subtype_fact(self, xml_node):
        """ Load a subtype fact, which indicates a subtype constraint.  Note,
            we chose not to move this node under <Constraints>, because it must
            be loaded prior to any associated XOR/IOR constraints. """
        attribs, name = get_basic_attribs(xml_node)
 
        # Get super and sub type XML nodes
        factroles = find(xml_node, "FactRoles")
        super_node = find(factroles, "SupertypeMetaRole")
        sub_node = find(factroles, "SubtypeMetaRole")
        supertype_node = find(super_node, "RolePlayer")
        subtype_node = find(sub_node, "RolePlayer")

        # Look-up the corresponding object types
        try:
            supertype = self._elements[supertype_node.get("ref")]
            subtype = self._elements[subtype_node.get("ref")]
        except KeyError:
            raise Exception("Cannot load subtype constraint.")

        # Does this subtype constraint provide a path to the preferred ID?
        path = (xml_node.get("PreferredIdentificationPath") == "true")

        # Create constraint
        cons = Constraint.SubtypeConstraint(subtype, supertype, path, **attribs)

        # If there are additional constraints on the subtype (e.g. XOR or IOR),
        # their role sequence will consist of the subtype fact's roles. We will
        # redirect the id for those roles to this constraint, so that the covers 
        # attribute is a list of SubtypeConstraints for constraints on subtypes.
        self._elements[super_node.get("id")] = cons
        self._elements[sub_node.get("id")] = cons

        self._add(cons) 

    ##########################################################################
    # Private Functions to Load Constraints
    ##########################################################################
    def _load_constraints(self, deontic=False):
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
            'ValueConstraint'           : self._load_value_constraint, 
            'RoleValueConstraint'       : self._load_value_constraint,
            'CardinalityConstraint'         : self._load_cardinality_constraint,
            'UnaryRoleCardinalityConstraint': self._load_cardinality_constraint
        }
        for node in node_collection(self._model_root, "Constraints"):
            if deontic == False and node.get("Modality") == "Deontic":
                continue

            result = self._call_loader(loader, node)
    
            if not isinstance(result, list): 
                result = [result]

            for cons in result:
                if cons != None and cons.covers != None:
                    self._add(cons)

    def _load_exclusion_constraint(self, xml_node):
        """ Load exclusion constraint. """
        attribs, name = get_basic_attribs(xml_node)
        kind = "Exclusion constraint"

        seq_node = find(xml_node, "RoleSequences")
        first_seq = self._load_role_sequence(seq_node[0], kind + " " + name)
        if isinstance(first_seq[0], Constraint.SubtypeConstraint):
            kind = "Subtype " + kind.lower()

        self.omissions.append(kind + " " + name)
        return None

    def _load_subset_constraint(self, xml_node):
        """ Load subset constraint. """
        attribs, name = get_basic_attribs(xml_node)
        name = "Subset constraint " + name

        sequences_node = find(xml_node, "RoleSequences")

        if len(sequences_node) != 2:
            msg = "{0} does not have exactly two role sequences"
            raise Exception(msg.format(name))

        # Load subset and superset role sequences
        attribs['subset'] = self._load_role_sequence(sequences_node[0], name)
        attribs['superset'] = self._load_role_sequence(sequences_node[1], name)

        return Constraint.SubsetConstraint(**attribs)

    def _load_equality_constraint(self, xml_node):
        """ Load equality constraint. """
        attribs, name = get_basic_attribs(xml_node)
        name = "Equality constraint " + name

        sequences_node = find(xml_node, "RoleSequences")

        # If there are > 2 role sequences, we split the equality constraint
        # into multiple 2-role-sequence equality constraints.  Each of them use
        # sequences_node[0] as the superset sequence and then one of the
        # subsequent role sequences as their subset sequence.

        cons_list = []
        superset_seq = sequences_node[0]        
        attribs['superset'] = self._load_role_sequence(superset_seq, name)
        sequences_node.remove(superset_seq)

        for sequence in sequences_node:
            attribs['subset'] = self._load_role_sequence(sequence, name)                
            cons_list.append(Constraint.EqualityConstraint(**attribs))

        return cons_list

    def _load_frequency_constraint(self, xml_node):
        """ Load frequency constraint. """
        attribs, name = get_basic_attribs(xml_node)
        name = "Frequency constraint " + name

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
        covers = self._load_role_sequence(xml_node, "Mandatory constraint " + name)

        # Lambda function to decide if constraint covers a subtype
        subtype = lambda x: x and isinstance(x[0], Constraint.SubtypeConstraint)

        if implied:
            return None
        elif subtype(covers):   
            if len(covers) > 1: # If len == 1 its on the implicit subtype fact
                self.omissions.append("Subtype inclusive-or constraint " + name)
            return None
        else:
            return Constraint.MandatoryConstraint(covers=covers, **attribs)

    def _load_uniqueness_constraint(self, xml_node):
        """ Load uniqueness constraint. """
        attribs, name = get_basic_attribs(xml_node)
        name = "Uniqueness constraint " + name

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

    def _load_value_constraint(self, node):
        """ Load value constraint. """
        attribs, name = get_basic_attribs(node)
        attribs['covers'] = covers = self._get_covered_element(node)

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

    def _load_cardinality_constraint(self, node):
        """ Load cardinality constraint. """
        attribs, name = get_basic_attribs(node)
        attribs['covers'] = self._get_covered_element(node)
        attribs['ranges'] = self._load_cardinality_ranges(node)

        return Constraint.CardinalityConstraint(**attribs)

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
            xml_node points to the RoleSequence node or its parent node. """

        if local_tag(xml_node) != 'RoleSequence':
            xml_node = find(xml_node, 'RoleSequence')

        name = constraint_name
        role_sequence = FactType.RoleSequence()
        implied_roles = 0 # Number of implied roles in the sequence
        total_roles = 0   # Total number of roles in the sequence

        for node in xml_node:
            if local_tag(node) == "Role":
                role = self._load_constraint_role(node, name)
                implied_roles += (role is None)
                total_roles += 1
                role_sequence.append(role)
            elif local_tag(node) == "JoinRule":
                try:
                    role_sequence.join_path = self._load_join_rule(node)
                except JoinPathException as ex:
                    msg = "{0} because its join path {1}."
                    self.omissions.append(msg.format(name, ex.message))
                    return None
            else:
                msg = "{0} has unexpected role sequence."
                raise Exception(msg.format(name))

        if 0 < implied_roles < total_roles:
            msg = "{0} because it covers implied and explicit roles"               
            self.omissions.append(msg.format(name))
            return None
        elif implied_roles == total_roles: # Implied constraint 
            return None
        else:
            return role_sequence

    def _load_constraint_role(self, xml_node, constraint_name):
        """ Returns a Role element within the RoleSequence of a constraint. """

        # Confirm deprecated path data is not present
        if find(xml_node, "ProjectedFrom") is not None:
            msg = constraint_name +" has deprecated join rule."
            raise Exception(msg)

        uid = xml_node.get("ref")
        return self._elements.get(uid)

    ###########################################################################
    # Note to future maintainers: the next four methods (_load_join_rule,
    # _load_join_path, _load_linear_path, _load_branches) is my attempt to 
    # parse the very complex <JoinRule> node and its children.  Join rules in 
    # NORMA support many features (subqueries, calculations, negations, etc.) 
    # that we haven't observed in industry ORM models.  Thus, we only load the 
    # most common types of join rules and raise JoinPathExceptions for the rest.
    ###########################################################################

    def _load_join_rule(self, node):
        """ Loads a join rule (i.e. a <JoinRule> node and its children). """
        join_path = JoinPath()
        
        if not(len(node) == 1 and local_tag(node[0]) == 'JoinPath'):
            raise JoinPathException("does not have exactly one JoinPath node")  

        for child in node[0]:
            if local_tag(child) in ['PathComponents', 'PathComponent']:
                if len(child) == 1 and local_tag(child[0]) == 'RolePath':
                    self._load_join_path(child[0], join_path)
                else:
                    msg = "does not have exactly one RolePath node"
                    raise JoinPathException(msg)                              
            elif local_tag(child) == 'JoinPathProjections':
                # NOTE: I am ignoring this node for now, because it's not needed
                # to determine the join path itself.  The only reason to do any
                # processing here would be to confirm that there are no 
                # unexpected children of this node (e.g. a CalculatedValue) and
                # to double-check that the ProjectedFrom nodes match the roles
                # covered by the constraint.
                pass
            else:
                raise JoinPathException(unsupported_node(child, node[0])) 

        return join_path

    def _load_join_path(self, node, join_path, root_role = None):
        """ Load <RolePath> or <SubPath> node of a <JoinRule> into join_path.
            `node` must point to a <RolePath> or <Subpath> node.  If root_role
            is not None, then the first role of paths along this branch will 
            join with root_role (which must be on a previous branch of 
            Join_path).  Returns first role on this branch of the path. """

        # We do not support negated splits
        split_neg = node.get("SplitIsNegated")
        if split_neg and split_neg.upper() == "TRUE":
            raise JoinPathException("has a negated path split")    

        # We do not support subpath combinations other than AND
        split_op = node.get("SplitCombinationOperator")
        if split_op and split_op.upper() != "AND":
            msg = "combines paths with an operator other than AND"
            raise JoinPathException(msg)                           

        first = None

        for child in node:
            if local_tag(child) == 'RootObjectType':
                # NOTE: I am ignoring this node for now, because it is not
                # needed to determine the join path structure.  The only reason
                # to check this node would be to confirm there is no "Negated" 
                # or "ValueRestriction" attribute.
                pass
            elif local_tag(child) == 'PathedRoles': # Linear Path
                # The root_role for any sub paths that follow this linear path
                # is the last role on the linear path.
                first, root_role = self._load_linear_path(child, join_path, root_role)  
            elif local_tag(child) == 'SubPaths': # Branching
                _first = self._load_branches(child, join_path, root_role)
                first = first or _first # Don't overwrite first if not None
            else:
                raise JoinPathException(unsupported_node(child, node))      

        return first           

    def _load_branches(self, node, join_path, root_role=None):
        """ Load <SubPaths> node of a <JoinRule> into join_path. Returns first
            role along any subpath. """

        first = None

        for child in node:
            if local_tag(child) == 'SubPath':
                _first = self._load_join_path(child, join_path, root_role)
                first = first or _first # Ensure we keep the very first role

                # If root_role is None, then subsequent subpaths join with 
                # the first role of the first subpath.
                root_role = root_role or first
            else:
                raise JoinPathException(unsupported_node(child, node))  
          
        return first

    def _load_linear_path(self, node, join_path, prev_role = None):
        """ Load <PathedRoles> node of a <JoinRule> into join_path. If prev_role
            is not None, joins the first role of this linear path with 
            prev_role.  Returns the first and last roles along this path. """

        first_role = None # First role of this branch of the join path

        for child in node:
            if local_tag(child) != 'PathedRole':
                raise JoinPathException(unsupported_node(child, node))         

            purpose = child.get("Purpose")
            isnegated = child.get("IsNegated")

            ref = child.get("ref")
            role = self._elements.get(ref)

            if role == None:
                raise JoinPathException("includes an implicit role")           
            elif len(child) != 0:
                raise JoinPathException(unsupported_node(child[0], child))     
            elif purpose == "PostOuterJoin":
                raise JoinPathException("includes an outer join")              
            elif isnegated and isnegated.upper()=="TRUE":
                raise JoinPathException("includes a negated role")             

            # On the first iteration, prev_role is either a role passed by the 
            # caller (i.e. from an earlier branch of the join path) or None.
            # On subsequent iterations, it is the previous role on this branch.
            if purpose == 'PostInnerJoin' and prev_role != None:               
                join_path.add_join(prev_role, role)

            if first_role == None: # First role in the path
                first_role = role

            prev_role = role  

        return first_role, prev_role # Permits joining with subsequent branches.              

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

def unsupported_node(node, parent):
    """ I use this error string multiple times. """
    template = "has a {1} node with an unsupported child node: {0}"
    return template.format(local_tag(node), local_tag(parent))
