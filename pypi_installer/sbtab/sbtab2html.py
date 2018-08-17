"""
SBtab2HTML
==========

Python script that converts SBtab file/s to HTML.
"""
#!/usr/bin/env python
import re
import string
import sys
from . import misc

urns = ["obo.chebi","kegg.compound","kegg.reaction","obo.go","obo.sgd","biomodels.sbo","ec-code","kegg.orthology","uniprot"]

def csv2html(sbtab_file,file_name,definition_file=None,sbtype=None):
    '''
    Generates html view out of csv file.

    Parameters
    ----------
    sbtab_file : str
       SBtab file as string representation.
    file_name : str
       SBtab file name.
    definition_file : str
       SBtab definition file as string representation.
    sbtype : str
       SBtab attribute TableType.
    '''
    #extract information from the definition file
    if not definition_file:
        try:
            def_file_open = open('definitions.tsv','r')
            def_file      = def_file_open.read()
            def_delimiter = '\t'
            col2description = findDescriptions(def_file,def_delimiter,sbtype)
            def_file_open.close()
        except:
            print('You have not provided the definition file and it cannot be found in this directory. Please provide it.')
            sys.exit(1)
    else:
        def_delimiter = '\t'
        col2description = findDescriptions(definition_file,def_delimiter,sbtype)

    #now start building the HTML file from the SBtab file
    delimiter = misc.getDelimiter(sbtab_file)    #checkseparator(sbtab_file)
    ugly_sbtab = sbtab_file.split('\n')
    nice_sbtab = '<html>\n<body>\n'
    nice_sbtab += '<p>\n<h2><b>'+file_name+'</b></h2>\n</p>\n'
    nice_sbtab += '<a style="background-color:#00BFFF">'+ugly_sbtab[0]+'</a>\n<br>\n'
    nice_sbtab += '<table>\n'

    ident_url  = False
    ident_cols = []

    for row in ugly_sbtab[1:]:
        if row.startswith('!'):
            nice_sbtab += '<tr bgcolor="#87CEFA">\n'
            splitrow = row.split(delimiter)
            for i,element in enumerate(splitrow):
                if 'Identifiers:' in element:
                    try:
                        searcher  = re.search('Identifiers:(.*)',element)
                        ident_url = 'http://identifiers.org/'+searcher.group(1)+'/'
                        ident_cols.append(i)
                    except: pass
                    
        else: nice_sbtab += '<tr>\n'

        for i,thing in enumerate(row.split(delimiter)):
            try: title = col2description[thing[1:]]
            except: title = ''
            if not ident_url:
                new_row = '<td title="'+str(title)+'">'+str(thing)+'</td>'
                nice_sbtab += new_row+'\n'
            else:
                if i in ident_cols and not thing.startswith('!'):
                    ref_string = ident_url+thing
                    new_row = '<td><a href="'+ref_string+'" target="_blank">'+str(thing)+'</a></td>'
                else:
                    new_row = '<td title="'+title+'">'+str(thing)+'</td>'
                nice_sbtab += new_row+'\n'
                
        nice_sbtab += '</tr>\n'
    nice_sbtab += '</table>\n'

    nice_sbtab += '</body>\n</html>\n'

    html_file = open(file_name[:-4]+'.html','w')
    for row in nice_sbtab: html_file.write(row)
    html_file.close()
    
    return nice_sbtab

def findDescriptions(def_file,def_delimiter,sbtype):
    '''
    Preprocesses the definition file in order to enable some nice mouseover effects for the known column names.

    Parameters
    ----------
    def_file : str
       SBtab definition file as string representation.
    def_delimiter : str
       Delimiter used for the columns; usually comma, tab, or semicolon.
    sbtype : str
       SBtab attribute TableType.
    '''    
    col2description = {}
    col_dsc         = False

    columnrow = def_file.split('\n')[1]
    columnrowspl = columnrow.split(def_delimiter)

    for row in def_file.split('\n'):
        splitrow = row.split(def_delimiter)
        if len(splitrow) != len(columnrowspl): continue
        if row.startswith('!!'): continue
        if row.startswith('!'):
            for i,elem in enumerate(splitrow):
                if elem == "!Description":
                    col_dsc = i
        if not string.capitalize(splitrow[2]) == string.capitalize(sbtype): continue
        if col_dsc and not splitrow[2].startswith('!'): col2description[splitrow[0]] = splitrow[col_dsc]

    return col2description
            
def checkseparator(sbtabfile):
    '''
    Finds the separator of the SBtab file.

    Parameters
    ----------
    sbtabfile : str
       SBtab file as string representation.
    '''
    sep = False

    for row in sbtabfile.split('\n'):
        if row.startswith('!!'): continue
        if row.startswith('!'):
            s = re.search('(.)(!)',row[1:])
            sep = s.group(1)

    return sep

if __name__ == '__main__':

    try: sys.argv[1]
    except:
        print('You have not provided input arguments. Please start the script by also providing an SBtab file, the definition file, and an optional HTML output filename: >python sbtab2html.py SBtabfile.csv definitions.tsv Output')
        sys.exit()

    file_name  = sys.argv[1]

    try:
        default_def = sys.argv[2]
        def_file    = open(default_def,'r')
        def_tab = def_file.read()
        def_file.close()
    except:
        def_tab = None
    
    try: output_name = sys.argv[3]+'.html'
    except: output_name = file_name[:-4]+'.html'

    sbtab_file = open(file_name,'r')
    sbtab      = sbtab_file.read()

    html = csv2html(sbtab,file_name,def_tab,output_name)
    #html_name = output_name
    html_file = open(output_name,'w')
    html_file.write(html)
    html_file.close()

    print('The HTML file has been successfully written to your working directory or chosen output path.')
