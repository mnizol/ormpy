##############################################################################
# File:        CommandLine.py
# Author:      Matthew Nizol
###############################################################################

""" This program contains the command line UI for the ORMPY program. """

###############################################################################
# Package Imports
###############################################################################
import sys
import argparse

from lib.NormaLoader import NormaLoader

###############################################################################
# Main function
###############################################################################
def execute():
    """ Command line entry point for ORMPY program. """

    # Parse Command Line
    parser = argparse.ArgumentParser(
        description='Object Role Modeling (ORM) Analysis Tool for Python')
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet', 
        default=False, help='suppress warning messages')
    parser.add_argument('-m', '--print-model', action='store_true', 
        dest='print_model', default=False, help='print model contents')        
    parser.add_argument('filename', type=str, help='File containing ORM model')
    args = parser.parse_args()

    # Import model from .ORM file
    try:
        loader = NormaLoader(args.filename)
    except Exception as exception:
        print "Could not load ", args.filename
        print exception
        sys.exit(2)

    if not args.quiet and len(loader.omissions) > 0:
        print "The following items were ignored when loading " + args.filename
        for omission in loader.omissions:
            print " "*2, omission

    if args.print_model:
        print
        loader.model.display()


