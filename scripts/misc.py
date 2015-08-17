#!/usr/bin/python
import re

def first_row(sbtab_content,delimiter):
    '''
    revokes a problem in the SBtab/tablib interface: tablib requires all rows to be
    equally long, but SBtab wants (especially for the export) only one element in
    the first row.
    '''
    splitt =  sbtab_content.split('\n')
    new_content = ''
    for i,row in enumerate(splitt):
        splitrow = row.split(delimiter)
        if i == 0: new_content += splitrow[0]+'\n'
        else: new_content += delimiter.join(splitrow)+'\n'

    return new_content

def create_filename(sbtab_name, table_type, table_name):
    '''
    creates a unique identifying name for an uploaded sbtab file to be displayed in the interface.
    '''
    if table_name != '':
        if not table_type.lower() in sbtab_name[:-4].lower(): filename = sbtab_name[:-4]+'_'+table_type+'_'+table_name
        else: filename  = sbtab_name[:-4]+'_'+table_name
    else:
        if not table_type.lower() in sbtab_name[:-4].lower(): filename = sbtab_name[:-4]+'_'+table_type
        else: filename  = sbtab_name[:-4]

    return filename

def csv2xls(sbtab_file,delimiter):
        '''
        converts sbtab file to xls file
        @sbtab_file: sbtab string
        '''
        import xlwt
        import tempfile
        
        book  = xlwt.Workbook()
        sheet = book.add_sheet('Sheet 1')

        split_sbtab_file = sbtab_file.split('\n')

        first_row = sheet.row(0)
        first_row.write(0,split_sbtab_file[0])

        for i,row in enumerate(split_sbtab_file[1:]):
            new_row   = sheet.row(i+1)
            split_row = row.split(delimiter)
            for j,element in enumerate(split_row):
                new_row.write(j,element)

        #if something is stupid and it works
        #then it is not stupid:
        book.save('simple.xls')
        fileobject = open('simple.xls','r')

        return fileobject

def getDelimiter(sbtab_file_string):
    '''
    check the sbtab file for a delimiter
    '''
    try: rows = sbtab_file_string.split('\n')
    except: rows = sbtab_file_string
    
    for row in rows:
        if row.startswith('!!'): continue
        elif row.startswith('"!!'): continue
        if row.startswith('!'):
            s = re.search('(.)(!)',row)
            #if there is only one column, we have to define a default separator.
            #let's use a tab, because it's most common. Doesn't matter anyway.
            try: sep = s.group(1)
            except: sep = '\t'

    return sep

def removeDoubleQuotes(sbtab_file_string):
    '''
    remove quotes and double quotes introduced by fucking MS Excel
    '''
    try: rows = sbtab_file_string.split('\n')
    except: rows = sbtab_file_string

    sbtab = []
    for row in rows:
        n1 = row.replace('""','#')
        if n1.startswith('!!'): n2 = n1
        else: n2 = n1.replace('"','')
        new_row = n2.replace('#','"')
        sbtab.append(new_row)

    new_sbtab = '\n'.join(sbtab)

    return new_sbtab
            
            
        
