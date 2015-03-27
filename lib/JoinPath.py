##############################################################################
# Package: ormpy
# File:    JoinPath.py
# Author:  Matthew Nizol
##############################################################################

""" The JoinPath module implements the JoinPath class and supporting classes."""

class JoinPath(object):
    """ A join path specifies the inner join of two or more fact types. """  

    def __init__(self, init_role):
        self.path = list()
        
        # TODO: initialize with init_role.

    def extend(self, role1, role2):
        """ Extend the join path by joining role1 (which should be part of a 
            fact type already on the path) with role2. """
        raise NotImplementedError()

    def materialize(self):
        """ Executes the joins along the join path and returns the resulting
            join fact type.  The join fact type will be covered by 
            copies of the same kinds of constraints that cover the fact types
            along the path.  """
        raise NotImplementedError()

class Join(object):
    """ A join is a tuple of roles on which two fact types will be joined.
        The roles must be played by compatible object types. """

    def __init__(self, role1, role2):
        self.roles = (role1, role2)

        # TODO: Do I confirm that roles are compatible here?  Would actually
        #       need to have a way to check that role.player and role2.player
        #       share common supertype.
        # TODO: Would also then want to confirm that roles are from diff
        #       fact types.
        

