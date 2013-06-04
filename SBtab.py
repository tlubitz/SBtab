#!/usr/bin/env python
import re
import copy
import tablib
import tablibIO

no_name_tables = []


def oneOrMany(spreadsheet_file):
    '''
    this extra function is supposed to check whether there are one or many SBtabs in an SBtab document.
    it returns a list of SBtab strings
    @param spreadsheet_file: file containing sbtabs
    @type spreadsheet_file: tablib object
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
    SBtab Table (v1 05/11/2013)
    '''
    def __init__(self, table, filename):
        '''
        initialize the SBtab table
        @param table: one sbtab
        @type table: tablib object
        @param filename: name of file that contains sbtab, with extension
        @type filename: string

        Raise error if file format is invalid, only 'tsv', 'csv', 'ods' or 'xls'
        '''
        self.filename = filename  # needed to be able to adress it from outside of the class for writing and reading stuff
        self.table = table

        # identification of file type (tsv/csv/ods/xls)
        if not (str(filename).endswith('.tsv') or str(filename).endswith('.csv') or str(filename).endswith('.ods') or str(filename).endswith('.xls')):
            raise SBtabError('The given file format is not supported: ' + filename + '. Please use ".tsv", ".csv", ".ods" or ".xls" instead.')

        # reading the header row (self: table_type, table_name, table_document, table_version, table_level)
        self.getHeaderRow()

        # reading the column names (initialize columns) (self.column_names)
        self.getColumns()

        # reading subcolumns (not obligate) (self.column_property_rows)
        # TODO: needed anymore??
        # try:
        #     self.getColumnProperties()
        # except:
        #     raise SBtabError('The specification row of the SBtab is invalid (see example files again).')

        # reading data rows (self.value_rows)
        self.getRows()
        # reading the position of the valid columns (self.ini_columns)
        self.initializeColumns()
        # create tablib Dataset instance with new sbtab table
        self.createSBtabDataset()

    def getHeaderRow(self):
        '''
        extracts the !!-header row from the SBtab file and its information
        if no name was set, name equals table_type and number of unnamed tables of same type

        string header_row
        string table_type
        string table_name
        string/None table_document
        string/NOne table_level
        string/None table_version

        Raise error if no header row in the table or no table type defined
        '''
        # initialise variables
        self.header_row = None
        global no_name_tables
        no_name_count = 0

        # find header row
        for row in self.table:
            for entry in row:
                if entry.startswith('!!'):
                    self.header_row = row
                    break

        # save string or return None
        if not self.header_row:
            raise SBtabError('This is not a valid SBtab table, please use validator to check format!')
        else:
            self.header_row = ' '.join(self.header_row)

        # replace double quotes by single quotes
        self.header_row = self.header_row.replace('"', '\'')

        # save TableType, otherwise raise Error
        try:
            self.table_type = re.search('TableType=\'([^\']*)\'', self.header_row).group(1)
        except:
            raise SBtabError('The TableType of the SBtab is not defined!')

        # save TableName, otherwise handle number of unnamed tables
        try:
            self.table_name = re.search('Table=\'([^\']*)\'', self.header_row).group(1)
        except:
            no_name_tables.append(self.table_type)
            for table_no_name in no_name_tables:
                if self.table_type == table_no_name:
                    no_name_count = no_name_count + 1
            self.table_name = self.table_type.capitalize() + '_' + str(no_name_count)

        # save TableDocument, otherwise return None
        try:
            self.table_document = re.search('Document=\'([^\']*)\'', self.header_row).group(1)
        except:
            self.table_document = None

        # save TableLevel, otherwise return None
        try:
            self.table_level = re.search('Level=\'([^\']*)\'', self.header_row).group(1)
        except:
            self.table_level = None

        # save TableVersion, otherwise return None
        try:
            self.table_version = re.search('Version=\'([^\']*)\'', self.header_row).group(1)
        except:
            self.table_version = None

    def getColumns(self):
        '''
        extract the column names of the SBtab, add first column name if necessary

        list column_names
        True/False inserted_column
        '''
        # save list of main column
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
        extract the rows of the SBtab, add first column if necessary

        list value_rows
        '''
        # add row to value_rows if row does'nt contain entries starting with '!'
        self.value_rows = []
        for row in self.table:
            for i, entry in enumerate(row):
                if entry.startswith('!'):
                    break
                else:
                    if len(row) == i + 1:
                        self.value_rows.append(list(row))
        # insert value column if mandatory column was added
        if self.inserted_column is True:
            for i, row in enumerate(self.value_rows):
                row.insert(0, self.table_type[0].upper() + self.table_type[- 1].lower() + str(i + 1))

    def initializeColumns(self):
        '''
        initialize columns for the SBtab table

        dict ini_columns
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
                self.ini_columns[column] = i

    def changeValue(self, row, column, new):
        '''
        change single value in the SBtab

        @param row: number of row to change
        @type row: integer
        @param column: number of column to change
        @type column: integer
        @param new: new entry
        @type new: String
        '''
        self.value_rows[row - 1][column - 1] = new

    def changeValueByName(self, row, column, new):
        '''
        change singe value in the SBtab by name of column and row

        @param row: name of entry in first column
        @type row: String
        @param column: name in main column
        @type column: String
        @paran new: new entry
        @type new: String
        '''
        col = self.ini_columns['!' + column]
        for r in self.value_rows:
            for entry in r:
                if entry == row:
                    r[col] = new

    def createSBtabDataset(self):
        '''
        create a tablib object of the SBtab file

        list sbtab_temp
        tablib.Dataset sbtab_dataset
        '''
        # initialise variables
        sbtab_temp = []
        self.sbtab_dataset = tablib.Dataset()
        header = self.header_row.split(' ')

        # delete spaces in header, main column and data rows
        header = [x.strip(' ') for x in header]
        self.column_names = [x.strip(' ') for x in self.column_names]
        for row in self.value_rows:
            try:
                for entry in row:
                    entry = entry.strip(' ')
            except:
                continue

        # add header, main column and data rows to temporary list object
        sbtab_temp.append(header)
        sbtab_temp.append(self.column_names)
        for row in self.value_rows:
            sbtab_temp.append(row)

        # delete all empty entries at the end of the rows
        for row in sbtab_temp:
            while not row[-1]:
                del row[-1]

        # make all rows the same length
        longest = max([len(x) for x in sbtab_temp])
        for row in sbtab_temp:
            if len(row) < longest:
                for i in range(longest - len(row)):
                    row.append('')
                self.sbtab_dataset.append(row)
            else:
                self.sbtab_dataset.append(row)

    def addRow(self, row_list, position=None):
        '''
        add row to the table, if postion is None at the end

        @param row_list: entries in new row
        @type row_list: list of Strings
        @param position: position of new row in table
        @type position: integer (0 = top)
        '''
        # empty column to fill up sbtab_dataset
        empty_list = []

        # if new row is to small, add empty entries to new row
        if len(row_list) < len(self.sbtab_dataset.dict[0]):
            for i in range(len(self.sbtab_dataset.dict[0]) - len(row_list)):
                row_list.append('')
        # if new row is to long, add empty entries to sbtab_dataset
        elif len(row_list) > len(self.sbtab_dataset.dict[0]):
            for i in range(len(self.sbtab_dataset.dict)):
                empty_list.append('')
            for i in range(len(row_list) - len(self.sbtab_dataset.dict[0])):
                self.sbtab_dataset.rpush_col(empty_list)
        # if no position is set, add new row to the end
        if not position:
            self.sbtab_dataset.rpush(row_list)
        else:
            self.sbtab_dataset.insert(position, row_list)

    def addColumn(self, column_list, position=None):
        '''
        add column to the table, if position is None at the end

        @param column_list: entries in new column
        @type column_list: list of Strings
        @param position: position of new column in table_name
        @type position: integer (0 = left)
        '''
        # empty column to fill up sbtab_dataset
        empty_list = []

        # if new column is to small, add empty entries to new column
        if len(column_list) < len(self.sbtab_dataset.dict):
            for i in range(len(self.sbtab_dataset.dict) - len(column_list)):
                column_list.append('')
        # if new column is to long, add empty entries to sbtab_dataset
        elif len(column_list) > len(self.sbtab_dataset.dict):
            for i in range(len(self.sbtab_dataset.dict)[0]):
                empty_list.append('')
            for i in range(len(column_list) - len(self.sbtab_dataset.dict[0])):
                self.sbtab_dataset.rpush(empty_list)
        # if no position is set, add new column to the end
        if not position:
            self.sbtab_dataset.rpush_col(column_list)
        else:
            self.sbtab_dataset.insert_col(position, column_list)

    def writeSBtab(self, format_type, filename, sbtab_dataset):
        '''
        write SBtab tablib object to file

        @param format_type: spreadsheet format and extension for file
        @type format_type: String
        @param filename: filename without ending (will be created)
        @type filename: String
        @param sbtab_dataset: sbtab table
        @type sbtab_dataset: tablib object

        Raise error if file format is invalid
        '''
        if format_type == 'tsv':
            tablibIO.writeTSV(sbtab_dataset, self.table_name)
        elif format_type == 'csv':
            tablibIO.writeCSV(sbtab_dataset, self.table_name)
        elif format_type == 'ods':
            tablibIO.writeODS(sbtab_dataset, self.table_name)
        elif format_type == 'xls':
            tablibIO.writeXLS(sbtab_dataset, self.table_name)
        else:
            raise SBtabError('The given file format is not supported: ' + filename + '. Please use ".tsv", ".csv", ".ods" or ".xls" instead.')
