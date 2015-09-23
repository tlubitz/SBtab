The Excel plugins are supposed to work in three ways and thus they require three different scripts:

1. Convert SBML file to SBtab file
This plugin requires the file sbml2sbtab.py. The input is an SBML model and the output is a list of SBtab files. Use it e.g. as explained in the general readme.txt in this directory. But: the *direct* output of this script is a list of strings, which should be easy to use for the plugin and display in Excel (I hope?).

2. Convert SBtab/s to SBML file.
This plugin requires the file sbtab2sbml.py. The input is either a list of SBtabs or one SBtab file or one file with several SBtabs in it. It can be seen in the main method how it is called. The output is an SBML file.

3. Validate SBtab files.
This plugin requires the file validatorSBtab.py. The input is either a single SBtab file, several SBtab files (use parameter "tabs" for initialisation) or a single file with many SBtabs in it. Here again, the usage can be seen in the main method. The output is a python dictionary that links the filename (key) to a string list of warnings (value).
