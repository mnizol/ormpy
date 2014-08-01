##############################################################################
# Package: ormpy
# File:    orm_model.py
# Author:  Matthew Nizol
##############################################################################

""" This module is part of the ormpy package.  It provides a model class to
store an ORM model consisting of a set of domains, a set of predicates, and
a set of constraints.  It also provides an instance class to store instances
of ORM models.
"""

import random
import uuid

##############################################################################
# Domain Class
##############################################################################
class domain:
    """ A domain identifies a set of elements of a particular data type.  
        A domain may either be an enumerated list of legal values, or a range
        of legal numeric values.
    """

    def __init__(self, name="", id="", enum=[], min=-float('inf'), max=float('inf')):
        """ Initialize a domain object.  

            Parameters:
                name: The name of the domain
                id:   A unique identifier (defaults to a new UUID)
                enum: An enumerated list of legal values
                min:  Minimum legal value (ignored if enum is populated)
                max:  Maximum legal value (ignored if enum is populated)
        """
        self.name = name
        self.id = id.strip() or str(uuid.uuid4())
        self.enum = enum

        if self.enum:
            self.min = None
            self.max = None
        else: 
            self.min = min
            self.max = max

    def randval(self):
        """ Returns a random value from the domain. """
        if self.enum: 
            return self.enum[random.randint(0, len(self.enum)-1)]
        else: 
            return random.randint(self.min, self.max)

    def newval(self, domain_pop):
        """ Returns a legal value not in a population of this domain. """
        value = None

        if self.enum: # Enumerated population
            candidates = set(self.enum) - domain_pop
            if len(candidates) > 0: value = candidates.pop()
        elif len(domain_pop) > 0: # Numeric, non-empty population
            maxval = max(domain_pop)
            if maxval < self.max: value = maxval + 1
        else: # Numeric, empty population
            value = self.min

        return value

    def display(self):
        """ Displays the name of the domain. """
        print " ", self.name


##############################################################################
# Role Class
##############################################################################
class role:
    """ A role is the smallest unit of a predicate.  Each role in a predicate
        is played by objects of a single domain.
    """
 
    def __init__(self, predicate, position, roledef):
        """ Initialize the role.

            Parameters:
            predicate: Predicate object that this role is part of.
            position:  Integer position (0..arity) of role in predicate.
            roledef:   Dictionary object defining role.  Must have a key 
                       "domain" whose value is the role's domain.  Optional
                       keys include "name" and "id"
        """
        self.predicate = predicate
        self.position = position
        self.domain = roledef["domain"]
        self.name = roledef.get("name")
        self.id = roledef.get("id")

        if self.name is None: self.name = self.domain.name + str(position)
        if self.id is None: self.id = str(uuid.uuid4())

    def todict(self):
        """ Format the role as a dictionary for display. """
        return {self.name: self.domain.name}

    def pop(self, model_inst):
        """ Return population of objects playing role in model instance. """
        return set([fact[0] for fact in rolesequence([self]).project(model_inst)])

    def newval(self, model_inst):
        """ Get a legal value not already playing role in a model instance.
            First, select an unused element from the domain population. 
            Otherwise, select a legal value from domain that is not in the population.
            If neither is possible, return a random value already playing that role.
        """ 
        rolepop = self.pop(model_inst)
        dompop = model_inst.domain_pop(self.domain.name)

        unused = dompop - rolepop

        if len(unused) > 0: 
            value = unused.pop()
        else: # Everything in domain population used.  Extend domain.
            value = self.domain.newval(dompop)
            if value is None: value = self.domain.randval() 

        return value
    

##############################################################################
# Role Sequence
##############################################################################
class rolesequence(list): # Inherits list
    def __init__(self, roles=[]):
        list.extend(self, roles)
        self.indices = []
        self.predicate = self[0].predicate

        for role in self:
            if role.predicate != self.predicate:
                raise Exception("Join paths are not implemented yet")
            else:
                self.indices.append(role.position)

    # Get instance of role sequence from instance of model
    def instance(self, inst):
        the_set = inst.facts[self.predicate.name]
        zipped = zip(*the_set)
        
        if len(zipped) > 0:
            return zip(*[zipped[i] for i in self.indices])
        else:
            return []
 
    # Get projection of role sequence from instance of model
    def project(self, inst):
        return set(self.instance(inst))

    # Role names for display
    def names(self):
        names = []
        for role in self:
            names.append(role.name + " of " + role.predicate.name)
        return names                 

##############################################################################
# Predicate
##############################################################################
class predicate(list): # Inherits list
    """ A predicate is a fact type in an ORM model.  Implemented as a named 
        list of roles.
    """  
    def __init__(self, name="", id="", roles=[]):
        """ Initialize the predicate object.
            Each element in roles[] should be a dictionary
            For example: predicate("Teacher has Student", 
            [{"name": "Teacher", "domain": Person}, {"name": "Student", "domain": Person}])
        """
        self.name = name
        self.arity = len(roles)
        self.id = id.strip() or str(uuid.uuid4())

        for i in range(self.arity):
            list.append(self, role(self, i, roles[i]))
 
    def display(self):
        """ Display the predicate """
        print " "*2, self.name, map(role.todict, self)

