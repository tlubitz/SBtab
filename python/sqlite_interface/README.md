sqlite_interface - I/O from and to SQLite
=========================================

SBtabDict - A wrapper object, derived from dict, for handling an SBtab with 
multiple tables. The keys are strings with the table names 
and the values are of the type SBtabTable. SBtabDict is an intermediate data
structure mainly used for I/O between SQLite and SBtab.

<b>From SBtab to SQLite</b><br>

In order to upload data from an SBtab file into an SQLite database, first use
FromSBtab() to read the data and then use SBtab2SQL() to insert the data into
the SQLite database. Example code:

```python
import sqlite3

_sbtab_dict = SBtabDict.FromSBtab(sbtab_fpath)
comm = sqlite3.connect(sqlite_fpath)
_sbtab_dict.SBtab2SQL(comm)
comm.close()
```

<b>From SQLite to SBtab</b><br>

Later, to load the data from the SQLite database into a SBtabDict structure
use FromSQLite(). Example code:

```python
sbtab_dict = SBtabDict.FromSQLite(sqlite_fpath)
```


