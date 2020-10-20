#!/usr/bin/env python
"""
SBtab to ObjTables converter commandline wrapper
===================================

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
except:
    import SBtab
    import misc

import copy
import libsbml
import argparse

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

# NOTE THAT THE FOLLOWING FUNCTION IS CODE DUPLICATED FROM sbml2sbtab.py
# IT WOULD BE BETTER TO HAVE ONE CENTRAL COPY OF THIS FUNCTION!

def create_obj_tables_doc(sbtab_doc):
    '''
    make a copy of the SBtab doc in form of an
    ObjTables doc
    '''
    obj_tables_doc = copy.deepcopy(sbtab_doc)

    obj_tables_doc.document_format = 'ObjTables'
    obj_tables_doc.doc_row = obj_tables_doc.doc_row.replace('SBtab', 'ObjTables')
    obj_tables_doc.change_attribute('schema', 'SBtab')
    obj_tables_doc.change_attribute('objTablesVersion', '1.0.1')
    #Currently, cannot be unset: 
    #obj_tables_doc.unset_attribute('SBtabVersion')
    #obj_tables_doc.unset_attribute('Document')

    for sbtab in obj_tables_doc.sbtabs:
        sbtab.table_format = 'ObjTables'
        sbtab.header_row = sbtab.header_row.replace('!!SBtab', '!!ObjTables')
        sbtab.change_attribute('schema', 'SBtab')
        sbtab.change_attribute('type', 'Data')
        sbtab.change_attribute('tableFormat', 'row')
        sbtab.change_attribute('class', sbtab.table_type)
        sbtab.change_attribute('name', sbtab.table_name)
        sbtab.change_attribute('objTablesVersion', '1.0.1')
        sbtab.unset_attribute('TableName')
        sbtab.unset_attribute('Date')
        #Currently, cannot be unset at all
        #sbtab.unset_attribute('TableType')
        #sbtab.unset_attribute('TableID')
        #sbtab.unset_attribute('Document')
        #Currently, cannot be unset (roundtrip impossible)
        #sbtab.unset_attribute('SBtabVersion')

    return obj_tables_doc


def converter_sbtab2objtables_wrapper(args):
    '''
    commandline wrapper for the SBtab to ObjTables converter
    '''
    # open and create SBtab
    try:
        f = open(args.sbtab, 'r').read()
    except:
        raise SBtabError('SBtab file %s could not be found.' % args.sbtab)
    
    try:
        sbtab_doc = SBtab.SBtabDocument('conversion_document', f, args.sbtab)
    except:
        raise SBtabError('SBtab Document %s could not be created.' % args.sbtab)

    # create converter class
    try:
        objtables_doc = create_obj_tables_doc(sbtab_doc)
        if len(args.outfile)>0:
            outfile = args.outfile
        else:
            outfile = 'objtables.tsv'
        p = open(outfile,'w')
        p.write(objtables_doc.doc_row+'\n')
        for objtable in objtables_doc.sbtabs:        
            p.write(objtable.to_str()+'\n\n')
        p.close()
    except:
        raise SBtabError('SBtab Document %s could not be converted.' % args.sbtab)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('sbtab', help='Path to SBtab input file.')
    parser.add_argument('-o', '--outfile', help='Path to ObjTables output file.', default=[])

    args = parser.parse_args()

    converter_sbtab2objtables_wrapper(args)
