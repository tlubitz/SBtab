#!/usr/bin/env python
"""
SBtab to SBML converter commandline wrapper
===================================

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
    from . import sbtab2sbml
except:
    import SBtab
    import misc
    import sbtab2sbml

import argparse

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def converter_sbtab2sbml_wrapper(args):
    '''
    commandline wrapper for the SBtab to SBML converter
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

    if len(args.outfile)>0:
        outfile = args.outfile
    else:
        outfile = 'sbml.xml'

    # create converter class
    if args.version:
        if args.version != '31' and args.version != '24':
            raise SBtabError('SBtab to SBML conversion does currently only support SBML Level and Version 2.4 and 3.1.')
        
        try:
            converter = sbtab2sbml.SBtabDocument(sbtab_doc)
            (sbml, warnings) = converter.convert_to_sbml(args.version)
            if len(warnings)>0:
                print('Warnings:')
                print(warnings)
            p = open(outfile,'w')
            p.write(sbml)
            p.close()
        except:
            raise SBtabError('SBtab Document %s could not be converted to SBML.' % args.sbtab)
    else:
        try:
            converter = sbtab2sbml.SBtabDocument(sbtab_doc)
            (sbml, warnings) = converter.convert_to_sbml('31')
            if len(warnings)>0:
                print('Warnings:')
                print(warnings)
            p = open(outfile,'w')
            p.write(sbml)
            p.close()    
        except:
            raise SBtabError('SBtab Document %s could not be converted to SBML.' % args.sbtab)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('sbtab', help='Path to SBtab input file.')
    parser.add_argument('-v', '--version', help='SBML version.')
    parser.add_argument('-o', '--outfile', help='Path to SBtab output file.', default=[])

    args = parser.parse_args()

    converter_sbtab2sbml_wrapper(args)

