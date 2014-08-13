##############################################################################
# Package: ormpy
# File:    TestDomain.py
# Author:  Matthew Nizol
##############################################################################

""" This file contains unit tests for the lib.Domain module. """

from unittest import TestCase

import lib.Domain as Domain

from lib.Constraint import ValueConstraint

class TestDomain(TestCase):
    """ Unit tests for the Domain module. """

    def setUp(self):
        pass

    def test_create_domain(self):
        """ Test creation of a domain. """




def main():
    cons = ValueConstraint()
    cons.add_range(min_value=4, max_value=10)
    cons.add_range(min_value=15, min_open=True, max_value=20, max_open=True)
    dom = NumericDomain(constraint=cons)
    for i in range(20):
        print dom.next()  


    print "="*50
    cons = ValueConstraint()
    cons.add_range(min_value=4.4, max_value=5.31)
    cons.add_range(min_value=15, min_open=True, max_value=16, max_open=True)
    dom = FloatDomain(constraint=cons)
    for i in range(20):
        print dom.next()  

    print "="*50
    dom = BoolDomain()
    for i in range(10):
        print dom.next() 

    print "="*50
    cons = ValueConstraint()
    cons.add_range(min_value=False, max_value=False)
    cons.add_range(min_value=False, max_value=False)
    dom = BoolDomain(cons)
    for i in range(10):
        print dom.next() 

if __name__=="__main__":
    main()

