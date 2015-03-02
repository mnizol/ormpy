##############################################################################
# Package: ormpy
# File:    Domain.py
# Author:  Matthew Nizol
##############################################################################

""" The Domain.py module implements the domains that underly types.
    More specifically, classes in the module provide a means to generate
    a set of values conforming to a particular data type.  For example: ::

        my_int = IntegerDomain()
        first10 = my_int.draw(10)

    The above code defines a domain of unsigned integers and then returns the 
    first 10 integers from that domain as a set.  """

import sys
import datetime # For constants
from datetime import date, time, timedelta # Do not include datetime class

class Domain(object):
    """ A domain, which can be used to generate a set of values conforming to a
        data type. """

    def __init__(self, max_size=sys.maxsize):
        super(Domain, self).__init__()

        #: Maximum number of elements permitted by the domain.  By default,
        #: the maximum is sys.maxsize.
        self.max_size = min(max_size, sys.maxsize) 

    def draw(self, n):
        """ Draw the first n elements from the domain and return as a list.  
            If n is larger than the number of elements in the domain,
            the entire domain is returned as a list. """
        n = min(n, self.max_size)
        generator = self._generate(n)
        result = list()
        i = 0

        while i < n:
            try:
                result.append(generator.next())
                i += 1
            except StopIteration:
                break 

        return result                      
    
    def _generate(self, n):
        """ Generator function called by draw().  This is an abstract method
            that must be customized by each subclass and must return a 
            generator object.  """
        raise NotImplementedError()

class IntegerDomain(Domain):
    """ A domain containing unsigned integers. """

    def __init__(self):
        super(IntegerDomain, self).__init__()
        
    def _generate(self, n):
        return (i for i in xrange(n))

class FloatDomain(Domain):
    """ A floating point domain.  Only includes floating point numbers
        in increments of 0.1 (e.g. 0.0, 0.1, 0.2, 0.3, etc.).  """

    def __init__(self):
        super(FloatDomain, self).__init__()

    def _generate(self, n):
        return (float(i) / 10.0 for i in xrange(n))

class BoolDomain(Domain):
    """ A domain for boolean (True/False) values. """

    def __init__(self):
        super(BoolDomain, self).__init__(max_size=2)

    def _generate(self, n):
        values = [False, True]
        return (i for i in values[:n])

class StringDomain(Domain):
    """ A domain for string values. The constructor includes a prefix
        parameter.  Generated strings are of the form 'prefix<n>'
        where <n> is a monotonically increasing unsigned integer. """

    def __init__(self, prefix=""):
        super(StringDomain, self).__init__()
        self.prefix = prefix

    def _generate(self, n):
        return (self.prefix + str(i) for i in xrange(n))

class DateDomain(Domain):
    """ A domain for date values.  Generated dates start on <start>
        which defaults to January 1, 2000."""

    def __init__(self, start=date(2000, 01, 01)):
        max_days = (date(datetime.MAXYEAR, 12, 31) - start).days + 1
        super(DateDomain, self).__init__(max_size=max_days)
        self.start = start

    def _generate(self, n):
        return (self.start + timedelta(i) for i in xrange(n))

class TimeDomain(Domain):
    """ A domain for time values.  Generated times start at <start>
        which defaults to midnight and increments by minutes. """

    def __init__(self, start=time()):
        start = datetime.datetime.combine(date.today(), start)
        stop = datetime.datetime.combine(date.today(), time(23, 59))
        max_mins = int((stop - start).total_seconds()/60) + 1
        super(TimeDomain, self).__init__(max_size=max_mins)

        self.start = start

    def _generate(self, n):
        return ((self.start + timedelta(minutes=i)).time() for i in xrange(n))

class DateTimeDomain(Domain):
    """ A domain for datetime values.  Generated datetimes start on <start>
        which defaults to January 1, 2000 at midnight and increment by
        minutes."""

    def __init__(self, start=datetime.datetime(2000, 01, 01)):
        max_dt = datetime.datetime(datetime.MAXYEAR, 12, 31, 23, 59)
        max_mins = int((max_dt - start).total_seconds()/60) + 1
        super(DateTimeDomain, self).__init__(max_size=max_mins)

        self.start = start

    def _generate(self, n):
        return (self.start + timedelta(minutes=i) for i in xrange(n))

class EnumeratedDomain(Domain):
    """ A domain whose values are explicitly provided by the caller. """

    def __init__(self):
        super(EnumeratedDomain, self).__init__()
        self._domain = list() # _domain is a list to enforce order; in add(),
                              # we will ensure its contents are unique

    @property
    def size(self):
        """ Size of the enumerated domain. """
        return len(self._domain)

    @property
    def max_size(self):
        """ Maximum size of the domain, which for an enumerated domain is 
            just the size of the underlying list (i.e. max_size answers the 
            question, what is the largest possible number of items to draw
            from the domain?). """
        return self.size

    @max_size.setter
    def max_size(self, value):
        """ Max_size cannot be set, it is always calculated for this class.  So 
            we ignore the value provided. This setter is needed because 
            __init__() on Domain tries to initialize max_size.  """
        pass         

    def add(self, elements):
        """ Add an element or list of elements to the domain."""
        if isinstance(elements, list):
            new_elements = set(elements) - set(self._domain)
            self._domain += sorted(new_elements)
        elif elements not in self._domain:
            self._domain.append(elements)

    def _generate(self, n):
        return (element for element in self._domain)

    
