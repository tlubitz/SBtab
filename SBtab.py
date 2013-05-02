#!/usr/bin/env python
import re
import copy
import tablib
from tablibIO import *


no_name_tables = []


def oneOrMany(sbtab_document):
    '''
    this extra function is supposed to check whether there are one or many SBtabs in an SBtab document.
    it returns a list of SBtab strings
    '''
    sbtabs = []
    rows = []
    starts = []

    # get starting points
    for i, row in enumerate(sbtab_document):
        rows.append(row)
        if row.startswith('!!'):
            starts.append(i)
        elif re.search('TableType="([^"])*"', row):
            starts.append(i)
        elif re.search('Table="([^"])*"', row):
            starts.append(i)
    starts.append(i + 1)
    end_of_file = i + 1

    if len(starts) == 0:
        return None
    elif len(starts) == 1:
        return sbtab_document
    elif len(starts) > 1:
        for i, start_point in enumerate(starts):
            if start_point == end_of_file:
                break
            single_sbtab = []
            for j in range(starts[i], starts[i + 1]):
                single_sbtab.append(rows[j])
            sbtabs.append(single_sbtab)

    return sbtabs


class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class SBtabTable():
    '''
    SBtab Table (v9 02/13)
    '''
    def __init__(self, table, filename, table_type=None):
        '''
        initialize the SBtab table
        @table: array of strings
        @filename: string
        '''
        self.filename = filename  # needed to be able to adress it from outside of the class for writing and reading stuff

        # identification of seperator (tsv/csv/ods/xls)
        if not str(filename).endswith('.tsv') or str(filename).endswith('.csv') or str(filename).endswith('.ods') or str(filename).endswith('.xls'):
            raise SBtabError('The given file format is not supported: ' + filename + '. Please use ".tsv", ".csv", ".ods" or ".xls" instead.')

        # reading the whole spreadsheet in a list line by line (self.table_rows)
        # this is mainly done to exclude empty lines

        self.table_rows = []
        for row in table:
            if not row.rstrip() == ['']:
                self.table_rows.append(row)

        # reading the header row (self: table_type, table_name, table_document,
        # table_version, table_level)
        self.getHeaderRow()
        # reading the column names (initialize columns) (self.column_names)
        self.getColumns()

        # reading subcolumns (not obligate) (self.column_property_rows)
        try:
            self.getColumnProperties()
        except:
            raise SBtabError(
                'The specification row of the SBtab is invalid (see example files again).')

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

    def makeExMarks(self):
        '''
        if column names are given without exclamation marks (old format), add them automatically.
        '''
        new_rows = []
        for row in self.table_rows:
            if row.startswith('QuantityType'):
                old_column_row = row.split(self.separator)
                new_column_row = []
                for item in old_column_row:
                    new_column_row.append('!' + item)
                new_rows.append(self.separator.join(new_column_row))
            else:
                new_rows.append(row)
        self.table_rows = new_rows
        # needed anymore??

    def getHeaderRow(self):
        '''
        extracts the !!-header row from the SBtab file and its information
        if no_name was set, name equals table_type and number of occurance
        '''
        self.header_row = None
        global no_name_tables
        no_name_count = 0

        for row in self.table_rows:
            if row.startswith('!!'):
                self.header_row = row

        try:
            self.table_type = re.search(
                'TableType="([^"]*)"', self.header_row).group(1)
        except:
            raise SBtabError('The TableType of the SBtab is not defined!')

        try:
            self.table_name = re.search(
                'Table="([^"]*)"', self.header_row).group(1)
        except:
            no_name_tables.append(self.table_type)
            for table_no_name in no_name_tables:
                if self.table_type == table_no_name:
                    no_name_count = no_name_count + 1
            self.table_name = self.table_type.capitalize() + str(no_name_count)

        try:
            self.table_document = re.search(
                'Document="([^"]*)"', self.header_row).group(1)
        except:
            self.table_document = None

        try:
            self.table_level = re.search(
                'Level="([^"]*)"', self.header_row).group(1)
        except:
            self.table_level = None

        try:
            self.table_version = re.search(
                'Version="([^"]*)"', self.header_row).group(1)
        except:
            self.table_version = None

    def getColumns(self):
        '''
        extract the column names of the SBtab
        '''
        # main_name = '!'+self.table_type.capitalize()
        for row in self.table_rows:
            if row.startswith('!') and not row.startswith('!!'):
                self.column_names = row.split(self.separator)
                break

        # insert mandatory first column if not existent
        self.inserted_column = 0
        if not self.column_names[0] == '!' + self.table_type.capitalize():
            self.column_names.insert(0, '!' + self.table_type.capitalize())
            self.inserted_column = 1

    def getColumnProperties(self):
        '''
        extract the subcolumns of the SBtab
        '''
        main_name = '!' + self.table_type.capitalize()
        self.column_property_rows = []
        for row in self.table_rows:
            if row.startswith('!') and not row.startswith(main_name) and not row.startswith('!!'):
                self.column_property_rows.append(row.split(self.separator))
            else:
                break

    def getRows(self):
        '''
        extract the rows of the SBtab
        '''
        self.value_rows = []
        for row in self.table_rows:
            split_row = row.split(self.separator)
            if not row.startswith('!') and not row.startswith(' ') and not row == '':
                # if len(split_row) == len(self.column_names):
                self.value_rows.append(split_row)
        # insert value column if mandatory column was added
        if self.inserted_column == 1:
            for i, row in enumerate(self.value_rows):
                row.insert(0, self.table_type[0].capitalize(
                ) + self.table_type[- 1].lower() + str(i + 1))

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

    def createSBtab(self):
        '''
        write the python object into a SBtab file, tsv format
        '''
