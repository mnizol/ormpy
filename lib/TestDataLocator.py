##############################################################################
# Package: ormpy
# File:    TestDataLocator.py
# Author:  Matthew Nizol
##############################################################################

""" Locates test data directory without resorting to environment variable. """

import os

def get_data_dir():
    """ Return test data directory.
        See http://stackoverflow.com/questions/2632199/how-do-i-get-the-path-of-
                  the-current-executed-file-in-python/2632297#2632297
    """
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, "test", "data")

