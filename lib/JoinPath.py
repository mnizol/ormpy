##############################################################################
# Package: ormpy
# File:    JoinPath.py
# Author:  Matthew Nizol
##############################################################################

""" The JoinPath module implements the JoinPath class and supporting classes."""

class JoinPath(object):
    """ A join path specifies the inner join of two or more fact types. """  

    def __init__(self):
        self._fact_types = list() #: List of fact types in join order
        self._joins = list() #: List of (Role, Role) join pairs

    @property
    def fact_types(self):
        """ The list of fact types along the join path, in join order. """
        return self._fact_types

    @property
    def joins(self):
        """ A list of (Role, Role) pairs in join order.  The i^th pair
            represents the join of the (i+1)^th fact type with some earlier 
            fact type in self.fact_types. """
        return self._joins

    def add_join(self, role1, role2):
        """ Extend the join path by joining role1 (which must be part of a 
            fact type already on the path) with role2. """
        
        # Validate the join
        if role1.player != role2.player:
            msg = "join roles must be played by the same object type"
            raise JoinPathException(msg)

        if len(self.fact_types) > 0 and role1.fact_type not in self.fact_types:
            msg = "first join role must already be on the join path"
            raise JoinPathException(msg)

        if role1.fact_type == role2.fact_type or role2.fact_type in self.fact_types:
            msg = "join would create a cycle in the join path"
            raise JoinPathException(msg)        

        # Join appears to be ok.  Let's extend the join path.
        if len(self.fact_types) == 0:
            self._fact_types = [role1.fact_type]

        self._fact_types.append(role2.fact_type)
        self._joins.append( (role1, role2) )

    def materialize(self):
        """ Executes the joins along the join path and returns the resulting
            join fact type.  """
        raise NotImplementedError()

class JoinPathException(Exception):
    """ Raised when defining or loading a join path with an unsupported 
        feature. """
    pass
