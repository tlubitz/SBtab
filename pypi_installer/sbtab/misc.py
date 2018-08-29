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
    if type(sbtab) == str and filename:
        ugly_sbtab = sbtab.split('\n')
        nice_sbtab = '<p><h2><b>%s</b></h2></p>' % filename
        delimiter = check_delimiter(sbtab)
    else:
        ugly_sbtab = sbtab.return_table_string().split('\n')
        nice_sbtab = '<p><h2><b>'+sbtab.filename+'</b></h2></p>'
        delimiter = sbtab.delimiter

    first = True
    for row in ugly_sbtab:
        if row.startswith('!!') and first:
            nice_sbtab += '<a style="background-color:#00BFFF">'+row+'</a><br>'
            nice_sbtab += '<table>'
            first = False
        elif row.startswith('!!'):
            nice_sbtab += '</table>'
            nice_sbtab += '<a style="background-color:#00BFFF">'+row+'</a><br>'
            nice_sbtab += '<table>'
        elif row.startswith('!'):
            nice_sbtab += '<tr bgcolor="#87CEFA">'
            splitrow = row.split(delimiter)
        elif row.startswith('%'):
            nice_sbtab += '<tr bgcolor="#C0C0C0">'
        elif row.startswith('Parameter balancing log file'):
            nice_sbtab += '<table><tr>'
        else: nice_sbtab += '<tr>'
        
        for i,thing in enumerate(row.split(delimiter)):
            if thing.startswith('!!'): continue
            new_row = '<td>'+str(thing)+'</td>'
            nice_sbtab += new_row
        nice_sbtab += '</tr>'
    nice_sbtab += '</table>'     

    return nice_sbtab  


