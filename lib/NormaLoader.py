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

    NormaLoader intentionally ignores much of the .orm file structure when
    loading the file into a :class:`lib.Model.Model` object (much of the .orm
    file is not relevant to the analyses performed by ORMPY).  All information
    outside of the <orm:ORMModel> element is ignored, which includes things
    like diagram (shape) data and extensions.  NormaLoader also ignores the 
    following (not necessarily exhaustive) list of items:

    * Sample (instance) data
    * Implicit elements not explicitly modeled by the modeler
    * Model errors reported by NORMA
    * Informal model notes
    * Multiple readings for a fact type
    * Derivation rules for subtypes, fact types, and roles
    * Constraints outside the scope of ORM-- or its extensions

    A list of important model elements (such as derivations 
    and constraints) that are ignored by NormaLoader is contained in the
    *omissions* attribute after loading the input file.
"""

from lib.Model import Model
import lib.ObjectType as ObjectType

import xml.etree.cElementTree as xml

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
        """ Initialize object and load *filename*.
        """
        
        # Public attributes

        #: The ORM model (:class:`lib.Model.Model`) loaded from the .orm file.
        self.model = Model() 

        #: List of items in the .orm file omitted by the NormaLoader
        self.omissions = []  

        # Private attributes

        # NORMA namespace constants.  If the .ORM file is based on updated
        # namespaces, we will not load it.
        self._ns_root = "{http://schemas.neumont.edu/ORM/2006-04/ORMRoot}"
        self._ns_core = "{http://schemas.neumont.edu/ORM/2006-04/ORMCore}"

        self._elements = {}   # Dictionary of {id, element} pairs 
    
        self._loader = {}
        self._boolean = {}
        self._build_mappings()

        self._load(filename)
    
    ###########################################################################
    # Private Utility Functions
    ###########################################################################
    def _build_mappings(self):
        """ Build mappings used by instances of the class.
        """
        # Mapping from XML element tag to loader functions
        self._loader = {
            'Objects' : self._load_elements,
            'EntityType' : self._load_entity_type,
            'ValueType'  : self._load_value_type,
            'ObjectifiedType' : self._load_objectified_type,
            'NestedPredicate' : self._load_nested_fact_type,
            'SubtypeDerivationRule' : self._load_subtype_derivation,
            'PreferredIdentifier' : self._load_preffered_identifier
        }

        self._boolean = {
            'true' : True,
            'false' : False,
             None: None
        }


    def _load(self, filename):
        """ Loads the .orm file named *filename* into *self.model* """
        root = self._parse_norma_file(filename)
        self._load_elements(root, self.model)


    def _parse_norma_file(self, filename):
        """ Parse a NORMA File and return the ORMModel element. """
        if filename.split(".")[-1].upper() != "ORM":
            raise Exception("Input filename must have .orm extension.")

        tree = xml.parse(filename)
        root = tree.getroot()

        if root.tag != self._ns_root + "ORM2":
            raise Exception("Root of input file must be <ormRoot:ORM2>.")

        model_node = root.find(self._ns_core + "ORMModel")

        if model_node is None:
            raise Exception("Cannot find <orm:ORMModel> in input file.")
        else:
            return model_node

    def _load_elements(self, parent, target):
        """ Call the loader function associated with each child element of the 
            *parent* element.  *target* is the object into which the XML data
            will be loaded.
        """
        for child in parent:
            tag = self._local_tag(child)
        
            try:
                self._loader[tag](child, target)
            except KeyError:
                pass # No loading function defined.


    def _local_tag(self, element):
        """ Strips namespace from tag element. """
        return element.tag.replace(self._ns_core, "")

    ##########################################################################
    # Private Functions to Load Object Types
    ##########################################################################
    def _load_entity_type(self, element, target):
        """ Loads an entity type rooted at node *element* """
        entity_type = ObjectType.EntityType()
        self._load_object_type(element, entity_type)

    def _load_value_type(self, element, target):
        """ Loads a value type rooted at node *element* """
        value_type = ObjectType.ValueType()
        self._load_object_type(element, value_type)

    def _load_objectified_type(self, element, target):
        """ Loads an objectified type rooted at node *element* """
        objectified_type = ObjectType.ObjectifiedType()
        self._load_object_type(element, objectified_type)

    def _load_object_type(self, element, object_type):
        """ Loads object type rooted at node *element* into *object_type*. """ 
        # Basic attributes
        object_type._id = element.get("id")
        object_type.name = element.get("Name").replace(" ", "_")
        object_type.independent = self._boolean[element.get("IsIndependent")]

        if element.get("IsImplicitBooleanValue") != "true": # Skip if implicit
            self._load_elements(element, object_type)
            if object_type._id:  # Will be None if element should be skipped
                self.model.add(object_type)
                self._elements[object_type._id] = object_type

    def _load_nested_fact_type(self, element, object_type):
        """ Loads NestedPredicate element into object_type. """
        if element.get("IsImplied") == "true":  # Skip implied object types
            object_type._id = None 
        else: # Store GUID of nested fact type
            object_type.nested_fact_type = element.get("ref")  

    def _load_subtype_derivation(self, element, object_type):
        """ Loads SubtypeDerivationRule into object_type. """
        self.omissions.append("Subtype derivation rule for " + object_type.name)

    def _load_preffered_identifier(self, element, object_type):
        """ Loads PreferredIdentifier into object_type. """
        object_type.identifier = element.get("ref")  # GUID for uniq constraint
        
        '''
        # Data Type
        node = self._find(element, "ConceptualDataType")
        if datatype_element:
            datatype_ref = datatype_element.get("ref")  # GUID for data type
            datatype_scale = datatype_element.get("Scale")
            datatype_length = datatype_element.get("Length")

        # Check for value constraints
        # NOTE: Only handling string lists.  Need to update for min+max range
        enum = []
        for item in element.iter(self.namespace + "ValueRange"):
            enum.append(item.get("MinValue"))

         # Create domain object
        domain = orm.domain(id = id, name = name, enum = enum, 
                            min = 0, max = self.maxint)

        # Load domain into model and element dictionary
        self.model.domains[name] = domain
        self.elements[id] = domain
        '''

'''
    def load_predicate(self, element):
        type = self.localTag(element)

        if type != "Fact": # Ignoring ImpliedFact, at least
            return #raise Exception("Unexpected predicate type: " + type)

        # Create FactType
        name = element.get("_Name")
        id = element.get("id")

        # Get roles        
        rolelist = []

        for role in self.find(element, "FactRoles"):
            if self.localTag(role) == "Role":
                domid = self.find(role, "RolePlayer").get("ref")

                roledict = {} # New dictionary every iteration
                roledict["domain"] = self.elements[domid]
                roledict["id"] = role.get("id")
                roledict["name"] = role.get("name")
                
                rolelist.append(roledict)
 
        # Create predicate
        predicate = orm.predicate(name = name, id = id, roles = rolelist)
        self.model.predicates[name] = predicate
        self.elements[id] = predicate

        # Add roles to element dictionary [cannot do until predicate creates role objects]
        for role in predicate:
            self.elements[role.id] = role       


    def load_constraint(self, element):
        type = self.localTag(element)
        id = element.get("id")

        # Skip if implied
        if element.get("IsImplied") == "true":
            return

        roles = []
        i = 0

        for roleseq in element.iter(self.namespace + "RoleSequence"):
            roles.append([])
            for role in roleseq:
                if self.localTag(role) == "Role":
                    id = role.get("ref")

                    if id not in self.elements: # NOTE: Confirm only implied roles can be missing from self.elements
                        return # Constrains implied roles

                    roles[i].append(self.elements[id])
            i += 1

        if type == "UniquenessConstraint":
            cons = orm.unique(roles = roles[0]) 
        elif type == "MandatoryConstraint":
            cons = orm.mandatory(roles = roles[0])
        elif type == "SubsetConstraint":
            cons = orm.subset(roles = roles[0], roles2 = roles[1])
        elif type == "ExclusionConstraint":
            cons = orm.exclusion(roles = roles[0], roles2 = roles[1])
        else:
            raise Exception("Unexpected constraint type: " + type)

        self.model.constraints.append(cons)



'''

        


