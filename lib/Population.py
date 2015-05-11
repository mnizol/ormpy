##############################################################################
# Package: ormpy
# File:    Population.py
# Author:  Matthew Nizol
##############################################################################

""" Module to generate a population of an ORMMinusModel. """

import sys
import os
import fractions

import lib.FactType as FactType
from lib.ORMMinusModel import ORMMinusModel
from lib.Constraint import FrequencyConstraint
from lib.SubtypeGraph import SubtypeGraph
from lib.Transformation import AbsorptionFactType

from itertools import cycle

class Population(object):
    """ A population of an ORMMinusModel. If the model is satisfiable, 
        then self.object_types and self.fact_types will contain the
        populations of objects and facts, respectively, that satisfy the
        constraints in the model.  For an unsatisfiable model, 
        Popuation() will raise a ValueError exception."""

    def __init__(self, model):
        super(Population, self).__init__()
        self._model = model

        #: A dictionary of object type populations.  Specifically, the key is
        #: the object type name and the value is a list of objects.
        self.object_types = {}  

        #: A dictionary of fact type populations.  Specifically, the key is the
        #: fact type name and the value is a :class:`lib.Population.Relation`.
        self.fact_types = {} 

        # A dictionary of role populations (i.e. unary relations)
        self._roles = {}                          

        # Generate the population
        if model.solution == None:
            raise ValueError("Cannot populate an unsatisfiable model.")
        else:
            self._populate_object_types_and_roles()
            self._populate_role_sequences()
            self._populate_fact_types()

    def _populate_object_types_and_roles(self):
        """ Populate all object types and roles in the model. """

        graph = SubtypeGraph(self._model.base_model)

        for obj_type in self._model.object_types:
            name = obj_type.fullname
            n = self._model.solution[name] 

            # Get the domain of this object type's root type (note that the root
            # of a primitive type is itself).  In ValueConstraintTransformation,
            # we ensured that by drawing the first n elements from the root 
            # type's domain, a subtype's population will be a subset of any of
            # its supertypes' populations.
            domain = graph.root_of[obj_type].domain                       

            # Populate the object type from its root type's domain 
            self.object_types[name] = list(domain.draw(n))

            # Populate the root roles played by this object type
            self._populate_root_roles(obj_type)

        # Iterate over object types again to populate non-root roles. Populating 
        # root roles first ensures that root populations are available to 
        # non-root roles, even if played by a different (but compatible) type
        for obj_type in self._model.object_types:
            self._populate_non_root_roles(obj_type)

    def _populate_root_roles(self, obj_type):
        """ Populate all root roles played by an object type. """
        
        # Create an iterator that will cycle over all objects in the object
        # type's domain in an endless loop.
        obj_name = obj_type.fullname
        obj_cycle = cycle(self.object_types[obj_name])

        # Get lists of root roles.  For non-experimental case (i.e. McGill), 
        # root_roles should equal obj_type.roles.
        root_roles = [r for r in obj_type.roles if is_root_role(r)]

        # Populate each root role by drawing the next N elements from obj_cycle, 
        # where N is the value of the role variable in the solution.
        for role in root_roles:
            name = role.fullname
            size = self._model.solution[name]
            pop = Relation([role.name]) # Create an empty population

            for i in xrange(size):
                next = obj_cycle.next()
                pop.add([next])

            self._roles[name] = pop

    def _populate_non_root_roles(self, obj_type):
        """ Populate non-root roles with first N elements of root role's pop."""

        non_root_roles = [r for r in obj_type.roles if not is_root_role(r)]

        for role in non_root_roles:
            name = role.fullname
            size = self._model.solution[name]
            try:
                pop = self._roles[role.root_role.fullname].first(size)
            except KeyError:
                raise Exception("Cannot find root role for " + name)
            self._roles[name] = pop
       
    def _populate_role_sequences(self):
        """ Populate all role sequences covered by an internal frequency 
            constraint.  """
    
        for cons in self._model.constraints.of_type(FrequencyConstraint):
            name = cons.fullname

            # Upstream logic in ORMMinusModel already ignored overlapping and 
            # external frequency constraints, so we can confirm the constraint
            # represents a valid role sequence by checking whether there is 
            # an associated variable in the solution.
            if name in self._model.solution:
                size = self._model.solution[name] 
                parts = cons.covers                 
                pop = self._combine_partial_pops(name, size, parts)
                self._roles[name] = pop

    def _populate_fact_types(self):
        """ Populate all fact types in the model by combining populations of
            fact type parts. """

        for fact_type in self._model.fact_types:
            name = fact_type.fullname
            size = self._model.solution[name]
            parts = self._model.get_parts(fact_type)            
            pop = self._combine_partial_pops(name, size, parts)

            if isinstance(fact_type, AbsorptionFactType):
                self._split_absorption_pop(fact_type, pop)
            else:                
                self.fact_types[name] = pop

    def _combine_partial_pops(self, name, size, parts):
        """ Combine populations of elements in parts list to create a combined
            population of a given size. """
        
        pop = Relation([])                
        for part in parts:
            next_pop = self._roles[part.fullname]
            pop = pop.combine_with(next_pop, size)
        return pop

    def _split_absorption_pop(self, fact_type, pop):
        """ Split the population of an AbsorptionFactType into populations of 
            the original fact types. """
        
        # Pre-condition: role names in fact_type are unique
        assert len(set(pop.names)) == len(pop.names), "Role names not unique"

        # Population of root role of absorption 
        root_pop = self._roles[fact_type.root_role.fullname]

        # Get a list of projections on each role of pop
        projections = zip(*pop) 

        # Combine each non-root role population with the root role population
        for i in range(pop.arity):
            role_name = pop.names[i]
            if role_name == fact_type.root_role.name:
                continue

            role_pop = Relation(names=[role_name])
            role_pop.extend([[x] for x in projections[i]])

            assert len(root_pop) == len(role_pop), "Unexpected population size"

            fact_pop = root_pop.combine_with(role_pop, len(root_pop))
            fact_name = fact_type.fact_type_names[role_name]
            self.fact_types[fact_name] = fact_pop               

    def _write_objects(self, name, stream):
        """ Write the populate of an object type to a file stream. """
        for obj in self.object_types[name]:
            stream.write(str(obj) + '\n')

    def _write_facts(self, name, stream):
        """ Write the population of a fact type to a file stream. """
        pop = self.fact_types[name]
        stream.write(','.join(pop.names) + "\n")
        for fact in pop:
            stream.write(','.join(map(str, fact)) + "\n")

    def write_csv(self, dirname):
        """ Write the entire population to CSV files stored in a directory 
            (one file per object type or fact type).  """   

        # Create directory if it doesn't exist 
        # See http://stackoverflow.com/a/14364249
        try: 
            os.makedirs(dirname)
        except OSError:
            if not os.path.isdir(dirname): raise

        # Write object type and fact type populations, one per file.
        for name in self.object_types:
            filename = os.path.join(dirname, name + ".csv")
            with open(filename, 'w') as out:                        
                self._write_objects(name, out)
                
        for name in self.fact_types:
            filename = os.path.join(dirname, name + ".csv")
            with open(filename, 'w') as out:
                self._write_facts(name, out)

    def write_stdout(self):
        """ Writes entire population to stdout. """
        for name in self.object_types:
            sys.stdout.write("Population of " + name + ":\n")
            self._write_objects(name, sys.stdout)
            print

        for name in self.fact_types:
            sys.stdout.write("Population of " + name + ":\n")
            self._write_facts(name, sys.stdout)
            print

