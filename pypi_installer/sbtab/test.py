#!/usr/bin/env python

##############################################################
# Create an SBtab object from a tsv spreadsheet file #########
##############################################################
import sbtab

f = open('sbtab_examples/BIOMD0000000061_Compound.tsv','r+')
tl_object = sbtab.tablibIO.importSetNew(f.read(),'name.tsv')
sbtab_object = sbtab.SBtab.SBtabTable(tl_object,'name.tsv')
f.close()

print(sbtab_object.table_type)

##############################################################
# Create an SBML object from an SBtab tsv spreadsheet file ###
##############################################################
f = open('sbtab_examples/BIOMD0000000061_Compound.tsv','r+')
s2s_object = sbtab.sbtab2sbml.SBtabDocument(f.read(),'name.tsv')
(sbml_object,warnings) = s2s_object.makeSBML()
f.close()

print(sbml_object)
