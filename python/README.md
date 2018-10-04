SBtab Python Code
=================
Here, we show you how to use SBtab in your own Python code. If you have questions that are not answered in this short summary, please refer to the [SBtab specification](https://www.sbtab.net/sbtab/default/specification.html) or send a mail to timo.lubitz@gmail.com and wolfram.liebermeister@gmail.com. Also, you can always feel free to add bug reports and feature requests to this Github repo.

<h3>Preliminaries</h3>
- python3
- libsbml (SBML manipulation for python)
- numpy (numerical operations for python)
- scipy (numerical operations for python)

<h3>How to embed SBtab Tables into your code</h3>

```python
    # SBtab classes source code
    import SBtab
    
    # SBtab validator
    import validatorSBtab
    
    # Converter SBtab -> SBML
    import sbtab2sbml
    
    # Converter SBML -> SBtab
    import sbml2sbtab
``` 
<h3>Create an SBtab Table (recommended for single tables)</h3>
    
```python
    # open a file and read it
    file_name = 'your_file.tsv'
    sbtab_file = open(file_name, 'r')
    file_content = sbtab_file.read()
    sbtab_file.close()

    # create an SBtab Table Object St
    St = SBtab.SBtabTable(file_content, file_name)
``` 
<h3>Alternatively, create an SBtab Document (recommended for larger documents with >1 tables)</h3>
    
```python
    # open a file and read it
    file_name = 'your_file.tsv'
    sbtab_file = open(file_name, 'r')
    file_content = sbtab_file.read()
    sbtab_file.close()

    # create an SBtab Document Object Sd
    Sd = SBtab.SBtabDocument('your_document_name', file_content, file_name)
    # you can also create an empty SBtab Document by
    # omitting the file_content and file_name.
    # you can add SBtab tables or strings to the document
    # by using the functions add_sbtab() or add_sbtab_string, respectively.
``` 

<h3>Validate your SBtab objects</h3>

```python
    # validate the file
    ValidateTable = validatorSBtab.ValidateTable(St)
    warnings = ValidateTable.return_output()
    print(warnings)

    # validate all SBtabs from the document
    ValidateDocument = validatorSBtab.ValidateDocument(Sd)
    warnings = ValidateDocument.validate_document()
    print(warnings)
```




## Starting the scripts from commandline:

All scripts can be either embedded in your code (see below) or started from commandline. The former looks like this:
`>python sbtab2sbml.py SBtabfile.csv Outputname`
...where "SBtabfile.csv" is the name of your SBtabfile, "Outputname" is an _optional_ outputname for the SBML file.

`>python sbml2sbtab.py SBMLfile.xml Outputname`
...where, analogously, "SBMLfile.xml" is the name of your SMBL file and "Outputname" is an _optional_ outputname for the SBtab file/s.

`>python validatorSBtab.py SBtabfile.csv definition.tsv`
...where "SBtabfile.csv" is your SBtab file to be validated and "definition.tsv" is the required default definition table, which can be found in the table_definition directory. Please note that also "SBtab.py" needs to be imported for the validation.

## Embedding of Code: Conversion of an SBML file to SBtab output files.

The conversion of an SBML file to SBtab files is easy: simply generate an instance of the class SBMLDocument in sbml2sbtab.py. You have to provide an SBML file as a libsbml instance and a model name as a string. Then start the function makeSBtabs():
```python
    reader = libsbml.SBMLReader()
    sbml = reader.readSBML(sys.argv[1])
    model = sbml.getModel()
    A = sbml2sbtab.SBMLDocument(model,'yourSBMLmodel.xml')
    (sbtabfiles,warnings) = A.makeSBtabs()

    for tab in sbtabfiles:
        tablib_tab = tablibIO.importSetNew(tab[0],'yourSBMLmodel.xml',separator='\t')
        SBtab_obj = SBtab.SBtabTable(tablib_tab,'yourSBMLmodel.xml')
        SBtab_obj.createDataset()
        SBtab_obj.writeSBtab('tsv', 'yourSBMLmodel.xml'.rstrip('.xml')+'_'+tab[1])
```
The SBtab files are now stored as a list of SBtab classes in the variable sbtabfiles. If the SBML model provides the required information, the output SBtab files are of the types: compartment, reaction, compound, quantitytype, event, and rule.

## Embedding of Code: Conversion of SBtab files to an SBML output file.

The conversion from SBtab files to SBML files can be done analogously. Create an instance of the class SBtabDocument in sbtab2sbml.py. The parameters that have to be provided are an SBtab file (of the type reaction) or a list of SBtab files (including one of the type reaction), a filename as a string, and the amount of SBtab files you are providing. Then start the function makeSBML() and the new SBML file is stored in sbml_file:
```python
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
```
If you are having troubles running or embedding the scripts, do not hesitate to contact Timo Lubitz (timo.lubitz@hu-berlin.de).
