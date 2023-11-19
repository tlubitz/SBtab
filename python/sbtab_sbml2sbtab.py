#!/usr/bin/env python
"""
SBML to SBtab / ObjTables converter commandline wrapper
===================================

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
    from . import sbml2sbtab
except:
    import SBtab
    import misc
    import sbml2sbtab

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

def converter_sbml2sbtab_wrapper(args):
    '''
    commandline wrapper for the SBML to SBtab converter
    '''
    # open and create SBML
    try:
        f = open(args.sbml, 'r').read()
    except:
        raise SBtabError('SBML file %s could not be found.' % args.sbml)

    if len(args.outfile)==0:
        args.outfile = "outfile.tsv"
    
    try:
        reader = libsbml.SBMLReader()
        sbml = reader.readSBMLFromString(f)
    except:
        raise SBtabError('SBtab Document %s could not be created.' % args.sbml)

    # create converter class
    try:
        converter = sbml2sbtab.SBMLDocument(sbml.getModel(), args.sbml)
        (sbtab_doc, objtables_doc, warnings) = converter.convert_to_sbtab()
        if len(warnings)>0:
            print(warnings)
        outfile = args.outfile
        if args.objtables:
            if len(args.outfile)==0:
                outfile = 'objtables.tsv'
            p = open(outfile,'w')
            p.write(objtables_doc.doc_row+'\n')
            for objtable in objtables_doc.sbtabs:        
                p.write(objtable.to_str()+'\n\n')
            p.close()
        else:
            if len(args.outfile)==0:
                outfile = 'sbtab.tsv'
            p = open(args.outfile,'w')
            p.write(sbtab_doc.doc_row+'\n')
            for sbtab in sbtab_doc.sbtabs:        
                p.write(sbtab.to_str()+'\n\n')
            p.close()
    except:
        raise SBtabError('SBML Document %s could not be converted.' % args.sbml)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    
    parser.add_argument('sbml', help='Path to SBML input file.')
    parser.add_argument('-o', '--outfile', help='Path to SBtab output file.', default=[])
    parser.add_argument('-j', '--objtables', help='Write output file in ObjTables (instead of SBtab) format.', action='store_true' )

    args = parser.parse_args()

    converter_sbml2sbtab_wrapper(args)