class Relation(list):
    """ A relation, which is a list of lists of identical arity. """
    
    def __init__(self, names=[]):
        super(Relation, self).__init__()
        self.names = names #: List of names of each column in the relation
        self.arity = len(names) #: Number of columns in the relation

    def add(self, tupl):
        """ Add tuple to the list. The ordering of elements in the tuple
            is assumed to match the order of self.names. """
        if len(tupl) == self.arity:
            self.append(tupl)
        else:
            raise Exception("Cannot add tuple of arity " + str(len(tupl)) +
                            " to a Relation of arity " + str(self.arity))

    def first(self, n):
        """ Return a new Relation containing first n elements of this one. """
        result = Relation(names=list(self.names))
        result.extend(self[:n])
        return result
        
    def combine_with(self, target, n):
        """ Combine self with a target relation according to the enumeration 
            algorithm of Smaragdakis, et al. """

        # Special case: if either relation is nullary, treat this as a no-op
        # and just return the other relation.
        if self.arity == 0: return target
        elif target.arity == 0: return self

        # Normal case
        result = Relation(self.names + target.names)

        s = len(self)
        t = len(target)

        i_s, i_t = 0, 0

        for i in xrange(min(n, s * t)):
            result.add(self[i_s] + target[i_t])

            i_s = (i_s + 1) % s
            i_t = (i_t + 1) % t

            if (i+1) % lcm(s, t) == 0:
                i_t = (i_t + 1) % t

        return result

########################################################################
# Utility functions
########################################################################
def lcm(a,b):
    """ Return the least common multiple of a and b. """
    # Credit: http://rosettacode.org/wiki/Least_common_multiple#Python. 
    return abs(a * b) / fractions.gcd(a,b) if a and b else 0
            
def is_root_role(role):
    """ Returns True if role is a root role. """
    return not hasattr(role, "root_role") # Always True if not experimental



