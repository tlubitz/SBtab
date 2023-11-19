#!/usr/bin/env python
"""
SBtab Validator commandline wrapper
===================================

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
    from . import validatorSBtab 
except:
    import SBtab
    import misc
    import validatorSBtab 

import argparse

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def validator_wrapper(args):
    '''
    commandline wrapper for the SBtab validator
    '''
    # open and create SBtab
    try:
        f = open(args.sbtab, 'r').read()
    except:
        raise SBtabError('SBtab file %s could not be found.' % args.sbtab)

    if args.document:
        try:
            sbtab_doc = SBtab.SBtabDocument('validation_document', f, args.sbtab)
        except:
            raise SBtabError('SBtab Document %s could not be created.' % args.document_name)
        if sbtab_doc.document_format == 'ObjTables':
            raise SBtabError('This tool does not validate ObjTables files; please use the online validator at https://www.objtables.org/app.')
    else:
        try:
            sbtab = SBtab.SBtabTable(f, args.sbtab)
        except:
            raise SBtabError('SBtab Table %s could not be created.' % args.sbtab)
        if sbtab.table_format == 'ObjTables':
            raise SBtabError('This tool does not validate ObjTables files; please use the online validator at https://www.objtables.org/app.')

    # if definitions file is given create SBtab object
    if args.definitions_file:
        try:
            d = open(args.definitions_file, 'r').read()
            sbtab_def = SBtab.SBtabTable(d, args.definitions_file)
        except:
            raise SBtabError('The definitions file %s could not be found.' % args.definitions_file)
    else:
        sbtab_def = None

    # create validator class and validate SBtab object
    if args.document:
        try:
            validate_doc = validatorSBtab.ValidateDocument(sbtab_doc, sbtab_def)
            warnings = validate_doc.validate_document()
            for sbtab in warnings:
                print(sbtab[0])
                if len(sbtab[1]) == 0:
                    print('No Warnings')
                else:
                    for warning in sbtab[1]:
                        print(warning)
                print('\n\n')
        except:
            raise SBtabError('SBtab Document %s could not be validated.' % args.document_name)
    else:
        try:
            validate_table = validatorSBtab.ValidateTable(sbtab, sbtab_def)
            warnings = validate_table.return_output()
            for warning in warnings:
                print(warning)
        except:
            raise SBtabError('SBtab Table %s could not be validated.' % args.sbtab)
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('sbtab', help='Path to an SBtab file.')
    parser.add_argument('-y', '--definitions_file', help='Path to an SBtab definitions file.')
    parser.add_argument('-d', '--document', help='Flag to validate an SBtab Document instead of SBtab Table.', action='store_true')
    parser.add_argument('-v', '--verbose', help='Flag to display script messages.', action='store_true')

    args = parser.parse_args()

    validator_wrapper(args)
