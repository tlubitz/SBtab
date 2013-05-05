#!/usr/bin/env python
import re
import copy
import tablib
from tablibIO import *


no_name_tables = []


def oneOrMany(spreadsheet_file):
    '''
    this extra function is supposed to check whether there are one or many SBtabs in an SBtab document.
    it returns a list of SBtab strings
    '''
    sbtabs = []

    # copy file, one for iteration, one for cutting
    sbtab_document = copy.deepcopy(spreadsheet_file)
    # create new tablib object
    sbtab = tablib.Dataset()

    # cutting sbtab_document, write tablib objects in list
    if len(spreadsheet_file) != 0:  # if file not empty
        for row in spreadsheet_file:
            if len(sbtab) == 0:  # if first line, append line w/o checking
                sbtab.rpush(sbtab_document.lpop())
            else:
                for i, entry in enumerate(row):
                    # if header row (!!), write to new tablib object and store the last one
                    if entry.startswith('!!'):
                        sbtabs.append(sbtab)
                        sbtab = tablib.Dataset()
                        sbtab.rpush(sbtab_document.lpop())
                        break
                    # if not header row, append line to tablib object
                    if len(row) == i + 1:
                        sbtab.rpush(sbtab_document.lpop())
        sbtabs.append(sbtab)

    # return list of tablib objects
    return sbtabs


