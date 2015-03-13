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
from lib.ORMMinus import ORMMinus
from lib.Population import Population

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
    parser.add_argument('-c', '--check-model', action='store_true',
        dest='check_model', default=False, help='check if model is satisfiable')
    parser.add_argument('-p', '--populate', action='store_true',
        dest='populate', default=False, help='populate the model')
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
        print "Some items were ignored when loading " + args.filename + ":"
        for omission in loader.omissions:
            print " "*3, omission
        print

    if args.print_model:
        loader.model.display()

    if args.check_model:
        ormminus = ORMMinus(model=loader.model)
        solution = ormminus.check()

        if not args.quiet and len(ormminus.ignored) > 0:
            print "Some constraints were ignored while checking the model:"
            for cons in ormminus.ignored:
                print " "*3, cons.name
            print

        if solution == None:
            print "Model is unsatisfiable."
        else:
            print "Model is satisfiable."  

    # TODO: Need to print omissions.  Don't want to be redundant with
    #       check_model code above---should Populate take a solution as a 
    #       parameter instead of computing solution in one step?
    # TODO: Accept size parameter.
    # TODO: Accept destination parameter.
    if args.populate:
        pop = Population(model=loader.model)
        pop.write_stdout()    
        



