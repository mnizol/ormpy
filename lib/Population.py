##############################################################################
# Package: ormpy
# File:    Population.py
# Author:  Matthew Nizol
##############################################################################

""" Module to generate a population of an ORM model. """

import sys
import csv
import fractions

import lib.FactType as FactType
from lib.ORMMinus import ORMMinus
from lib.Constraint import FrequencyConstraint
from itertools import cycle

class Population(object):
    """ A population of an ORM model. If the model is satisfiable, 
        then self.object_types and self.fact_types will contain the
        populations of objects and facts, respectively, that satisfy the
        constraints in the model.  For an unsatisfiable model, 
        self.object_types and self.fact_types will both be None."""

    DEFAULT_SIZE = 15 #: Default size of object and fact type populations.

    def __init__(self, model, ubound=DEFAULT_SIZE):
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
        self.populate(ubound=ubound)

    def populate(self, ubound=DEFAULT_SIZE):
        """ Generate a population for the model. """
        ormminus = ORMMinus(self._model, ubound=ubound)
        solution = ormminus.check()

        if solution == None:
            self.object_types = None
            self.fact_types = None
        else:
            self._populate_object_types_and_roles(solution)
            self._populate_role_sequences(solution)
            self._populate_fact_types(solution, ormminus)

    def _populate_object_types_and_roles(self, solution):
        """ Populate all object types and roles in the model. """

        for obj_type in self._model.object_types:
            name = obj_type.fullname
            domain = obj_type.domain
            size = solution[name]            

            # Populate the object type from its domain 
            self.object_types[name] = list(domain.draw(size))

            # Populate the roles played by this object type
            self._populate_roles(solution, obj_type)

    def _populate_roles(self, solution, obj_type):
        """ Populate all roles played by an object type. """
        
        # Create an iterator that will cycle over all objects in the object
        # type's domain in an endless loop.
        obj_name = obj_type.fullname
        obj_cycle = cycle(self.object_types[obj_name])

        # Populate each role by drawing the next <size> elements from obj_cycle, 
        # where <size> is the value of the role variable in the solution.
        for role in obj_type.roles:
            name = role.fullname
            size = solution[name]
            pop = Relation([role.name]) # Create an empty population

            for i in xrange(size):
                next = obj_cycle.next()
                pop.add([next])

            self._roles[name] = pop
       
    def _populate_role_sequences(self, solution):
        """ Populate all role sequences covered by an internal frequency 
            constraint.  """
    
        for cons in self._model.constraints.of_type(FrequencyConstraint):
            name = cons.fullname

            # Upstream logic in ORMMinus already ignored overlapping and 
            # external frequency constraints, so we can confirm the constraint
            # represents a valid role sequence by checking whether there is 
            # an associated variable in the solution.
            if name in solution:
                size = solution[name] 
                parts = cons.covers                 
                pop = self._combine_partial_pops(name, size, parts)
                self._roles[name] = pop

    def _populate_fact_types(self, solution, ormminus):
        """ Populate all fact types in the model by combining populations of
            fact type parts. """

        for fact_type in self._model.fact_types:
            name = fact_type.fullname
            size = solution[name]
            parts = ormminus.get_parts(fact_type)            
            pop = self._combine_partial_pops(name, size, parts)
            self.fact_types[name] = pop

    def _combine_partial_pops(self, name, size, parts):
        """ Combine populations of elements in parts list to create a combined
            population of a given size. """
        
        pop = Relation([])                
        for part in parts:
            next_pop = self._roles[part.fullname]
            pop = pop.combine_with(next_pop, size)
        return pop

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

    def write_csv(self, directory=None):
        """ Write the entire population to CSV files stored in a directory 
            (one file per object type or fact type).  """    
        if self.object_types == None: return

        for name in self.object_types:
            filename = os.path.join(directory, name)
            with open(filename, 'w') as out:                        
                self._write_objects(name, out)
                
        for name in self.fact_types:
            filename = os.path.join(directory, name)
            with open(filename, 'w') as out:
                self._write_facts(name, out)

    def write_stdout(self):
        """ Writes entire population to stdout. """
        if self.object_types == None: return

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
            