class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class SBtabTable():
    '''
    SBtab Table (v0 05/03/2013)
    '''
    def __init__(self, table, filename, table_type=None):
        '''
        initialize the SBtab table
        @table: array of strings
        @filename: string
        '''
        self.filename = filename  # needed to be able to adress it from outside of the class for writing and reading stuff
        self.table = table

        # identification of seperator (tsv/csv/ods/xls)
        if not (str(filename).endswith('.tsv') or str(filename).endswith('.csv') or str(filename).endswith('.ods') or str(filename).endswith('.xls')):
            raise SBtabError('The given file format is not supported: ' + filename + '. Please use ".tsv", ".csv", ".ods" or ".xls" instead.')

        # reading the header row (self: table_type, table_name, table_document, table_version, table_level)
        self.getHeaderRow()
        if not self.header_row:
            raise SBtabError('This is not a valid SBtab table, please use validator to check format!')

        # reading the column names (initialize columns) (self.column_names)
        self.getColumns()

        # reading subcolumns (not obligate) (self.column_property_rows)
        # TODO: needed anymore??
        # try:
        #     self.getColumnProperties()
        # except:
        #     raise SBtabError('The specification row of the SBtab is invalid (see example files again).')

        # reading rows (self.value_rows)
        self.getRows()
        # reading the position of the valid columns (self.ini_columns)
        self.initializeColumns()
        # read out the column values by column name
        print self.table_name
        for column in self.ini_columns:
            print 'Column: ' + column
            print 'Position: ' + str(self.ini_columns[column])
            print 'Values: '
            for valcol in self.value_rows:
                try:
                    if valcol[self.ini_columns[column]].rstrip('\n') == '':
                        valcol[self.ini_columns[column]] = None
                        print 'None'
                    elif valcol[self.ini_columns[column]].rstrip('\n') == '?':
                        valcol[self.ini_columns[column]] = None
                        print 'None'
                    elif valcol[self.ini_columns[column]].rstrip('\n').lower() == 'na':
                        valcol[self.ini_columns[column]] = None
                        print 'None'
                    elif valcol[self.ini_columns[column]].rstrip('\n').lower() == 'nan':
                        valcol[self.ini_columns[column]] = None
                        print 'None'
                    else:
                        print valcol[self.ini_columns[column]].rstrip('\n')
                except:
                    print 'None'

        # read out the column values by first column
        self.value_by_first = {}
        for row in self.value_rows:
            self.value_by_first[row[0]] = row[1:]
        print self.value_by_first

        self.createSBtab('tsv')

    def getHeaderRow(self):
        '''
        extracts the !!-header row from the SBtab file and its information
        if no_name was set, name equals table_type and number of occurance
        '''
        self.header_row = None
        global no_name_tables
        no_name_count = 0

        for row in self.table:
            for entry in row:
                if entry.startswith('!!'):
                    self.header_row = row
                    break

        if not self.header_row:
            return None
        else:
            self.header_row = ' '.join(self.header_row)

        try:
            self.table_type = re.search('TableType="([^"]*)"', self.header_row).group(1)
        except:
            raise SBtabError('The TableType of the SBtab is not defined!')

        try:
            self.table_name = re.search('Table="([^"]*)"', self.header_row).group(1)
        except:
            no_name_tables.append(self.table_type)
            for table_no_name in no_name_tables:
                if self.table_type == table_no_name:
                    no_name_count = no_name_count + 1
            self.table_name = self.table_type.capitalize() + '_' + str(no_name_count)

        try:
            self.table_document = re.search('Document="([^"]*)"', self.header_row).group(1)
        except:
            self.table_document = None

        try:
            self.table_level = re.search('Level="([^"]*)"', self.header_row).group(1)
        except:
            self.table_level = None

        try:
            self.table_version = re.search('Version="([^"]*)"', self.header_row).group(1)
        except:
            self.table_version = None

    def getColumns(self):
        '''
        extract the column names of the SBtab
        '''
        for row in self.table:
            for entry in row:
                if entry.startswith('!') and not entry.startswith('!!'):
                    self.column_names = list(row)
                    break

        # insert mandatory first column if not existent
        self.inserted_column = False
        if not self.column_names[0].title() == '!' + self.table_type.title():
            self.column_names.insert(0, '!' + self.table_type.title())
            self.inserted_column = True

    def getColumnProperties(self):
        '''
        extract the subcolumns of the SBtab
        '''
        # TODO: Needed??
        main_name = '!' + self.table_type.title()
        self.column_property_rows = []
        for row in self.table:
            for entry in row:
                if entry.startswith('!') and not entry.startswith('!' + main_name) and not entry.startswith('!!'):
                    self.column_property_rows = list(row)
                    break

    def getRows(self):
        '''
        extract the rows of the SBtab
        '''
        self.value_rows = []
        for row in self.table:
            for i, entry in enumerate(row):
                if not entry.startswith('!'):
                    if len(row) == i + 1:
                        self.value_rows.append(list(row))
        # insert value column if mandatory column was added
        if self.inserted_column is True:
            for i, row in enumerate(self.value_rows):
                row.insert(0, self.table_type[0].upper() + self.table_type[- 1].lower() + str(i + 1))

    def initializeColumns(self):
        '''
        initialize columns for the SBtab table
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
                self.ini_columns[column] = i

    def changeValue(self, row, column, new):
        '''
        change single value in the SBtab
        '''
        pass

    def createSBtab(self, format_type):
        '''
        write the python object into a SBtab file
        '''
        sbtab_file = tablib.Dataset()
        header = self.header_row.split(' ')

        header = [x.strip(' ') for x in header]
        self.column_names = [x.strip(' ') for x in self.column_names]
        for row in self.value_rows:
            for entry in row:
                if not entry:
                    entry = ''
            row = [x.strip(' ') for x in row]

        if len(self.column_names) < len(header):
            dif = len(header) - len(self.column_names)
            for i in range(dif - 1):
                self.column_names = self.addEntry(self.column_names)
        if len(self.column_names) > len(header):
            dif = len(self.column_names) - len(header)
            for i in range(dif - 1):
                header = self.addEntry(header)

        sbtab_file.lpush(header)
        sbtab_file.lpush(self.column_names)
        tablibIO.writeTSV(sbtab_file)

    def addEntry(self, list_row):
        '''
        add empty entry at the end of a list
        '''
        row.append('')

        return list_object

    def delEntry(self, list_row):
        '''
        delete empty entry at the end of a list
        '''
        for entry in enumerate(list_row):
            if len(list_row) == i + 1:
                if entry == '':
                    del row[i]

        return list_object
