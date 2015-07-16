##############################################################################
# Package: ormpy
# File:    TestCommandLine.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.CommandLine module. """
from __future__ import print_function

from unittest import TestCase

import lib.CommandLine as CommandLine
import lib.TestDataLocator as TestDataLocator
from lib.Population import Population
from lib.ORMMinusModel import ORMMinusModel
from lib.Constraint import CardinalityConstraint

from nose.plugins.logcapture import LogCapture

import sys
import os
import logging
from StringIO import StringIO

STDOUT = sys.stdout

class TestCommandLine(TestCase):
    """ Unit tests for the CommandLine module. """

    def setUp(self):
        self.data_dir = TestDataLocator.get_data_dir()

        # Log capturing
        self.log = LogCapture()
        self.log.logformat = '%(levelname)s: %(message)s'
        self.log.begin()

    def test_arg_parse(self):
        """ Test argument parsing. """
        args = CommandLine.parse_args(["-qc", "-u 200", "test.orm"])

        self.assertTrue(args.quiet)
        self.assertFalse(args.verbose)
        self.assertFalse(args.debug)
        self.assertTrue(args.check_model)
        self.assertFalse(args.populate)
        self.assertEquals(args.ubound, 200)
        self.assertFalse(args.deontic)
        self.assertEquals(args.filename, "test.orm")

        args = CommandLine.parse_args(["-dp", "-o /home", "test.orm"])

        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
        self.assertTrue(args.debug)
        self.assertFalse(args.check_model)
        self.assertTrue(args.populate)
        self.assertEquals(args.ubound, 10)
        self.assertEquals(args.directory, " /home")

        args = CommandLine.parse_args(["--include-deontic", "test.orm"])
        self.assertTrue(args.deontic)
        self.assertFalse(args.experimental)

        args = CommandLine.parse_args(["--experimental", "test.orm"])
        self.assertTrue(args.experimental)
        self.assertEquals(args.generator, 'csv')

        args = CommandLine.parse_args(["-p", "--output-type", "logiql", "test.orm"])
        self.assertEquals(args.generator, 'logiql')

        args = CommandLine.parse_args(["-p", "test.orm"])
        self.assertEquals(args.random, False)

        args = CommandLine.parse_args(["-p", "--random-bounds", "test.orm"])
        self.assertEquals(args.random, True)
        self.assertEquals(args.custom_size_file, None)

        args = CommandLine.parse_args(["-p", "--custom-size-file", "/dev/null", "test.orm"])
        self.assertEquals(args.random, False)
        self.assertEquals(args.custom_size_file, "/dev/null")


    def test_log_config(self):
        """ Test configuration of the logger. """
        root = logging.getLogger()

        args = CommandLine.parse_args(["-q", "test"])
        CommandLine.configure_logger(args)
        self.assertEquals(root.getEffectiveLevel(), logging.ERROR)

        args = CommandLine.parse_args(["test"])
        CommandLine.configure_logger(args)
        self.assertEquals(root.getEffectiveLevel(), logging.WARNING)

        args = CommandLine.parse_args(["-v", "test"])
        CommandLine.configure_logger(args)
        self.assertEquals(root.getEffectiveLevel(), logging.INFO)

        args = CommandLine.parse_args(["-d", "test"])
        CommandLine.configure_logger(args)
        self.assertEquals(root.getEffectiveLevel(), logging.DEBUG)

    def test_import_model(self):
        """ Test successful import of a small model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-cu 10", path])
        model = CommandLine.import_model(path, args)

        self.assertEquals(model.object_types.count(), 1)
        self.assertIsNotNone(model.object_types.get("A"))
        self.assertEquals(model.fact_types.count(), 0)
        self.assertEquals(model.constraints.count(), 0)

    def test_import_fail(self):
        """ Test failed import of a model. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "does_not_exist.orm")
        args = CommandLine.parse_args(["-cu 10", path])

        with self.assertRaises(SystemExit) as ex:
            model = CommandLine.import_model(path, args)

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Could not load does_not_exist.orm: [Errno 2] No such file or directory: '" + path + "'"])
        self.log.afterTest(None)

    def test_custom_size_file_not_found(self):
        """ Test failed loading of custom size file. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "empty_model.orm")
        dne = os.path.join(self.data_dir, "non_existent_size_file")
        args = CommandLine.parse_args(["-cu 10", "--custom-size-file", dne, path])

        model = CommandLine.import_model(path, args)

        with self.assertRaises(SystemExit) as ex:
            CommandLine.apply_custom_size_file(model, args.custom_size_file, args.ubound)    

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Could not load " + dne + ": [Errno 2] No such file or directory: '" + dne + "'"])
        self.log.afterTest(None)

    def test_custom_size_bad_line(self):
        """ Test failed loading of custom size file due to bad line. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "simple_model.orm")
        size = os.path.join(self.data_dir, "custom_size_bad_line.txt")
        args = CommandLine.parse_args(["-cu 10", "--custom-size-file", size, path])

        model = CommandLine.import_model(path, args)

        with self.assertRaises(SystemExit) as ex:
            CommandLine.apply_custom_size_file(model, args.custom_size_file, args.ubound)    

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Could not load " + size + ": bad line is not in the model. Try using full element name."])
        self.log.afterTest(None)

    def test_custom_size_bad_cardinality(self):
        """ Test failed loading of custom size file due to bad cardinality. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "simple_model.orm")
        size = os.path.join(self.data_dir, "custom_size_bad_cardinality.txt")
        args = CommandLine.parse_args(["-cu 10", "--custom-size-file", size, path])

        model = CommandLine.import_model(path, args)

        with self.assertRaises(SystemExit) as ex:
            CommandLine.apply_custom_size_file(model, args.custom_size_file, args.ubound)    

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Could not load " + size + ": ObjectTypes.A cannot have non-integer cardinality."])
        self.log.afterTest(None)

    def test_custom_bounds(self):
        """ Test application of custom bounds. """
        path = os.path.join(self.data_dir, "simple_model.orm")
        size = os.path.join(self.data_dir, "custom_size.txt")
        args = CommandLine.parse_args(["-cu 10", "--custom-size-file", size, path])
        model = CommandLine.import_model(path, args)

        self.assertEquals(len(model.constraints.of_type(CardinalityConstraint)), 0)

        CommandLine.apply_custom_size_file(model, args.custom_size_file, args.ubound)

        sizes = [c.ranges[0].upper for c in model.constraints.of_type(CardinalityConstraint)]

        self.assertEquals(len(sizes), 4)
        self.assertItemsEqual(sizes, [3,10,8,4]) # The cardinality of 25 is truncated to ubound of 10

        pop = Population(ORMMinusModel(model, ubound=args.ubound))

        self.assertEquals(len(pop.object_types["ObjectTypes.A"]), 10)
        self.assertEquals(len(pop.object_types["ObjectTypes.B"]), 3)
        self.assertEquals(len(pop.object_types["ObjectTypes.C"]), 10)

        self.assertEquals(len(pop.fact_types["FactTypes.BHasC"]), 4)
        self.assertEquals(len(pop.fact_types["FactTypes.ALikesB"]), 10)
        self.assertEquals(len(pop.fact_types["FactTypes.AHasB"]), 8)

    def test_random_bounds(self):
        """ Test application of random bounds. """
        path = os.path.join(self.data_dir, "simple_model.orm")
        args = CommandLine.parse_args(["-cu 10", path])
        model = CommandLine.import_model(path, args)

        self.assertEquals(len(model.constraints.of_type(CardinalityConstraint)), 0)

        CommandLine.apply_random_sizes(model, args.ubound, seed=0)

        sizes = [c.ranges[0].upper for c in model.constraints.of_type(CardinalityConstraint)]

        self.assertEquals(len(sizes), 6)
        self.assertItemsEqual(sizes, [9,8,5,3,6,5])

        pop = Population(ORMMinusModel(model))

        self.assertEquals(len(pop.object_types["ObjectTypes.A"]), 9)
        self.assertEquals(len(pop.object_types["ObjectTypes.B"]), 5)
        self.assertEquals(len(pop.object_types["ObjectTypes.C"]), 8)

        self.assertEquals(len(pop.fact_types["FactTypes.BHasC"]), 3)
        self.assertEquals(len(pop.fact_types["FactTypes.ALikesB"]), 6)
        self.assertEquals(len(pop.fact_types["FactTypes.AHasB"]), 5)

    def test_check_unsat(self):
        """ Test checking unsatisfiable model."""
        path = os.path.join(self.data_dir, "unsat_smarag_1.orm")
        args = CommandLine.parse_args(["-cu 10", path])
        model = CommandLine.import_model(path, args)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model is unsatisfiable.\n")
        restore_stdout()

    def test_check_unsat_strengthened(self):
        """ Test checking unsatisfiable strengthened model."""
        path = os.path.join(self.data_dir, "disjunctive_reference_scheme_unsat.orm")
        args = CommandLine.parse_args(["-cu 10", "--experimental", path])
        model = CommandLine.import_model(path, args)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model satisfiability cannot be determined.\n")
        restore_stdout()

    def test_check_sat(self):
        """ Test checking a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-cu 1", path])
        model = CommandLine.import_model(path, args)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model is satisfiable.\n")
        restore_stdout()

    def test_populate_sat(self):
        """ Test populating a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-pu 1", path])
        model = CommandLine.import_model(path, args)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Population of ObjectTypes.A:\n0\n\n")
        restore_stdout()

    def test_populate_sat_write_to_bad_dir(self):
        """ Test populating a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        bad = os.path.join(self.data_dir, "..", "output", "NOT_A_DIRECTORY")

        args = CommandLine.parse_args(["-pu 1", "-o", bad, path])
        model = CommandLine.import_model(path, args)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model is satisfiable.\nCannot write population to " + bad + "\n")
        restore_stdout()

    def test_populate_exception(self):
        """ Test exception catching during population. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-pu 1", path]) # No -o option so we'll try to write to stdout
        sys.stdout = None # Force an exception when trying to write to stdout

        model = CommandLine.import_model(path, args)        

        with self.assertRaises(SystemExit) as ex:
            CommandLine.check_or_populate(model, args)                

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Failed to populate the model: 'NoneType' object has no attribute 'write'"])
        self.log.afterTest(None)
        restore_stdout()

    def test_execute_noop(self):
        """ Test execution without any action parameter. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        capture_stdout()
        CommandLine.execute([path])        
        self.assertEquals(read_stdout(), "")
        restore_stdout()

    def test_execute_print(self):
        """ Test execution with --print-model parameter. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        capture_stdout()
        CommandLine.execute(["-m", path])        
        self.assertEquals(read_stdout(), "Object Types:\n    A\nFact Types:\nConstraints:\n")
        restore_stdout()

    def test_execute_check(self):
        """ Test execution with --check-model parameter. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        capture_stdout()
        CommandLine.execute(["-c", path])        
        self.assertEquals(read_stdout(), "Model is satisfiable.\n")
        restore_stdout()

    def test_execute_print_and_check(self):
        """ Test execution with --print-model and --check-model parameter. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        capture_stdout()
        CommandLine.execute(["--check-model", "--print-model", path])        
        self.assertEquals(read_stdout(), "Object Types:\n    A\nFact Types:\nConstraints:\nModel is satisfiable.\n")
        restore_stdout()

    def test_select_generator(self):
        """ Test that different generator functions are correctly called. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-pu 1", "-o", "/tmp", path])
        model = CommandLine.import_model(path, args)

        # Add a dummy function to the GENERATOR dictionary
        args.generator = 'dummy'
        CommandLine.GENERATOR['dummy'] = lambda m, p, d: print("Dummy generator was called for directory " + d)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Dummy generator was called for directory /tmp\n")
        restore_stdout() 

    def test_confirm_original_model_passed_to_generator(self):
        """ Confirm the untransformed model is passed to the generator method."""
        path = os.path.join(self.data_dir, "join_rule_valid_linear_path_euc.orm")

        # Important: need --experimental so that EUC strenghtening is applied
        args = CommandLine.parse_args(["-p", "-o", "/tmp", "--experimental", path])
        model = CommandLine.import_model(path, args)

        # Hijack the generator function
        args.generator = 'dummy'
        template = "Original: {0}, Transformed: {1}"
        CommandLine.GENERATOR['dummy'] = lambda m, p, d: \
            print(template.format(str(m.constraints.get("EUC") is not None), 
                                  str(p._model.constraints.get("EUC") is not None)))

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Original: True, Transformed: False\n")
        restore_stdout()

##############################################################################
# Utility functions
##############################################################################
def capture_stdout():
    sys.stdout = StringIO()

def restore_stdout():
    sys.stdout = STDOUT # STDOUT is a global defined at the top of the module

def read_stdout():
    return sys.stdout.getvalue()