##############################################################################
# Constraint
##############################################################################
class constraint(object):
    """ A constraint restricts the valid population of an object or fact type.
        This class is an abstract class to be inherited by more 
        specific constraint classes such as uniqueness and mandatory.
    """

    def __init__(self, name="", roles=[]):
        self.kind = ""
        self.name = name
        self.rolesequence = rolesequence(roles) # Covered roles

    def predicates(self):
        return [self.rolesequence.predicate] # TODO: Assumes no join paths

    def display(self):
        print " "*2, self.kind, " on roles ", self.rolesequence.names()

##############################################################################
# Uniqueness Constraint
##############################################################################
class unique(constraint):
    """ A uniqueness constraint requires that all tuples in the covered roles are unique.
    """

    def __init__(self, name="", roles=[]):
        super(unique, self).__init__(name=name, roles=roles)
        self.kind = "UC"

    def check(self, instance):
        """ Check whether the uniqueness constraint is satisifed on a given instance.
            Returns a value from 0 to 1 indicating the number of unique tuples in 
            the covered roles divided by the total number of tuples in the covered roles.
        """
        roleseq = self.rolesequence

        predname = roleseq[0].predicate.name
        roleinst = roleseq.project(instance)

        n = float(len(instance.facts[predname])) # Total number of covered values
        nuniq = float(len(roleinst))             # Number of unique covered values

        return n - nuniq  # Number of duplicates

    def repair(self, instance):
        return False
 
##############################################################################
# Mandatory Constraint
##############################################################################
class mandatory(constraint):
    """ A mandatory constraint requires that all elements in a domain play a role at least once.
    """

    def __init__(self, name="", roles=[]):
        super(mandatory, self).__init__(name=name, roles=roles)
        self.kind = "MC"
        self.domain = roles[0].domain

        if len(roles) != 1:
            raise Exception("Mandatory constraint operates on a single role")

    def __sets(self, instance):
        """ Internal logic shared by check() and repair().  Not intended to be called by a user.
            Returns the set of common elements between the role and its domain, the total
            set of elements from the domain, and the elements in the domain that are not in the role.
        """
        roleinst = self.rolesequence.project(instance)

        rvals = set(fact[0] for fact in roleinst)  # Set of unique values playing this role
        dvals = instance.objects[self.domain.name] # Set of unique values in domain
 
        common  = rvals & dvals  # values in common
        total   = rvals | dvals  # values in total
        missing = dvals - rvals  # values missing

        return common, total, missing

    def check(self, instance):
        """ Checks whether the mandatory constraint is satisfied on the covered role.  Returns
            the number of unique elements playing the role divided by the number of elements
            in the domain of the role.
        """
        common, total, missing = self.__sets(instance)

        return float(len(missing))  # 0.0 if valid

    def repair(self, instance):
        """ Repairs a violated mandatory constraint by adding tuples to the affected predicate
            until the mandatory constraint is satisfied.
        """
        position = self.rolesequence[0].position
        predname = self.rolesequence[0].predicate.name

        common, total, missing = self.__sets(instance)

        for val in missing:
            # TODO: Code duplicated with random_pop
            newfact = []
            for role in self.rolesequence[0].predicate:
                newfact.append(role.newval(instance)) # Try to get unique new value for this rol
            newfact[position] = val
            instance.add_fact(predname, tuple(newfact))

        return len(missing) > 0 # Whether a repair was needed

##############################################################################
# Set-based Constraints (Supertype of Exclusion, Subset, Equality, XOR)
##############################################################################
class setconstraint(constraint):
    """ Class setconstraint is an abstract class intend to be inherited by
        specific set-based constraint implementations (e.g. subset)
    """
    def __init__(self, name="", roles=[], roles2=[]):
        super(setconstraint, self).__init__(name=name, roles=roles)
        self.rolesequence2 = rolesequence(roles2)         
      
    def predicates(self):
        return [self.rolesequence.predicate, self.rolesequence2.predicate] # TODO: Assumes no join paths
  
    def display(self):
        print " "*2, self.kind, " from roles ", self.rolesequence.names(), " to roles ", self.rolesequence2.names()

