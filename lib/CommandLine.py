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

from lib.NormaLoader import NormaLoader
from lib.ORMMinusModel import ORMMinusModel
from lib.Population import Population

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

    # Other parameters
    parser.add_argument('-u', '--upper-bound', type=int, 
        dest='ubound', default=10, help='upper bound on model element sizes')
    parser.add_argument('-o', '--output-dir', help='output directory',
        dest='directory', default='')
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

            if args.directory.strip() == '':
                pop.write_stdout()
            else:
                try:
                    pop.write_csv(args.directory.strip())
                except:
                    print "Model is satisfiable."
                    print "Cannot write population to " + args.directory
        else:
            print "Model is satisfiable."
    except Exception as exception:
        text = "populate" if args.populate else "check"
        logging.error("Failed to %s the model: %s", text, exception)
        logging.debug("Stack trace:", exc_info=sys.exc_info())
        sys.exit(2)        
