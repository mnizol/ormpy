##############################################################################
# Package: ormpy
# File:    CSV.py
# Author:  Matthew Nizol
##############################################################################

""" This module provides a class to generate a directory of CSV files from an 
    OrmPy Population object.
"""

import os

class CSV(object):
    """ Generate a directory of CSV files from an OrmPy Population. """

    def __init__(self, model=None, population=None, dirname=None, *args, **kwargs):
        super(CSV, self).__init__(*args, **kwargs)
        population.write_csv(dirname)
