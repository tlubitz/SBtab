#!/usr/bin/env python
"""
SBtab Validator commandline wrapper
===================================

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
except:
    import SBtab
    import misc

import argparse

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def sbtab2html_wrapper(args):
    '''
    commandline wrapper for the SBtab validator
    '''
    # open and create SBtab
    try:
        f = open(args.sbtab, 'r').read()
    except:
        raise SBtabError('SBtab file %s could not be found.' % args.sbtab)

    # count given tabs and prepare file name w/o path
    tab_amount = misc.count_tabs(f)
    if '/' in args.sbtab:
        name_pre = args.sbtab.split('/')[-1:]
    else: name_pre = args.sbtab
    
    if args.multiple:
        try:
            sbtab_doc = SBtab.SBtabDocument('sbtab_doc_prelim', f, args.sbtab)
            for tab in sbtab_doc.sbtabs:
                name = name_pre[0][:4] + '_' + tab.table_id + '.html'
                try:
                    write_html(tab, name)
                except:
                    raise SBtabError('The HTML file %s could not be created.' % name)
        except:
            raise SBtabError('The multiple HTML files could not be created.')
    else:
        try:
            if tab_amount > 1:
                sbtab = SBtab.SBtabDocument('sbtab_doc_prelim', f, args.sbtab)
                name = name_pre[0][:4] + '_' + sbtab.name + '.html'    
            else:
                sbtab = SBtab.SBtabTable(f, args.sbtab)
                name = name_pre[0][:4] + '_' + sbtab.table_id + '.html'
            write_html(sbtab, name)
        except:
            raise SBtabError('The HTML file could not be created.')

def write_html(sbtab, name):
    '''
    calls the sbtab_to_html function and writes the HTML to disk
    '''
    html = misc.sbtab_to_html(sbtab, mode='standalone')
    h = open(name, 'w')
    h.write(html)
    h.close()    
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('sbtab', help='Path to an SBtab file.')
    parser.add_argument('-m', '--multiple', help='Flag to create multiple HTML files', action='store_true')
    parser.add_argument('-v', '--verbose', help='Flag to display script messages.', action='store_true')

    args = parser.parse_args()

    sbtab2html_wrapper(args)

