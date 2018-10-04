SBtab Python Code
=================
Here, we show you how to use SBtab in your own Python code. If you have questions that are not answered in this short summary, please refer to the [SBtab specification](https://www.sbtab.net/sbtab/default/specification.html) or send a mail to timo.lubitz@gmail.com and wolfram.liebermeister@gmail.com. Also, you can always feel free to add bug reports and feature requests to this Github repo.

<h3>Preliminaries</h3>
<ul>
    <li>python3</li>
    <li>libsbml (SBML manipulation for python)</li>
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
    (sbml,warnings) = Cd.convert_to_sbml('31')
    # ...where '31' is the SBML Level/Version 3.1
```
<h3>Convert SBML to SBtab Document</h3>

```python
    # read SBML model
    import libsbml
    f = open('hynne.xml','r').read()
    doc = reader.readSBMLFromString(f)
    model = doc.getModel()
    
    # convert model to SBtab Document Sd
    Cd = sbml2sbtab.SBMLDocument(model)
    (Sd,warnings) = Cd.convert_to_sbtab()
```
<h3>The scripts can also be called from commandline</h3>
Please stay tuned for a summary on how to do this. It will follow next week (today is October, 4th).

