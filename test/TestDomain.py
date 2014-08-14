##############################################################################
# Package: ormpy
# File:    TestDomain.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Domain module. """

from unittest import TestCase

import lib.Domain as Domain

import sys
from datetime import date, time, datetime

class TestDomain(TestCase):
    """ Unit tests for the Domain module. """

    def setUp(self):
        pass

    def test_empty_domain(self):
        """ Test an empty domain. """
        actual = Domain.IntegerDomain(0)
        expected = []
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 0)

    '''
    Commented out because it takes almost a second to run.
    def test_full_domain(self):
        """ Test an exceeded domain. """
        actual = Domain.IntegerDomain(sys.maxsize + 1)
        expected = range(sys.maxsize)
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, actual.max_size)
    '''

    def test_int_domain(self):
        """ Test an IntegerDomain. """
        actual = Domain.IntegerDomain(8)
        expected = [0, 1, 2, 3, 4, 5, 6, 7]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 8)
        self.assertEquals(actual.max_size, sys.maxsize)

    def test_float_domain(self):
        """ Test a FloatDomain. """
        actual = Domain.FloatDomain(12)
        expected = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 12)
        self.assertEquals(actual.max_size, sys.maxsize)

    def test_bool_domain_full(self):
        """ Test a complete BoolDomain. """
        actual = Domain.BoolDomain()
        expected = [False, True]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 2)
        self.assertEquals(actual.max_size, 2)

    def test_bool_domain_partial(self):
        """ Test a partial BoolDomain. """
        actual = Domain.BoolDomain(1)
        expected = [False]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 1)
        self.assertEquals(actual.max_size, 2)

    def test_string_domain_no_prefix(self):
        """ Test a StrDomain with no prefix. """
        actual = Domain.StrDomain(5)
        expected = ['0', '1', '2', '3', '4']
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 5)
        self.assertEquals(actual.max_size, sys.maxsize)

    def test_string_domain_prefix(self):
        """ Test a StrDomain with a prefix. """
        actual = Domain.StrDomain(4, prefix='Test')
        expected = ['Test0', 'Test1', 'Test2', 'Test3']
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 4)

    def test_date_domain_default(self):
        """ Test a DateDomain with default start date."""
        actual = Domain.DateDomain(3)
        expected = [date(2000,1,1), date(2000,1,2), date(2000,1,3)]
        self.assertItemsEqual(actual, expected)

    def test_date_domain(self):
        """ Test a DateDomain with a provided start date."""
        actual = Domain.DateDomain(3, start=date(1961,2,28))
        expected = [date(1961,2,28), date(1961,3,1), date(1961,3,2)]
        self.assertItemsEqual(actual, expected)

        diff = (date(9999,12,31) - date(1961,2,28)).total_seconds()
        diff = int(diff) / (60*60*24)
        self.assertEqual(actual.max_size, diff + 1)

    def test_date_overflow(self):
        """ Confirm date domain does not overflow. """
        actual = Domain.DateDomain(100, start=date(9999,12,30))
        expected = [date(9999,12,30), date(9999,12,31)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 2)
        self.assertEquals(actual.max_size, 2)

    def test_time_domain_default(self):
        """ Test a TimeDomain with default start time. """
        actual = Domain.TimeDomain(3)
        expected = [time(0, 0), time(0, 1), time(0, 2)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 3)
        self.assertEquals(actual.max_size, 60*24)

    def test_time_domain(self):
        """ Test a TimeDomain with provided start time. """
        actual = Domain.TimeDomain(4, start=time(11,58))
        expected = [time(11, 58), time(11, 59), time(12, 0), time(12, 1)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 4)
        # Minutes from 11:58am to 11:59pm
        self.assertEquals(actual.max_size, 60*24/2+2) 

    def test_time_overflow(self):
        """ Confirm that TimeDomain does not overflow. """
        actual = Domain.TimeDomain(400, start=time(23,58))
        expected = [time(23, 58), time(23, 59)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 2)
        # Minutes from 11:58pm to 11:59pm
        self.assertEquals(actual.max_size, 2)

    def test_datetime_domain_default(self):
        """ Test a DateTimeDomain with default start time. """
        actual = Domain.DateTimeDomain(3)
        expected = [datetime(2000, 1, 1, 0, 0), 
                    datetime(2000, 1, 1, 0, 1), 
                    datetime(2000, 1, 1, 0, 2)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 3)

    def test_datetime_domain(self):
        """ Test a DateTimeDomain with provided start time. """
        actual = Domain.DateTimeDomain(3, start=datetime(1999,12,31,23,58))
        expected = [datetime(1999,12,31,23,58),
                    datetime(1999,12,31,23,59),
                    datetime(2000, 1, 1, 0, 0)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 3)

    def test_datetime_domain_overflow(self):
        """ Confirm a DateTimeDomain does not overflow. """
        actual = Domain.DateTimeDomain(300, start=datetime(9999,12,31,23,58))
        expected = [datetime(9999,12,31,23,58),
                    datetime(9999,12,31,23,59)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(actual.size, 2)
        self.assertEquals(actual.max_size, 2)



    


          

