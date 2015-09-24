"""
Commandline scripts
=========

There are several Python-based commandline scripts that can be used to integrate core functions of SBtab handling into new software. We are providing the following scripts:

- convert SBtab file/s to SBML file
- convert SBML file to SBtab files
- convert SBtab file/s to HTML file

The prerequisites to use these scripts are:

- python 2.7 or higher
- numpy (numerical operations for python)
- libsbml (SBML manipulation for python)
- re (regular expression module for python)

If you are experiencing troubles running or embedding the scripts, do not hesitate to contact Timo Lubitz (timo.lubitz@hu-berlin.de).

1. Converting an SBML file to SBtab output files.

The conversion of an SBML file to SBtab files is easy: simply generate an instance of the class SBMLDocument in sbml2sbtab.py. You have to provide an SBML file as a libsbml instance and a model name as a string. Then start the function makeSBtabs():

    reader     = libsbml.SBMLReader()
    sbml       = reader.readSBML('yourSBMLmodel.xml')
    A          = SBMLDocument(sbml,'mysbmlmodel.xml')
    sbtabfiles = A.makeSBtabs()

The SBtab files are now stored as a list of SBtab classes in the variable sbtabfiles. If the SBML model provides the required information, the output SBtab files are of the types: compartment, reaction, compound, and quantitytype.

2. Converting SBtab files to an SBML output file.

The conversion from SBtab files to SBML files can be done analogously. Create an instance of the class SBtabDocument in sbtab2sbml.py. The parameters that have to be provided are an SBtab file (of the type reaction) or a list of SBtab files (including one of the type reaction), a filename as a string, and the amount of SBtab files you are providing. Then start the function makeSBML() and the new SBML file is stored in sbml_file:

    #first: open x SBtab files
    sbtab_reaction = open('sbtabs/sbtab_reaction_full.tsv','r')
    sbtab_compound = open('sbtabs/sbtab_compound_full.tsv','r')

    #second: if there are more than one SBtab file, create a list document
    document = []
    document.append(sbtab_reaction.read())
    document.append(sbtab_compound.read())

    #third: create class instance and create SBML
    sbtab_class = SBtabDocument(document,'sbtabname.tsv',2)
    sbml_file   = sbtab_class.makeSBML()

3. Converting SBtab files an HTML output file.

SBtab files in csv format can be converted to HTML files by using the script sbtab2html.py. Please make sure that the file definitions.csv is available in the directory the script is started from. definitions.csv is required for the HTML mouseovers of the columns. The parameters for starting the converter are the SBtab file, the name of the file as a string, and the SBtab table type as a string. The script returns the SBtab file as HTML, moreover this HTML file is written on your hard disk.

    sbtab_file = open('your_sbtab.csv','r')
    sbtab      = sbtab_file.read()
    html_file  = sbtab2html.csv2html(sbtab,'your_sbtab.csv','your_tabletype')
"""
