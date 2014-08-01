# norma.py

The norma.py module loads a .orm file produced by the NORMA
plugin for Visual Studio (http://sourceforge.net/projects/orm/).

Tested with the following namespace versions:

* ormRoot: http://schemas.neumont.edu/ORM/2006-04/ORMRoot 
* orm: http://schemas.neumont.edu/ORM/2006-04/ORMCore

## Omissions

We intentionally ignore much of the .orm file structure when loading it, as
we are only interested in the most fundamental aspects of the model for analysis.
We ignore all nodes outside of the ORMModel node, which includes diagram data (i.e. graphical shape data) and extensions.
We also ignore implicit types and constraints added by NORMA but not explicitly modeled by the modeler.

Within the ORMModel node, we ignore the following nodes:

* Functions (probably intended to support derived fact types)
* ReferenceModeKinds and CustomReferenceModeKinds (not needed as NORMA generates the underlying value 
  types and reference fact types automatically)
* All informal notes (Definitions, Notes, ModelNotes)
* ModelErrors
* Extensions

We also ignore the name and id attributes of the ORMModel.  

For Object Types, we most notably ignore:

* Subtype derivation rules (which is only informally captured by NORMA)
* Instances
* Extensions

For Fact Types and Roles, we most notably ignore:

* Fact type and role derivation rules (which is only informally captured by NORMA)
* Implicit types (ImplicitFact, which is used for the implicit fact types of an objectification)
* Multiple readings (Just use the Name attribute which stores the first reading)
* Instances
* Extensions

For constraints, we only consider constraints that can be handled by ORM-- and its extensions.
Other constraints are reported to the user as ignored.
