#!/usr/bin/env python
import re
import string

urns = ["obo.chebi","kegg.compound","kegg.reaction","obo.go","obo.sgd","biomodels.sbo","ec-code","kegg.orthology","uniprot"]

def csv2html(sbtab_file,file_name,sbtype):
    '''
    generates html view out of csv file
    '''
    #extract information from the definition file
    def_file_open = open('definitions.csv','r')
    def_file      = def_file_open.read()
    def_delimiter = '\t'
    col2description = findDescriptions(def_file,def_delimiter,sbtype)
    def_file_open.close()

    #now start building the HTML file from the SBtab file
    delimiter = checkSeperator(sbtab_file)
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
    preprocesses the definition file in order to enable some nice mouseover effects for the known column names
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
            
def checkSeperator(sbtabfile):
    '''
    find the seperator of the file; this is fucked up, but crucial
    '''
    sep = False

    for row in sbtabfile.split('\n'):
        if row.startswith('!!'): continue
        if row.startswith('!'):
            s = re.search('(.)(!)',row[1:])
            sep = s.group(1)

    return sep
