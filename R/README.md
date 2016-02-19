R interface
========================

The files in this folder are addressed to R users. They allow the usage of SBtab functionality and objects within R from different angles.

### Loading SBtab files in R

SBtab files can be loaded in R without the employment of Python. Two files are required:
- sbtab_read_tsv.R - a function for reading TSV-formatted SBtab files that contain a single table, into an R data.frame. It is assumed that the first line is the header, and that the SBtab table spans all rows in the TSV file.
- one_or_many.R - a function for reading TSV-formatted SBtab files that (possibly) contain multiple tables, into a list of R data.frames. It is assumed that the tables are separated by a single line that contains only the character '%'. This function can be used for files with single tables as well.

The R file example.R shows how the functions can be used to load the SBtab files.

### rPython interface

SBtab files can also be loaded in R via the rPython interface. This means that the SBtab Python code is called from within the R framework. The file SBtab_in_.R exemplifies how SBtab objects can be loaded, manipulated, validated, and exported to SBML or vice versa. More details can be found in the code documentation.