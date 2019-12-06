#!/usr/bin/env python
"""
SBtab to HTML commandline wrapper
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
import os

class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def sbtab2html_wrapper(sbtab, multiple, output, template, links, pageheader, definitions_file,show_table_text=True):
    '''
    commandline wrapper for sbtab_to_html function
    '''
    # open and create SBtab
    try:
        f = open(sbtab, 'r').read()
    except:
        raise SBtabError('SBtab file %s could not be found.' % sbtab)

    # count given tabs and prepare file name w/o path
    tab_amount = misc.count_tabs(f)
    if '/' in sbtab:
        name_pre = sbtab.split('/')[-1:]
    else:
        name_pre = sbtab

    # count given tabs and prepare file name w/o path
    if output is not None:
        outfile_dir, outfile_file = os.path.split(output)
        if not os.path.exists(outfile_dir):
            os.mkdir(outfile_dir)
        outfile_file=os.path.splitext(outfile_file)[0]
        name_pre[0] = outfile_file
    else:
        outfile_dir = '.'

    file_basename = os.path.splitext(name_pre[0])[0]

    if tab_amount > 1:
        multiple = True

    if multiple:
        try:
            sbtab_doc = SBtab.SBtabDocument('sbtab_doc_prelim', f, sbtab)
            for tab in sbtab_doc.sbtabs:
                if len(file_basename):
                    name = outfile_dir + '/' + file_basename + '_' + tab.table_id + '.html'
                else:
                    name = outfile_dir + '/' + tab.table_id + '.html'
                try:
                    write_html(tab, name, template, links, pageheader, definitions_file,show_table_text=show_table_text)
                except:
                    raise SBtabError('The HTML file %s could not be created.' % name)
        except:
            raise SBtabError('The multiple HTML files could not be created.')
    else:
        try:
            if tab_amount > 1:
                sbtab = SBtab.SBtabDocument('sbtab_doc_prelim', f, sbtab)
                name = outfile_dir + '/' + file_basename + '_' + sbtab.table_id + '.html'
            else:
                sbtab = SBtab.SBtabTable(f, sbtab)
                name = outfile_dir + '/' + file_basename + '.html'
            write_html(sbtab, name, template, links, pageheader, definitions_file,show_table_text=show_table_text)
        except:
            raise SBtabError('The HTML file could not be created.')

def write_html(sbtab, name, template, links, pageheader, definitions_file, show_table_text=True):
    '''
    calls the sbtab_to_html function and writes the HTML to disk
    '''
    html = misc.sbtab_to_html(sbtab, mode='standalone',template=template, put_links = links, title_string=pageheader, show_header_row=False, show_table_name=True, show_table_text=show_table_text, definitions_file = definitions_file)
    h = open(name, 'w')
    h.write(html)
    h.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert SBtab files into HTML')

    parser.add_argument('sbtab', help='Path to an SBtab file.')
    parser.add_argument('-m', '--multiple', help='Flag to create multiple HTML files', action='store_false')
    parser.add_argument('-o', '--output', help='Output directory', default = [])
    parser.add_argument('-t', '--template', help='Template file, to be used instead of default HTML template', default=[])
    parser.add_argument('-v', '--verbose', help='Flag to display script messages', action='store_true')
    parser.add_argument('-l', '--links', help='Flag to put links automatically', action='store_true')
    parser.add_argument('-p', '--pageheader', help='Page title string to be shown on HTML page', default=[])
    parser.add_argument('-d', '--definitions_file', help='Path to custom definitions file', default=[])

    args = parser.parse_args()

    sbtab2html_wrapper(args.sbtab, args.multiple, args.output, args.template, args.links, args.pageheader, args.definitions_file)
