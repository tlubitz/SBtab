SBtab Python Code
=================
Here, we show you how to use SBtab in your own Python code. If you have questions that are not answered in this short summary, please refer to the [SBtab specification](https://www.sbtab.net/sbtab/default/specification.html) or send a mail to timo.lubitz@gmail.com and wolfram.liebermeister@gmail.com. Also, you can always feel free to add bug reports and feature requests to this Github repo.

<h3>Preliminaries</h3>
<ul>
    <li>python3</li>
    <li>libsbml (SBML manipulation for python)</li>
    <li>openpyxl (I/O of xlsx files)</li>
    <li>numpy (numerical operations for python)</li>
    <li>scipy (numerical operations for python)</li>
 </ul>

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

    # create an SBtab Table Object St and add filename and content
    St = SBtab.SBtabTable()
    St.set_filename(file_name)
    St.add_sbtab_string(file_content)
``` 
<h3>Alternatively, create an SBtab Document (recommended for larger documents with >1 tables)</h3>
    
```python
    # open a file and read it
    file_name = 'your_file.tsv'
    sbtab_file = open(file_name, 'r')
    file_content = sbtab_file.read()
    sbtab_file.close()

    # create an SBtab Document Object Sd
    Sd = SBtab.SBtabDocument()
    Sd.set_filename(file_name)
    Sd.set_name('My_SBtab_Document')
    Sd.add_sbtab_string(file_content)
    
    # you can add further SBtab tables or strings to the document
    # by using the functions add_sbtab() or add_sbtab_string(), respectively.
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
<h3>Convert SBtab Document to SBML</h3>

```python
    # see generation of SBtab Document Sd above
    Cd = sbtab2sbml.SBtabDocument(Sd)
    (sbml, warnings) = Cd.convert_to_sbml('31')
    # ...where '31' is the SBML Level/Version 3.1
```
<h3>Convert SBML to SBtab Document</h3>

```python
    # read SBML model
    import libsbml
    f = open('hynne.xml', 'r').read()
    reader = libsbml.SBMLReader()
    doc = reader.readSBMLFromString(f)
    model = doc.getModel()
    
    # convert model to SBtab Document Sd
    Cd = sbml2sbtab.SBMLDocument(model, 'hynne.xml')
    (Sd,warnings) = Cd.convert_to_sbtab()
```
<h3>Python API</h3>
The API for the Python modules can be found in the directory <i>SBtab/python/api_documentation/</i>.


<h3>The scripts can also be called from commandline</h3>

Validate a single SBtab file:

> python3 sbtab_validator.py path_to_your_sbtab.tsv

Validate a single SBtab file and provide a definitions file:

> python3 sbtab_validator.py path_to_your_sbtab.tsv --sbtab_definitions path_to_your_definitions.tsv

Validate a document of SBtab files (optionally provide defintions.tsv as above):

> python3 sbtab_validator.py path_to_your_sbtab.tsv -d

Convert an SBtab file to SBML (the SBML file will be written to the current directory):

> python3 sbtab_sbtab2sbml.py path_to_your_sbtab.tsv --version 31

...where "--version 31" stands for SBML Level 3 Version 1. Also possible is "--version 24". Default is "31".

Convert an SBML file to SBtab (the SBtab Document will be written to the current directory):

> python3 sbtab_sbml2sbtab.py path_to_your_sbml.xml

If you are encountering trouble with any of the above, please file a bug report in Github. You can also feel free to file feature requests in the same manner.


