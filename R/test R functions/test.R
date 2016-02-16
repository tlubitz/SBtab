#install.packages("rPython")

#get some libraries
library(RJSONIO)
library(rPython)

#set working directory and python path
python.exec("import sys, os")
python.exec("basedir = os.path.expanduser('~/git/SBtab')")
python.exec("sys.path.append(basedir + '/python')")
python.exec("sys.path.append(basedir + '/python/commandline_scripts')")
setwd(path.expand('~/git/SBtab/R/test R functions'))

#load some of the python scripts.
#please be aware that the executable scripts validatorSBtab, sbtab2sbml, and sbml2sbtab have to
#be edited to disable the auto execution; easiest to do this is exclusion of the __main__ methods.
python.exec("import libsbml")
python.exec("import tablibIO")
python.exec("from SBtab import SBtabTable")
python.exec("from validatorSBtab import ValidateTable")
python.exec("from sbtab2sbml import SBtabDocument")
python.exec("from sbml2sbtab import SBMLDocument")

#first, generate SBtab object
python.exec("sbtab_file   = open('reaction.tsv','r')")
python.exec("file_content = sbtab_file.read()")
python.exec("sbtab_file.close()")
python.exec("tablib_obj = tablibIO.importSetNew(file_content,'reaction.tsv')")
python.exec("SBtab_obj = SBtabTable(tablib_obj,'reaction.tsv')")

#receiving variables from the SBtab object
file_name <- python.get("SBtab_obj.filename")
#table attributes
table_type <- python.get("SBtab_obj.table_type")
table_name <- python.get("SBtab_obj.table_name")
table_document <- python.get("SBtab_obj.table_document")
table_version <- python.get("SBtab_obj.table_version")
unique_key <- python.get("SBtab_obj.unique_key")
#table structure
delimiter <- python.get("SBtab_obj.delimiter")
columns <- python.get("SBtab_obj.columns")
columns_dict <- python.get("SBtab_obj.columns_dict")
value_rows <- python.get("SBtab_obj.value_rows")

#changing variables of the SBtab object:
#1. changing a single value in the table
row_index = 1
column_index = 2
new_content = 'new_reaction_name'
python.call("SBtab_obj.changeValue",row_index,column_index,new_content)

#2. change an existing row and add it to the SBtab document
value_rows[[1]][1] <- 'new_ID'
value_rows[[1]][2] <- 'new_name'
python.call("SBtab_obj.addRow",value_rows[[1]])

#3. remove a row
python.call("SBtab_obj.removeRow",1)

#4. remove a column
python.call("SBtab_obj.removeColumn",1)

#5. validate the SBtab file and save warnings in R variable
python.exec("V_obj = ValidateTable(file_content,'reaction.tsv')")
warnings <- python.get("V_obj.warnings")

#6. convert an SBtab file to SBML
python.exec("sbtab_file = SBtabDocument(file_content,'reaction.tsv',1)")
python.exec("pysbml = sbtab_file.makeSBML()")
rsbml <- python.get("pysbml")
write(rsbml[[1]], file='sbml.xml')

#7. convert SBML to SBtab
python.exec("reader = libsbml.SBMLReader()")
python.exec("sbml = reader.readSBML('sbml.xml')")
python.exec("A = SBMLDocument(sbml,'yourSBMLmodel.xml')")
python.exec("(sbtabfiles,warnings) = A.makeSBtabs()")
sbtabs <- python.get("sbtabfiles")
warnings <- python.get("warnings")

