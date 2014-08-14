##############################################################################
# Package: ormpy
# File:    Domain.py
# Author:  Matthew Nizol
##############################################################################

""" The Domain.py module implements the domains that underly value types. 
    More specifically, classes in the module provide a means to generate
    a set of values conforming to a particular data type.  For example, ::

        my_int = IntegerDomain(10)

    will produce a set containing the first 10 unsigned integers.  """

MAX_SIZE = 1000000 # Essentially arbitrary.  Set well below sys.maxsize.

import datetime # For constants
from datetime import date, time, timedelta # Do not include datetime class

class Domain(set):
    """ A domain, which is a set of values conforming to a data type. """
    
    def __init__(self, size, max_size = MAX_SIZE):
        """ Initialize the domain. """
        self.max_size = min(max_size, MAX_SIZE)
        self.size = min(size, self.max_size)

class IntegerDomain(Domain):
    """ An integer domain containing the first <size> unsigned integers. """
    
    def __init__(self, size):
        """ Initialize the set with the first <size> unsigned integers. """
        super(IntegerDomain, self).__init__(size)
        set.__init__(self, range(0, self.size))
        

class FloatDomain(Domain):
    """ A floating point domain.  Only contains floating point numbers 
        in increments of 0.1 (e.g. 0.1, 0.2, 0.3, etc.).  """

    def __init__(self, size):
        """ Initialize. """
        super(FloatDomain, self).__init__(size)
        values = [float(i) / 10.0 for i in xrange(self.size)]
        set.__init__(self, values)

class BoolDomain(Domain):
    """ A domain for boolean (True/False) values. """

    def __init__(self, size = 2):
        """ Initialize. """
        super(BoolDomain, self).__init__(size, max_size = 2)
        values = [False, True]
        set.__init__(self, values[:self.size])

class StrDomain(Domain):
    """ A domain for string values. The constructor includes a prefix
        parameter.  Generated strings are of the form 'prefix<n>' 
        where <n> is a monotonically increasing unsigned integer. """
    
    def __init__(self, size, prefix=""):
        """ Initialize. """
        super(StrDomain, self).__init__(size)
        values = [prefix + str(i) for i in xrange(self.size)]
        set.__init__(self, values)

class DateDomain(Domain):
    """ A domain for date values.  Generated dates start on <start>
        which defaults to January 1, 2000."""

    def __init__(self, size, start=date(2000,01,01)):
        """ Initialize. """
        max_days = (date(datetime.MAXYEAR, 12, 31) - start).days + 1
        super(DateDomain, self).__init__(size, max_size = max_days)
        values = [start + timedelta(i) for i in xrange(self.size)]
        set.__init__(self, values)

class TimeDomain(Domain):
    """ A domain for time values.  Generated times start at <start>
        which defaults to midnight and increment by minutes. """

    def __init__(self, size, start=time()):
        """ Initialize. """
        start = datetime.datetime.combine(date.today(), start)
        stop  = datetime.datetime.combine(date.today(), time(23,59))
        max_mins = int((stop - start).total_seconds()/60) + 1
        super(TimeDomain, self).__init__(size, max_size = max_mins)
        values = [(start + timedelta(minutes=i)).time() for i in xrange(self.size)]
        set.__init__(self, values) 

class DateTimeDomain(Domain):
    """ A domain for datetime values.  Generated datetimes start on <start>
        which defaults to January 1, 2000 at midnight and increment by
        minutes."""

    def __init__(self, size, start=datetime.datetime(2000,01,01)):
        """ Initialize. """
        max_dt = datetime.datetime(datetime.MAXYEAR, 12, 31, 23, 59)
        max_mins = int((max_dt - start).total_seconds()/60) + 1
        super(DateTimeDomain, self).__init__(size, max_size = max_mins)
        values = [start + timedelta(minutes=i) for i in xrange(self.size)]
        set.__init__(self, values)      
        
    
