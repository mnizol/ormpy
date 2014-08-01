##############################################################################
# Package: ormpy
# File:    norma_loader.py
# Author:  Matthew Nizol
##############################################################################

""" Module for importing .orm files produced by the NORMA modeling tool
"""

import orm_model as orm
import xml.etree.cElementTree as xml

##############################################################################
# Norma_Loader Class
##############################################################################
class norma_loader:
    """ Loads a .orm file produced by the NORMA modeling tool into an orm_model.model class.
    """
    def __init__(self, filename=None):
        """ Initialize loader object; can optionally pass the *filename* of the .orm file to load 
        """
        # NORMA namespace constants.  If the .ORM file is based on updated
        # namespaces, we will not load it.
        self.NS_ROOT = "{http://schemas.neumont.edu/ORM/2006-04/ORMRoot}"
        self.NS_CORE = "{http://schemas.neumont.edu/ORM/2006-04/ORMCore}"

        self.elements = {}  # Dictionary of {id, element} pairs from the .ORM file
        self.model = orm.model() # Create a new ORMPY model

        if filename:
            self.load(filename)


    def load(self, filename):
        """ Loads the .orm file named *filename* into *self.model* (of class *orm_model.model*)
        """
        root = self.parse_norma_file(filename) # Load and confirm this is a .ORM file
     
        # Add object types
        for object_type in self.find(root, "Objects"):
            self.load_object_type(object_type)

        '''
        # Add facts
        for factType in self.find(root, "Facts"):
            self.load_predicate(factType)

        # Add constraints
        for cons in self.find(root, "Constraints"):
            try:
                self.load_constraint(cons)
            except Exception as e:
                print "Failed (", str(e), "): ", cons.get("Name")

        '''

 
    def parse_norma_file(self, filename):
        """ Parse a NORMA File (*filename*) and return the ORMModel node as an :class:`xml.etree.Element`
        """
        if filename.split(".")[-1].upper() != "ORM":
            raise Exception("Input filename must have .orm extension.")

        tree = xml.parse(filename)

        root = tree.getroot()

        if root.tag != self.NS_ROOT + "ORM2":
            raise Exception("Root element of input file must be <ormRoot:ORM2>.")

        model_node = root.find(self.NS_CORE + "ORMModel")

        if model_node is None:
            raise Exception("Cannot find <orm:ORMModel> element in input file.")
        else:
            return model_node


    def load_object_type(self, element):
        """ Loads an object type rooted at node *element* of the :class:`xml.etree.ElementTree` created by :func:`parse_norma_file`
            into a new object_type in the object_type list *self.model.object_types*.
        """
        type = self.localTag(element)
        
        if type not in ["EntityType", "ValueType", "ObjectifiedType"]: 
            raise Exception("Unexpected object type: " + type) 

        id = element.get("id")
        name = element.get("Name").replace(" ", "_")

        # Check for value constraints
        # TODO: Only handling string lists.  Need to update for min+max range
        enum = []
        for item in element.iter(self.namespace + "ValueRange"):
            enum.append(item.get("MinValue"))

        # Skip if implied
        nested = self.find(element, "NestedPredicate")
        if nested is not None and nested.get("IsImplied") == "true":
            return

        # Create domain object
        domain = orm.domain(id = id, name = name, enum = enum, min = 0, max = self.maxint)

        # Load domain into model and element dictionary
        self.model.domains[name] = domain
        self.elements[id] = domain

    '''
    Load Predicate from NORMA File
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

    '''
    Load Constraint from NORMA File
    '''
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

                    if id not in self.elements: # TODO: Confirm only implied roles can be missing from self.elements
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
    Wrapper functions to strip namespace
    '''
    def find(self, element, tag):
        return element.find(self.namespace + tag)

    def localTag(self, element):
        return element.tag.replace(self.namespace, "")



        


