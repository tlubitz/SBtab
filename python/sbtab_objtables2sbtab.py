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

# IT WOULD BE BETTER TO HAVE ONE CENTRAL COPY OF THIS FUNCTION!

def create_sbtab_from_obj_tables_doc(objtables_doc, sbtab_def):
    '''
    make a copy of the ObjTables doc in form of an
    SBtab doc
    '''
    sbtab_doc = copy.deepcopy(objtables_doc)

    sbtab_doc.document_format = 'SBtab'
    sbtab_doc.doc_row = sbtab_doc.doc_row.replace('ObjTables','SBtab')
    sbtab_doc.change_attribute('SBtabVersion', '1.2')
    sbtab_doc.unset_attribute('schema')
    sbtab_doc.unset_attribute('objTablesVersion')

    for sbtab in sbtab_doc.sbtabs:
        sbtab.table_format = 'SBtab'
        sbtab.header_row = sbtab.header_row.replace('!!ObjTables','!!SBtab')
        sbtab.change_attribute('TableName', sbtab.table_name)
        #sbtab.unset_attribute('name')
        sbtab.unset_attribute('schema')
        sbtab.unset_attribute('type')
        sbtab.unset_attribute('tableFormat')
        sbtab.unset_attribute('class')
        sbtab.unset_attribute('objTablesVersion')

    return sbtab_doc

def converter_objtables2sbtab_wrapper(args):
    '''
    commandline wrapper for the ObjTables to SBtab converter
    '''
    # open ObjTables file
    try:
        f = open(args.objtables, 'r').read()
    except:
        raise SBtabError('SBtab file %s could not be found.' % args.objtables)
    
    try:
        objtables_doc = SBtab.SBtabDocument('conversion_document', f, args.objtables)
    except:
        raise SBtabError('SBtab Document %s could not be created.' % args.objtables)

    # if definitions file is given create SBtab object
    if args.definitions_file:
        try:
            d = open(args.definitions_file, 'r').read()
            sbtab_def = SBtab.SBtabTable(d, args.definitions_file)
        except:
            raise SBtabError('The definitions file %s could not be found.' % args.definitions_file)
    else:
        sbtab_def = None

    # create converter class
    try:
        sbtab_doc = create_sbtab_from_obj_tables_doc(objtables_doc, sbtab_def)
        if len(args.outfile)>0:
            outfile = args.outfile
        else:
            outfile = 'sbtab.tsv'
        p = open(outfile,'w')
        p.write(sbtab_doc.doc_row+'\n')
        for sbtab in sbtab_doc.sbtabs:        
            p.write(sbtab.to_str()+'\n\n')
        p.close()
    except:
        raise SBtabError('SBtab Document %s could not be converted.' % args.sbtab)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('objtables', help='Path to ObjTables input file.')
    parser.add_argument('-o', '--outfile', help='Path to SBtab output file.', default=[])
    parser.add_argument('-y', '--definitions_file', help='Path to an SBtab definitions file.')

    args = parser.parse_args()

    converter_objtables2sbtab_wrapper(args)
