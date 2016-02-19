#!/usr/bin/env python
import re
import tablib
import string
import validatorSBtab
import tablib.packages.xlrd as xlrd

urns = ["obo.chebi","kegg.compound","kegg.reaction","obo.go","obo.sgd","biomodels.sbo","ec-code","kegg.orthology","uniprot","hmdb"]

def csv2html(sbtab_file,file_name,delimiter,sbtype,def_file=None,def_file_name=None):
    '''
    generates html view out of csv file
    '''
    if def_file:
        FileValidClass = validatorSBtab.ValidateFile(def_file,def_file_name)
        def_delimiter  = FileValidClass.checkseparator()
    else:
        def_file_open = open('./definitions/definitions.tsv','r')
        def_file      = def_file_open.read()
        def_delimiter = '\t'

    col2description = findDescriptions(def_file,def_delimiter,sbtype)

    ugly_sbtab = sbtab_file.split('\n')
    nice_sbtab = '<p><h2><b>'+file_name+'</b></h2></p>'
    nice_sbtab += '<a style="background-color:#00BFFF">'+ugly_sbtab[0]+'</a><br>'
    nice_sbtab += '<table>'

    ident_url  = False
    ident_cols = []
    col2urn    = {}

    for row in ugly_sbtab[1:]:
        if row.startswith('!'):
            nice_sbtab += '<tr bgcolor="#87CEFA">'
            splitrow = row.split(delimiter)
            for i,element in enumerate(splitrow):
                if 'Identifiers:' in element:
                    try:
                        searcher  = re.search('Identifiers:(.*)',element)
                        ident_url = 'http://identifiers.org/'+searcher.group(1)+'/'
                        #ident_cols.append(i)
                        col2urn[i] = ident_url
                    except: pass
        elif row.startswith('%'):
            nice_sbtab += '<tr bgcolor="#C0C0C0">'
        else: nice_sbtab += '<tr>'
        
        for i,thing in enumerate(row.split(delimiter)):
            try: title = col2description[thing[1:]]
            except: title = ''
            if not ident_url:
                new_row = '<td title="'+str(title)+'">'+str(thing)+'</\td>'
                nice_sbtab += new_row
            else:
                if i in col2urn.keys() and not thing.startswith('!'):
                    ref_string = col2urn[i]+thing
                    new_row = '<td><a href="'+ref_string+'" target="_blank">'+str(thing)+'</a></\td>'
                else:
                    new_row = '<td title="'+title+'">'+str(thing)+'</\td>'
                nice_sbtab += new_row
                
        nice_sbtab += '</tr>'
    nice_sbtab += '</table>'
    
    return nice_sbtab


def xls2html(xls_sbtab,file_name,sbtype,def_file=None,def_file_name=None):
    '''
    generates html view out of xls file
    '''
    if def_file:
        FileValidClass = validatorSBtab.ValidateFile(def_file,def_file_name)
        def_delimiter  = FileValidClass.checkseparator(def_file)
    else:
        def_file_open = open('./definitions/definitions.tsv','r')
        def_file      = def_file_open.read()
        def_delimiter = '\t'

    col2description = findDescriptions(def_file,def_delimiter,sbtype)

    nice_sbtab = '<p><h2><b>'+file_name+'</b></h2></p>'
    ident_url = False

    dbook = tablib.Databook()
    xl = xlrd.open_workbook(file_contents=xls_sbtab)

    for sheetname in xl.sheet_names():
        dset = tablib.Dataset()
        dset.title = sheetname
        sheet = xl.sheet_by_name(sheetname)
        for row in range(sheet.nrows):
            if row == 0:
                new_row = ''
                for thing in sheet.row_values(row):
                    if not thing == '': new_row += thing
                nice_sbtab += '<a style="background-color:#00BFFF">'+new_row+'</a><br>'
                nice_sbtab += '<table>'
            elif row == 1:
                new_row = ''
                for i,thing in enumerate(sheet.row_values(row)):
                    try: title = col2description[thing[1:]]
                    except: title = ''
                    if not thing == '': new_row += '<td title="'+title+'">'+str(thing)+'</\td>'
                    if "Identifiers:" in thing:
                        urn_str = re.search("\w*\.\w*",thing)
                        urn     = urn_str.group(0)
                        ident_url = 'http://identifiers.org/'+urn+'/'
                        ident_col = i
                nice_sbtab += '<tr bgcolor="#87CEFA">'+new_row+'</tr>'
            else:
                new_row = ''
                for i,thing in enumerate(sheet.row_values(row)):
                    if not ident_url:
                        new_row += '<td>'+str(thing)+'</td>'
                    else:
                        if i == ident_col:
                            ref_string  = ident_url+thing
                            new_row    += '<td><a href="'+ref_string+'" target="_blank">'+str(thing)+'</a></\td>'
                        else:
                            new_row    += '<td>'+str(thing)+'</td>'
                nice_sbtab += '<tr>'+new_row+'</tr>'
                        
    return nice_sbtab    

def xml2html(sbml_file):
    '''
    generates html view out of xml file
    '''
    old_sbml = sbml_file.split('\n')
    new_sbml = '<xmp>'

    for row in old_sbml:
        new_sbml += row + '\n'

    new_sbml += '</xmp>'
        
    return new_sbml

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
            
