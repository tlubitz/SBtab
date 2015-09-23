0. Introduction

The scripts in this directory will allow you to convert SBML files to SBtab files and vice versa. The prerequisites for these scripts are:

- python 2.7 or higher
- numpy (numerical operations for python)
- libsbml (SBML manipulation for python)
- re (regular expression module for python)

These scripts can be embedded in your own code easily. Just follow the instructions on how to use the interface:

1. Converting an SBML file to SBtab output files.

The conversion of an SBML file to SBtab files is easy: simply generate an instance of the class SBMLDocument in sbml2sbtab.py. You have to provide an SBML file as a libsbml instance and a model name as a string. Then start the function makeSBtabs():

    reader = libsbml.SBMLReader()
    sbml = reader.readSBML(sys.argv[1])
    model = sbml.getModel()
    A = sbml2sbtab.SBMLDocument(model,'yourSBMLmodel.xml')
    (sbtabfiles,warnings) = A.makeSBtabs()

    for tab in sbtabfiles:
        tablib_tab = tablibIO.importSetNew(tab[0],'yourSBMLmodel.xml',seperator='\t')
        SBtab_obj = SBtab.SBtabTable(tablib_tab,'yourSBMLmodel.xml')
        SBtab_obj.createDataset()
        SBtab_obj.writeSBtab('tsv', 'yourSBMLmodel.xml'.rstrip('.xml')+'_'+tab[1])

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

If you are having troubles running or embedding the scripts, do not hesitate to contact Timo Lubitz (timo.lubitz@hu-berlin.de).