##############################################################################
# Exclusion Constraint
##############################################################################
class exclusion(setconstraint):
    """ An exclusion constraint requires that the population of two sets of roles is disjoint. """

    def __init__(self, name="", roles=[], roles2=[]):
        super(exclusion, self).__init__(name=name, roles=roles, roles2=roles2)
        self.kind = "EX"
        
    def check(self, instance):
        """ Return the proportion of tuples covered by the constraint that satisfy the constraint. """
        roleinst1 = self.rolesequence.project(instance)
        roleinst2 = self.rolesequence2.project(instance)

        return float(len(roleinst1 & roleinst2)) # Number of values in common

    def repair(self, instance):
        """ Remove tuples that violate the constraint. """
        roleinst1 = self.rolesequence.project(instance)
        roleinst2 = self.rolesequence2.project(instance)
        
        common = roleinst1 & roleinst2

        predname = self.rolesequence.predicate.name
        indices = self.rolesequence.indices

        facts = instance.facts[predname]

        remove = []

        for fact in facts:
            if tuple(fact[i] for i in indices) in common: 
                remove.append(fact)
           
        for fact in remove:
            facts.remove(fact)
            #return 1 # Testing...

        return len(remove) > 0

##############################################################################
# Subset Constraint
##############################################################################
class subset(setconstraint):
    """ A subset constraint requires that the population of one set of roles
        is a subset of the population of another set of roles. """

    def __init__(self, name="", roles=[], roles2=[]):
        super(subset, self).__init__(name=name, roles=roles, roles2=roles2)
        self.kind = "SB"
        
    def check(self, instance):
        """ Return the proportion of tuples covered by the constrain that satisfy the constraint. """
        roleinst1 = self.rolesequence.project(instance)
        roleinst2 = self.rolesequence2.project(instance)

        return float(len(roleinst1 - roleinst2)) # Number of bad values in subset role

    def repair(self, instance):  # TODO: Very similar to exclusion repair -- refactor?
        """ Delete tuples that violate the constraint. """

        roleinst1 = self.rolesequence.project(instance)
        roleinst2 = self.rolesequence2.project(instance)
        
        diff = roleinst1 - roleinst2

        predname = self.rolesequence.predicate.name
        indices = self.rolesequence.indices

        facts = instance.facts[predname]

        remove = []

        for fact in facts:
            if tuple(fact[i] for i in indices) in diff: 
                remove.append(fact)
           
        for fact in remove:
            facts.remove(fact)
            #return 1 # TESTING....

        return len(remove) > 0

##############################################################################
# Model class
##############################################################################
class model(object):
    """ The model class is the ORMPY internal representation of an ORM model.
        It consists of a dictionary of domains (object types), a dictionary
        of predicates (fact types), and a list of constraints.
    """

    def __init__(self):
        self.domains = {}
        self.predicates = {}
        self.constraints = []

    # Add predicate to model
    def add_pred(self, predicate):
        if predicate.name not in self.predicates:
            self.predicates[predicate.name] = predicate       
            for role in predicate:
                self.add_dom(role.domain)
                 
    # Add new domain to model
    def add_dom(self, domain):
        if domain.name not in self.domains:
            self.domains[domain.name] = domain

    # Add new constraint to model
    def add_cons(self, constraint):
        self.constraints.append(constraint)

    # Display model
    def display(self):
        print "Domains:"
        map(domain.display, self.domains.values())            

        print "Predicates:"        
        map(predicate.display, self.predicates.values())            

        print "Constraints:"
        for cons in self.constraints:
            cons.display() # Otherwise top-level display() is called
            # map(constraint.display, self.constraints)
            
            
##############################################################################
# Instance class
##############################################################################
class instance(object):
    """ The instance class stores a population of a model. It consists of
        a reference to the model, a population of object types, and a 
        population of fact types.
    """

    # Initialize the instance
    def __init__(self, model):
        self.model = model
        self.objects = {key: set() for key in model.domains.keys()} 
        self.facts = {key: set() for key in model.predicates.keys()} 

    # Testing 1.2.3
    def rebuild_objects(self):
        result = {key: set() for key in self.model.domains.keys()}

        for predname in self.facts:
            predicate = self.model.predicates[predname]
            arity = predicate.arity

            for fact in self.facts[predname]:                
                for i in range(arity):
                    domain = predicate[i].domain.name                    
                    result[domain].add(fact[i])

        self.objects = result

    # Add fact to a predicate
    def add_fact(self, predicate, fact):
        target = self.model.predicates[predicate]
        for i in range(min(target.arity, len(fact))):
            self.objects[target[i].domain.name].add(fact[i])
        self.facts[predicate].add(fact)

    # Generate a population of random facts for a predicate
    def random_pop(self, predicate, max_size):
        for i in range(random.randint(1, max_size)): 
            fact = [role.domain.randval() for role in predicate]
            self.add_fact(predicate.name, tuple(fact))

    # Domain population
    def domain_pop(self, name):
        return self.objects[name]

    # Display the instance
    def display(self):
        print "Objects:"

        objlist = self.objects.keys()
        objlist.sort()

        for name in objlist:
            values = list(self.objects[name])
            values.sort()           
            print " "*2, name, values

        print "Facts:" 
         
        factlist = self.facts.keys()
        factlist.sort()
       
        for name in factlist:
            values = list(self.facts[name])
            values.sort()
            print " "*2, name, ":", [role.domain.name for role in self.model.predicates[name]]

            for value in values:
                print " "*4, value
    
    
