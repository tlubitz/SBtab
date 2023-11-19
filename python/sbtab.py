#!/usr/bin/env python
"""
SBtab commandline wrapper 
=========================

The commandline tool "sbtab [COMMAND]" provides a wrapper 
around the following SBtab tools:

sbtab.py sbml2sbtab      = sbtab_sbml2sbtab.py
sbtab.py sbtab2sbml      = sbtab_sbtab2sbml.py      
sbtab.py sbtab2objtables = sbtab_sbtab2objtables.py
sbtab.py objtables2sbtab = sbtab_objtables2sbtab.py 
sbtab.py sbtab2html      = sbtab_sbtab2html.py      
sbtab.py validator       = sbtab_validator.py       

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
    from . import validatorSBtab 
    from . import sbtab_sbml2sbtab
    from . import sbtab_sbml2sbtab
    from . import sbtab_sbtab2sbml
    from . import sbtab_sbtab2objtables
    from . import sbtab_objtables2sbtab
    from . import sbtab_sbtab2html
    from . import sbtab_validator
except:
    import SBtab
    import misc
    import validatorSBtab 
    import sbtab_sbml2sbtab
    import sbtab_sbtab2sbml
    import sbtab_sbtab2objtables
    import sbtab_objtables2sbtab
    import sbtab_sbtab2html
    import sbtab_validator
    
import argparse

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('command', help='SBtab command')
    parser.add_argument('infile', help='Path to an SBtab, SBML, or ObjTables input file.')
    parser.add_argument('-d', '--document',  help='Flag to validate an SBtab Document instead of SBtab Table.', action='store_true')
    parser.add_argument('-j', '--objtables', help='Write output file in ObjTables (instead of SBtab) format.', action='store_true' )
    parser.add_argument('-l', '--links',     help='Flag to put links automatically', action='store_true')
    parser.add_argument('-m', '--multiple',  help='Flag to create multiple HTML files', action='store_false')
    parser.add_argument('-o', '--outfile',   help='Path to SBtab output file.', default=[])
    parser.add_argument('-p', '--pageheader', help='Page title string to be shown on HTML page', default='')
    parser.add_argument('-r', '--output',    help='Output directory', default = None)
    parser.add_argument('-t', '--template',  help='Template file, to be used instead of default HTML template', default=[])
    parser.add_argument('-v', '--verbose',   help='Flag to display script messages', action='store_true')
    parser.add_argument('-w', '--version', help='SBML version.')
    parser.add_argument('-y', '--definitions_file', help='Path to an SBtab definitions file.')

    args = parser.parse_args()

    if args.command =="sbml2sbtab":
        args.sbml = args.infile
        sbtab_sbml2sbtab.converter_sbml2sbtab_wrapper(args)

    if args.command =="sbtab2sbml":
        args.sbtab = args.infile
        sbtab_sbtab2sbml.converter_sbtab2sbml_wrapper(args)

    if args.command =="sbtab2objtables":
        args.sbtab = args.infile
        sbtab_sbtab2objtables.converter_sbtab2objtables_wrapper(args)

    if args.command =="objtables2sbtab":
        args.objtables = args.infile
        sbtab_objtables2sbtab.converter_objtables2sbtab_wrapper(args)

    if args.command =="sbtab2html":
        args.sbtab = args.infile
        sbtab_sbtab2html.sbtab2html_wrapper(args.sbtab, args.multiple, args.output, args.template, args.links, args.pageheader, args.definitions_file)

    if args.command =="validator":
        args.sbtab = args.infile
        sbtab_validator.validator_wrapper(args)