def tsv_to_html_improved(sbtab, filename=None):
    '''
    generates html view out of tsv file
    '''
    sbtab_html = '''
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="author" content="Timo Lubitz">
    <meta name="description"  content="Parameter Balancing Website">
    
    <!-- this is required for responsiveness -->
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>Parameter Balancing for Kinetic Models of Cell Metabolism</title>
    <!--<link rel="stylesheet" type="text/css" href="css/pb.css">-->
    <link href="../../static/css/css_template/css/bootstrap.min.css" rel="stylesheet">
    <link href="../../static/css/css_template/css/custom.css" rel="stylesheet">
    <link rel="shortcut icon" href="/pb/static/css/css_template/img/pb-logo.png" type="image/icon">
    <link rel="icon" href="/pb/static/css/css_template/img/pb-logo.png" type="image/icon">
    </head>

    <body>
    <!-- navbar: this is a navbar; navbar-inverse: it's dark; navbar-static-top: it's always at the top -->
    <nav class="navbar navbar-inverse navbar-fixed-top">
    <!-- setting a max-width by using a container -->
      <div class="container">
        <div class="navbar-header">
	  <!-- button is hidden on desktop, becomes a hamburger on mobile! the span items are the hamburger lines --> 
	  <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
	    <span class="sr-only">Toggle navigation</span>
	    <span class="icon-bar"></span>
	    <span class="icon-bar"></span>
	    <span class="icon-bar"></span>
	  </button>
	  <a class="navbar-brand" href="#">Parameter Balancing</a>
	</div>
	
	<!-- simple right aligned list-->
	<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
	  <ul class="nav navbar-nav navbar-right">
	    <li> <a href="../../default/balancing.html" title="Go to online balancing">Online Balancing</a></li>
	    <li> <a href="../../static/css/css_template/documentation.html" title="Documentation and Manuals">Documentation</a></li>
	    <li> <a href="../../static/css/css_template/download.html" title="Installation and Downloads">Download</a></li>
	    <li> <a href="../../static/css/css_template/contact.html" title="Contact the balancing team">Contact</a></li>
	  </ul>
	</div>
      </div>
    </nav>

    <header>
    <div class="container-fluid bg-1 text-center" style="padding-top:50px">

    '''    
    if type(sbtab) == str and filename:
        ugly_sbtab = sbtab.split('\n')
        #nice_sbtab = '<p><h2><b>%s</b></h2></p>' % filename
        sbtab_html += '<h2><small>%s</small></h2></div></header>'
        delimiter = check_delimiter(sbtab)
    else:
        ugly_sbtab = sbtab.return_table_string().split('\n')
        #nice_sbtab = '<p><h2><b>'+sbtab.filename+'</b></h2></p>'
        sbtab_html += '<h2><small>'+sbtab.filename+'</small></h2></div></header>'
        delimiter = sbtab.delimiter

    sbtab_html += '<main><table class="table-striped">'
        
    first = True
    for i, row in enumerate(ugly_sbtab):
        # declaration of first SBtab in document
        if row.startswith('!!') and first:
            sbtab_html += '<tr><th colspan="%s">%s</th></tr>' % (len(ugly_sbtab[i+2]), row)
            first = False

        # conclusion of SBtab and beginning of new SBtab (if there are more than one)
        elif row.startswith('!!'):
            sbtab_html += '</table><table class="table-striped">'
            sbtab_html += '<tr><th colspan="%s">%s</th></tr>' % (len(ugly_sbtab[i+2]), row)

        # column header row
        elif row.startswith('!'):
            splitrow = row.split(delimiter)
            sbtab_html += '<tr>'
            for col in splitrow:
                sbtab_html += '<th>%s</th>' % col
            sbtab_html += '</tr>'

        # comment row
        elif row.startswith('%'):
            sbtab_html += '<tr bgcolor="#C0C0C0">%s</tr>' % row

        # log file header
        elif row.startswith('Parameter balancing log file'):
            sbtab_html += '<tr>%s</tr>'

        # normal row
        else:
            splitrow = row.split(delimiter)
            sbtab_html += '<tr>'
            for col in splitrow:
                sbtab_html += '<td>%s</td>' % col
            sbtab_html += '</tr>'

        '''
        # normal row
        for i,thing in enumerate(row.split(delimiter)):
            if thing.startswith('!!'): continue
            #new_row = '<td>'+str(thing)+'</td>'
            #nice_sbtab += new_row
        #nice_sbtab += '</tr>'
        '''
    sbtab_html += '''
    </table>
    </main>
    <hr>
    <footer class="container-fluid bg-3 text-center">
    <p>Thanks to <a href="https://getbootstrap.com/" target="_blank">Bootstrap</a> and <a href="http://web2py.com/" target="_blank">Web2py</a>. Code and further information on <a href="https://github.com/tlubitz/parameter_balancing" target="_blank">Github</a>.</p> 
    </footer>
    
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="js/bootstrap.min.js"></script>
    </body>
    </html>
    '''
    return sbtab_html


def csv2xls(sbtab):
    '''
    Converts SBtab file to xls file.
    Parameters
    ----------
    sbtab_file : SBtab
       SBtab object
    '''
    import xlwt

    # open workbook
    book  = xlwt.Workbook()
    sheet = book.add_sheet('Sheet 1')

    # write header and columns
    first_row = sheet.row(0)
    first_row.write(0,sbtab.header_row)

    second_row = sheet.row(1)
    for i, element in enumerate(sbtab.columns):
        second_row.write(i, element)

    # write the rows of the SBtab
    for i, row in enumerate(sbtab.value_rows):
        new_row = sheet.row(i+2)
        for j, element in enumerate(row):
            new_row.write(j,element)

    book.save('simple.xls')
    fileobject = open('simple.xls','r')

    return fileobject


def xlsx_to_tsv(file_object):
    '''
    convert xlsx SBtab file to tsv format
    '''
    import openpyxl
    from io import BytesIO
    
    wb = openpyxl.load_workbook(filename = BytesIO(file_object))#, read_only=True)
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
    # remove validator here; not required anymore
    # improve interface: provide SBtab, use sbtab.delimiter
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
    
    print('I HAVE EXCLUDED TABLIB.XLRD HERE BECAUSE IT DOES NOT EXIST ANYMORE; GO TO MAKEHTML.PY AND FIX!')
    dbook = tablib.Databook()
    #xl = xlrd.open_workbook(file_contents=xls_sbtab)

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
            
