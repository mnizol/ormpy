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
        actual = Domain.IntegerDomain().draw(0)
        expected = []
        self.assertItemsEqual(actual, expected)

    def test_full_domain(self):
        """ Test an exceeded domain. """
        actual = Domain.BoolDomain().draw(20)
        expected = [False, True]
        self.assertItemsEqual(actual, expected)

    def test_int_domain(self):
        """ Test an IntegerDomain. """
        domain = Domain.IntegerDomain()
        actual = domain.draw(8)
        expected = [0, 1, 2, 3, 4, 5, 6, 7]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, sys.maxsize)

    def test_float_domain(self):
        """ Test a FloatDomain. """
        domain = Domain.FloatDomain()
        actual = domain.draw(12)
        expected = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, sys.maxsize)

    def test_bool_domain_full(self):
        """ Test a complete BoolDomain. """
        domain = Domain.BoolDomain()
        actual = domain.draw(2)
        expected = [False, True]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, 2)

    def test_bool_domain_partial(self):
        """ Test a partial BoolDomain. """
        actual = Domain.BoolDomain().draw(1)
        expected = [False]
        self.assertItemsEqual(actual, expected)

    def test_string_domain_no_prefix(self):
        """ Test a StringDomain with no prefix. """
        domain = Domain.StringDomain()
        actual = domain.draw(5)
        expected = ['0', '1', '2', '3', '4']
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, sys.maxsize)

    def test_string_domain_prefix(self):
        """ Test a StringDomain with a prefix. """
        actual = Domain.StringDomain(prefix='Test').draw(4)
        expected = ['Test0', 'Test1', 'Test2', 'Test3']
        self.assertItemsEqual(actual, expected)

    def test_date_domain_default(self):
        """ Test a DateDomain with default start date."""
        actual = Domain.DateDomain().draw(3)
        expected = [date(2000,1,1), date(2000,1,2), date(2000,1,3)]
        self.assertItemsEqual(actual, expected)

    def test_date_domain(self):
        """ Test a DateDomain with a provided start date."""
        domain = Domain.DateDomain(start=date(1961,2,28))
        actual = domain.draw(3)
        expected = [date(1961,2,28), date(1961,3,1), date(1961,3,2)]
        self.assertItemsEqual(actual, expected)

        diff = (date(9999,12,31) - date(1961,2,28)).total_seconds()
        diff = int(diff) / (60*60*24)
        self.assertEqual(domain.max_size, diff + 1)

    def test_date_overflow(self):
        """ Confirm date domain does not overflow. """
        domain = Domain.DateDomain(start=date(9999,12,30))
        actual = domain.draw(100)
        expected = [date(9999,12,30), date(9999,12,31)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, 2)

    def test_time_domain_default(self):
        """ Test a TimeDomain with default start time. """
        domain = Domain.TimeDomain()
        actual = domain.draw(3)
        expected = [time(0, 0), time(0, 1), time(0, 2)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, 60*24)

    def test_time_domain(self):
        """ Test a TimeDomain with provided start time. """
        domain = Domain.TimeDomain(start=time(11,58))
        actual = domain.draw(4)
        expected = [time(11, 58), time(11, 59), time(12, 0), time(12, 1)]
        self.assertItemsEqual(actual, expected)

        # Minutes from 11:58am to 11:59pm
        self.assertEquals(domain.max_size, 60*24/2+2) 

    def test_time_overflow(self):
        """ Confirm that TimeDomain does not overflow. """
        domain = Domain.TimeDomain(start=time(23,58))
        actual = domain.draw(400)
        expected = [time(23, 58), time(23, 59)]
        self.assertItemsEqual(actual, expected)

        # Minutes from 11:58pm to 11:59pm
        self.assertEquals(domain.max_size, 2)

    def test_datetime_domain_default(self):
        """ Test a DateTimeDomain with default start time. """
        actual = Domain.DateTimeDomain().draw(3)
        expected = [datetime(2000, 1, 1, 0, 0), 
                    datetime(2000, 1, 1, 0, 1), 
                    datetime(2000, 1, 1, 0, 2)]
        self.assertItemsEqual(actual, expected)

    def test_datetime_domain(self):
        """ Test a DateTimeDomain with provided start time. """
        actual = Domain.DateTimeDomain(start=datetime(1999,12,31,23,58)).draw(3)
        expected = [datetime(1999,12,31,23,58),
                    datetime(1999,12,31,23,59),
                    datetime(2000, 1, 1, 0, 0)]
        self.assertItemsEqual(actual, expected)

    def test_datetime_domain_overflow(self):
        """ Confirm a DateTimeDomain does not overflow. """
        domain = Domain.DateTimeDomain(start=datetime(9999,12,31,23,58))
        actual = domain.draw(300)
        expected = [datetime(9999,12,31,23,58),
                    datetime(9999,12,31,23,59)]
        self.assertItemsEqual(actual, expected)
        self.assertEquals(domain.max_size, 2)

    def test_not_implemented_exception(self):
        """ Just for 100% coverage, confirm not implemented exception raised 
            on Domain class's _generate function. """
        domain = Domain.Domain()
        with self.assertRaises(NotImplementedError) as ex:
            g = domain._generate(10) 

    def test_forced_stop_iteration(self):
        """ Just for 100% coverage, force a StopIteration exception within
            Domain.draw(). """
        domain = Domain.Domain(max_size = 100) 

        # Create custom _generate() function that can only produce 5 items 
        # despite max_size
        domain._generate = lambda n: (i for i in xrange(5))

        actual = domain.draw(7) # Should raise StopIteration exception within
                                # the for loop
        expected = [0, 1, 2, 3, 4]
        self.assertItemsEqual(actual, expected)

    def test_enumerated(self):
        """ Test EnumeratedDomain. """
        domain = Domain.EnumeratedDomain()

        self.assertItemsEqual(domain.draw(10), [])
        self.assertEquals(domain.max_size, 0)

        domain.add(5)
        domain.add(['a','b','c'])

        self.assertItemsEqual(domain.draw(0), [])
        self.assertEquals(domain.draw(4), [5,'a','b','c'])
        self.assertEquals(domain.max_size, 4)

        # Add element already in the domain
        domain.add('a')
        self.assertEquals(domain.draw(5), [5,'a','b','c'])

        # Add list with partial overlap
        domain.add([7,6,5])
        self.assertEquals(domain.draw(10), [5,'a','b','c',6,7])

        # Add list with full overlap
        domain.add(['a','b'])
        self.assertEquals(domain.draw(10), [5,'a','b','c',6,7])
        



