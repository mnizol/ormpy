# ormpy
**ormpy** provides a Python-based API to load, check, and instantiate 
Object Role Modeling (ORM) models developed with the [NORMA modeling tool](http://sourceforge.net/projects/orm/).
The primary algorithm is based upon research by [Smaragdakis, et al.](http://dl.acm.org/citation.cfm?id=1507652)

**ormpy** is a work-in-progress.  Currently, the Smaragdakis algorithm
is implemented, and we are working to add extensions by 
[McGill, et al.](http://dl.acm.org/citation.cfm?id=2001428) and [Nizol, et al.](http://dl.acm.org/citation.cfm?id=2593771)

## Dependencies
**ormpy** has been tested with Python 2.7 on a 64-bit Linux machine.  To 
build ORM models consumable by **ormpy**, you must use [NORMA](http://sourceforge.net/projects/orm/),
which is a Visual Studio plug-in.  However, several test models are available at 
[./test/data](./test/data).  These can be viewed online using the [ORM Solutions ORM Viewer](http://ormsolutions.com/tools/orm.aspx) 
without installing NORMA.

## Command-line use
**ormpy** includes a command-line interface which can be executed via the
[ormpy](./ormpy) script.  Run `ormpy -h` for usage instructions.

## API Documentation
API documentation is at [./doc/_build/html](./doc/_build/html).  To rebuild the 
documentation after an update to the code, run the [update_doc](./update_doc) 
script.  This script requires [sphinx](http://sphinx-doc.org/man/sphinx-apidoc.html).

## Unit Tests
The [./test](./test) subdirectory contains a suite of unit tests and test data.
Some tests rely on [nosetests](https://nose.readthedocs.org/en/latest/) plugins.
You can run all tests in the test suite via the [run_tests](./run_tests) script.
This script requires [nosetests](https://nose.readthedocs.org/en/latest/) and [coverage.py](http://nedbatchelder.com/code/coverage/).
Executing `run_tests --cover` provides test coverage information via coverage.py.

