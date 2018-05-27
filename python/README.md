SBtab Python Code
=================
This directory holds all SBtab files implemented in Python3. For directory content please see the main directory.

<h3>How to embed SBtab Tables into your code</h3>

```python
import SBtab
import validate

# open a file and read it
file_name = 'your_file.tsv'
sbtab_file = open(file_name, 'r')
file_content = sbtab_file.read()
sbtab_file.close()

# create an SBtab Object
Sbtab_obj = SBtab.SBtabTable(file_content, file_name)

# validate the file
ValidateClass = validatorSBtab.validateTable(Sbtab_obj)
warnings = ValidateClass.return_output()
print(warnings)

# alternatively, create an SBtab Document (if you have more than one SBtab belonging to one document)
Sbtab_doc = SBtab.SBtabDocument()

# add an SBtab as object
Sbtab_doc.add_sbtab(Sbtab_obj)
# or as string:
Sbtab_doc.add_sbtab_string(file_content, file_name)

# validate single file from the document
for sbtab in Sbtab_doc.sbtabs:
    ValidateClass = validatorSBtab.validateTable(Sbtab_obj)
    warnings = ValidateClass.return_output()
    print(warnings)
```
