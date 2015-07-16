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
import logging
import os
import random

from lib.NormaLoader import NormaLoader
from lib.ORMMinusModel import ORMMinusModel
from lib.Population import Population
from lib.Constraint import CardinalityConstraint, CardinalityRange

import lib.generators.CSV as CSV
import lib.generators.LogiQL as LogiQL

GENERATOR = {'csv'   : CSV.CSV,
             'logiql': LogiQL.LogiQL}

###############################################################################
# Command line user interface
###############################################################################
def execute(arglist=None):
    """ Command line entry point for ORMPY program.  Use the arglist parameter
        to provide an argument list manually (i.e. not via sys.argv). """

    # Parse Command Line
    args = parse_args(arglist)
    
    # Configure the logger
    configure_logger(args)

    # Import model from .ORM file
    model = import_model(args.filename, args)

    # Modify size distribution if requested
    if args.random:
        apply_random_sizes(model, args.ubound)

    if args.custom_size_file:
        apply_custom_size_file(model, args.custom_size_file, args.ubound)    

    # Print the model, if requested
    if args.print_model:
        model.display()

    # Check and/or populate the model, if requested
    if args.check_model or args.populate:
        check_or_populate(model, args)

###############################################################################
# Subroutines
###############################################################################
def parse_args(arglist=None):
    """ Parse command line arguments and return an args object.  To provide
        an argument list manually (i.e. not from sys.argv), use the arglist
        parameter. """

    parser = argparse.ArgumentParser(
        description='Object Role Modeling (ORM) Analysis Tool for Python')

    # Message-level options
    parser.add_argument('-q', '--quiet', action='store_true', dest='quiet',
        default=False, help='suppress warning messages')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose',
        default=False, help='display all messages except debugging info')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug',
        default=False, help='display debugging messages (implies -v)')

    # Action options
    parser.add_argument('-m', '--print-model', action='store_true',
        dest='print_model', default=False, help='print model contents')
    parser.add_argument('-c', '--check-model', action='store_true',
        dest='check_model', default=False, help='check if model is satisfiable')
    parser.add_argument('-p', '--populate', action='store_true',
        dest='populate', default=False, help='populate the model')

    # Options related to upper bounds on element sizes
    parser.add_argument('-u', '--upper-bound', type=int, 
        dest='ubound', default=10, help='upper bound on model element sizes')
    parser.add_argument('--random-bounds', dest='random', action='store_true', 
        help='distribute upper bounds on element sizes randomly '
             '(subject to --upper-bound)', default=False)
    parser.add_argument('--custom-size-file', type=str, dest='custom_size_file', 
        help='name of file containing "ELEMENT_NAME, UPPER_BOUND" pairs '
             '(subject to --upper-bound)')

    # Output generation options
    parser.add_argument('--output-type', help='output type',
        dest='generator', default='csv', choices=['csv', 'logiql'])
    parser.add_argument('-o', '--output-dir', help='output directory',
        dest='directory', default='')

    # Other parameters
    parser.add_argument('--include-deontic', help='include deontic constraints',
        dest='deontic', action='store_true', default=False)
    parser.add_argument('--experimental', help='use experimental extensions',
        dest='experimental', action='store_true', default=False)

    # Filename to parse
    parser.add_argument('filename', type=str, help='File containing ORM model')

    return parser.parse_args(arglist)

def configure_logger(args):
    """ Configure the logger. """
    logging.basicConfig(format='%(levelname)s: %(message)s')

    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.INFO
    elif args.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.getLogger().setLevel(level)
    

def import_model(path, args):
    """ Import the request ORM model and return it. """
    try:
        loader = NormaLoader(path, deontic=args.deontic)
        return loader.model
    except Exception as exception:
        logging.error("Could not load %s: %s", 
                      os.path.basename(path), exception)
        logging.debug("Stack trace:", exc_info=sys.exc_info())
        sys.exit(2)

def apply_random_sizes(model, ubound, seed=None):
    """ Apply random size limits to the model elements (subject to ubound). """
    random.seed(seed)
    for element in list(model.object_types) + list(model.fact_types):
        ranges = [CardinalityRange(1, random.randint(1, ubound))]
        model.add(CardinalityConstraint(ranges, covers=[element]))

def apply_custom_size_file(model, filename, ubound):
    """ Apply custom size file to model element sizes (subject to ubound). """
    try:
        with open(filename, 'r') as in_file:
            for line in in_file:
                if line.strip() == "": continue
                split = [s.strip() for s in line.partition(",")]

                element = model.get(split[0])

                if element is None:
                    msg = "{0} is not in the model. Try using full element name." 
                    raise ValueError(msg.format(split[0]))
                    
                try:
                    size = min(int(split[2]), ubound)
                except ValueError:
                    msg = "{0} cannot have non-integer cardinality."
                    raise ValueError(msg.format(split[0]))

                ranges = [CardinalityRange(1, size)]
                model.add(CardinalityConstraint(ranges, covers=[element]))

    except Exception as exception:
        logging.error("Could not load %s: %s", filename, exception)
        logging.debug("Stack trace:", exc_info=sys.exc_info())
        sys.exit(2)        
        
def check_or_populate(model, args):
    """ Check or populate the model, as requested. """
    try:
        model = ORMMinusModel(model, max(1, args.ubound), 
                              experimental=args.experimental)

        if model.solution == None:
            if model.strengthened:
                print "Model satisfiability cannot be determined."
            else:
                print "Model is unsatisfiable."
        elif args.populate:
            pop = Population(model)
            dirname = args.directory.strip()

            if dirname == '':
                pop.write_stdout()
            else:
                try:
                    # Pass the original, untransformed model to the GENERATOR
                    original_model = import_model(args.filename, args)
                    GENERATOR[args.generator](original_model, pop, dirname)
                except:
                    print "Model is satisfiable."
                    print "Cannot write population to " + dirname
                    if args.debug: raise
        else:
            print "Model is satisfiable."
    except Exception as exception:
        text = "populate" if args.populate else "check"
        logging.error("Failed to %s the model: %s", text, exception)
        logging.debug("Stack trace:", exc_info=sys.exc_info())
        sys.exit(2)        
