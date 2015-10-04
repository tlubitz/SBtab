SBtab Python Code
=================
This directory holds all SBtab files implemented in Python. For directory content please see the main directory.

<h3>How to embed SBtab into your code</h3>

```python
import tablibIO
import SBtab

#1: Open a file and read it
sbtab_file   = open('your_file.tsv','r')
file_content = sbtab_file.read()
sbtab_file.close()

#2: create a tablib object
tablib_obj = tablibIO.importSetNew(file_content,'your_file.tsv')

#3: create an SBtab object
SBtab_obj = SBtab.SBtabTable(tablib_obj,'your_file.tsv')

```
