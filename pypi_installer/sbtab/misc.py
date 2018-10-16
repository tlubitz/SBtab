#!/usr/bin/python
import re
import string
import libsbml
import numpy
import scipy
import scipy.linalg
import scipy.optimize
import random
import copy
import math
import os

try: from . import SBtab
except: import SBtab

def count_tabs(sbtab_string):
    '''
    count how many SBtabs are in in this string
    '''
    counter = 0
    for row in sbtab_string.split('\n'):
        if row.startswith('!!SBtab'):
            counter += 1
    return counter


def validate_file_extension(file_name, file_type):
    '''
    returns Boolean to evaluate if the file has the correct extension:
    sbml => xml
    sbtab => tsv, csv, xlsx
    '''
    # check extension for sbml file
    if file_type == 'sbml' and file_name[-3:] == 'xml': return True
    elif file_type == 'sbml': return False
    else: pass

    # check extension for sbtab file
    if file_type == 'sbtab' and file_name[-3:] == 'tsv': return True
    elif file_type == 'sbtab' and file_name[-3:] == 'csv': return True
    elif file_type == 'sbtab' and file_name[-4:] == 'xlsx': return True
    elif file_type == 'sbtab': return False
    else: pass

    # if something is completely off, return False
    return False


def check_delimiter(sbtab_file):
    '''
    determine the delimiter of the tabular file
    '''
    sep = False

    try:
        for row in sbtab_file.split('\n'):
            if row.startswith('!!'): continue
            if row.startswith('!'):
                s = re.search('(.)(!)', row[1:])
                # if there is only 1 column, we have to define a default separator
                # let's use a tab.
                try: sep = s.group(1)
                except: sep = '\t'
    except: pass

    return sep


def split_sbtabs(sbtab_strings):
    '''
    cuts an large SBtab string in single SBtab strings if necessary
    '''
    sbtabs = []
    sbtab_string = ''
    counter = 1
    
    for row in sbtab_strings.split('\n'):
        if row.startswith('!!'):
            if sbtab_string == '':
                sbtab_string = row + '\n'
                continue
            else:
                try:
                    sbtabs.append(sbtab_string)
                    sbtab_string = row + '\n'
                    counter += 1
                except:
                    print('Warning: Could not write SBtab %s' % counter)
                    counter += 1
        else:
            sbtab_string += row + '\n'
    sbtabs.append(sbtab_string) 
                    
    return sbtabs


def tsv_to_html(sbtab, filename=None):
    '''
    generates html view out of tsv file
    '''
    # read in header and footer from HTML template
    html_template = open('template.html', 'r').read()
    try:
        header = re.search('(<html lang="en">.*style="padding-top:50px">)', html_template, re.DOTALL).group(0)
        footer = re.search('(</table>.*</html>)', html_template, re.DOTALL).group(0)
    except:
        print('Cannot read required template.html.')
    html_template.close()
    html = header

    # read in definitions file for nice mouse over
    try_paths = ['definitions.tsv',
                 os.path.join(os.path.dirname(__file__), '../static/files/default_files/definitions.tsv'),
                 os.path.join(os.path.dirname(__file__), '../definition_table/definitions.tsv'),
                 os.path.join(os.path.dirname(__file__), 'definitions.tsv')]

    for path in try_paths:
        try:
            def_file = open(path, 'r')
            break
        except: pass

    sbtab_def = SBtab.SBtabTable(def_file.read(), 'definitions.tsv')

    # now build the html file
    if sbtab.object_type == 'table':
        # finish header with title
        try:
            sbtab = sbtab.to_str().split('\n')
            html += '<h2><small>%s</small></h2></div></header>' % sbtab.filename
            delimiter = sbtab.delimiter
        except:
            print('SBtab object cannot be read properly. Is it valid?')

        # start main
        html += '<main><table class="table-striped">'

        # header row
        html += '<tr><th colspan="%s">%s</th></tr>' % (len(sbtab.columns), sbtab.header_row)

        # columns
        html += '<tr>'
        for col in sbtab.columns:
            html += '<th>%s</th>' % col
        html += '</tr>'

        # value rows
        for row in sbtab.value_rows:
            html += '<tr>'
            for col in row:
                html += '<td>%s</td>' % col
            html += '</tr>'

        # comment rows
        for row in sbtab.comments:
            html += '<tr>'
            for col in row:
                html += '<td>%s</td>' % col
            html += '</tr>'

        # close table
        html += '</table>'

    elif sbtab.object_type == 'doc':
        pass
        
    else:
        print('The given SBtab object is invalid.')
            
    html += footer
    
    return html


def xlsx_to_tsv(file_object):
    '''
    convert xlsx SBtab file to tsv format
    '''
    import openpyxl
    from io import BytesIO
    
    wb = openpyxl.load_workbook(filename = BytesIO(file_object))
    ws = wb.active
    ranges = wb[ws.title]
    table_string = ''

    for row in ranges:
        for column in row:
            if str(row[0].value).startswith('!'):
                if column.value != None and str(column.value) != '':
                    table_string += str(column.value) + '\t'
            else:
                table_string += str(column.value) + '\t'
        table_string = table_string[:-1] + '\n'
        
    return table_string


def tab_to_xlsx(sbtab_object):
    '''
    converts SBtab object to xlsx file object
    '''
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    
    ws['A1'] = sbtab_object.header_row
    ws.append(sbtab_object.columns)
    for row in sbtab_object.value_rows:
        ws.append(row)

    wb.save('transition.xlsx')
    
    fileobject = open('transition.xlsx','rb')

    return fileobject.read()


urns = ["obo.chebi","kegg.compound","kegg.reaction","obo.go","obo.sgd","biomodels.sbo","ec-code","kegg.orthology","uniprot","hmdb"]

def csv2html(sbtab_file,file_name,delimiter,sbtype,def_file=None,def_file_name=None):
    '''
    generates html view out of csv file
    '''
    # remove validator here; not required anymore
    # improve interface: provide SBtab, use sbtab.delimiter
    if def_file:
        FileValidClass = validatorSBtab.ValidateFile(def_file,def_file_name)
        def_delimiter  = FileValidClass.checkseparator()
    else:
        def_file_open = open('./definitions/definitions.tsv','r')
        def_file      = def_file_open.read()
        def_delimiter = '\t'

    col2description = findDescriptions(def_file,def_delimiter,sbtype)

    sbtab = sbtab_file.split('\n')
    nice_sbtab = '<p><h2><b>'+file_name+'</b></h2></p>'
    nice_sbtab += '<a style="background-color:#00BFFF">'+sbtab[0]+'</a><br>'
    nice_sbtab += '<table>'

    ident_url  = False
    ident_cols = []
    col2urn    = {}

    for row in sbtab[1:]:
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
            
def extract_supported_table_types():
    '''
    extracts all allowed SBtab TableTypes from the definition file
    '''
    try_paths = ['definitions.tsv',
                 os.path.join(os.path.dirname(__file__), '../static/files/default_files/definitions.tsv'),
                 os.path.join(os.path.dirname(__file__), '../definition_table/definitions.tsv'),
                 os.path.join(os.path.dirname(__file__), 'definitions.tsv')]

    for path in try_paths:
        try:
            def_file = open(path, 'r')
            break
        except:
            pass

    sbtab_def = SBtab.SBtabTable(def_file.read(), 'definitions.tsv')
    supported_types = []
    for row in sbtab_def.value_rows:
        t = row[sbtab_def.columns_dict['!IsPartOf']]
        if t not in supported_types:
            supported_types.append(t)

    return supported_types
