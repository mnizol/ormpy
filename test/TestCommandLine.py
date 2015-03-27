##############################################################################
# Package: ormpy
# File:    TestCommandLine.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.CommandLine module. """

from unittest import TestCase

import lib.CommandLine as CommandLine
import lib.TestDataLocator as TestDataLocator
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
        self.assertEquals(args.filename, "test.orm")

        args = CommandLine.parse_args(["-dp", "-o /home", "test.orm"])

        self.assertFalse(args.quiet)
        self.assertFalse(args.verbose)
        self.assertTrue(args.debug)
        self.assertFalse(args.check_model)
        self.assertTrue(args.populate)
        self.assertEquals(args.ubound, 10)
        self.assertEquals(args.directory, " /home")

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
        model = CommandLine.import_model(path)

        self.assertEquals(model.object_types.count(), 1)
        self.assertIsNotNone(model.object_types.get("A"))
        self.assertEquals(model.fact_types.count(), 0)
        self.assertEquals(model.constraints.count(), 0)

    def test_import_fail(self):
        """ Test failed import of a model. """
        self.log.beforeTest(None)
        logging.getLogger().setLevel(logging.WARNING) # Don't want stack trace

        path = os.path.join(self.data_dir, "does_not_exist.orm")
        
        with self.assertRaises(SystemExit) as ex:
            model = CommandLine.import_model(path)

        self.assertItemsEqual(self.log.formatLogRecords(), 
            ["ERROR: Could not load does_not_exist.orm: [Errno 2] No such file or directory: '" + path + "'"])
        self.log.afterTest(None)

    def test_check_unsat(self):
        """ Test checking unsatisfiable model."""
        path = os.path.join(self.data_dir, "unsat_smarag_1.orm")
        args = CommandLine.parse_args(["-cu 10", path])
        model = CommandLine.import_model(path)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model is unsatisfiable.\n")
        restore_stdout()

    def test_check_sat(self):
        """ Test checking a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-cu 1", path])
        model = CommandLine.import_model(path)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Model is satisfiable.\n")
        restore_stdout()

    def test_populate_sat(self):
        """ Test populating a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        args = CommandLine.parse_args(["-pu 1", path])
        model = CommandLine.import_model(path)

        capture_stdout()
        CommandLine.check_or_populate(model, args)        
        self.assertEquals(read_stdout(), "Population of ObjectTypes.A:\n0\n\n")
        restore_stdout()

    def test_populate_sat_write_to_bad_dir(self):
        """ Test populating a satisfiable model. """
        path = os.path.join(self.data_dir, "no_fact_types.orm")
        bad = os.path.join(self.data_dir, "..", "output", "NOT_A_DIRECTORY")

        args = CommandLine.parse_args(["-pu 1", "-o", bad, path])
        model = CommandLine.import_model(path)

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

        model = CommandLine.import_model(path)        

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


##############################################################################
# Utility functions
##############################################################################
def capture_stdout():
    sys.stdout = StringIO()

def restore_stdout():
    sys.stdout = STDOUT # STDOUT is a global defined at the top of the module

def read_stdout():
    return sys.stdout.getvalue()
