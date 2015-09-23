#!/usr/bin/env python
import SBtab
import tablibIO
#import SBtabDefinition
import re
import collections

class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ValidateTable:
    """
    Validator (version 0.2.0 15/02/2014)
    Check SBtab file and SBtab object.
    """
    def __init__(self, table, sbtab_name, def_table, def_name):
        """
        Initialize validator and start check for file and table format.

        Parameters
        ----------
        table : tablib object
            Tablib object of the Sbtab file
        sbtab_name : str
            File path of the Sbtab file
        """
        # import definitions from definition table
        definition_table = tablibIO.importSetNew(def_table,def_name,seperator='\t')
        definition_sbtab = SBtab.SBtabTable(definition_table, def_name)
        self.definitions = definition_sbtab.sbtab_list

        # create set of valid table types
        #self.allowed_table_types = ['Reaction', 'Gene', 'Relationship', 'Regulator', 'Enzyme', 'Compound', 'Compartment', 'Quantity']
        self.allowed_table_types = list(set([row[3] for row in self.definitions[2:][0]]))

        # create dict of valid column names per table type
        self.allowed_columns = {}
        for table_type in self.allowed_table_types:
            self.allowed_columns[table_type] = [row[1] for row in self.definitions[2:][0] if row[3] == table_type]

        # initialize warning string
        self.warnings = []
        # define self variables
        self.table = table
        self.filename = sbtab_name

        # check file format and header row
        self.checkTableFormat()

        # try creating SBtab instance
        #try:
        self.sbtab = SBtab.SBtabTable(self.table, self.filename)
        #except:
        #    raise SBtabError('The Parser cannot work with this file!')
        # remove empty column headers
        f_columns = []
        for element in self.sbtab.columns:
            if element == '': pass
            else: f_columns.append(element)
        self.sbtab.columns = f_columns

        # check SBtab object for validity
        self.checkTable()

        '''
        if len(self.warnings) > 0:
            print self.warnings
        else:
            print 'No warnings detected!'
        '''
        
    def checkTableFormat(self):
        """
        Validate format of SBtab file, check file format and header row.
        """
        # Check tablib header
        if self.table.headers:
            self.warnings.append('Tablib header is set, will be removed. This feature is not supported.')
            self.table.headers = None
        # save table rows in variable
        self.rows_file = self.table.dict

        # save header row
        header_row = self.rows_file[0]
        while '' in header_row:
            header_row.remove('')
        header = ""
        for x in header_row[:-1]:
            header += x + ' '
        header += header_row[-1]
        header = header.replace('"', "'")
        try: header = header.replace('\xe2\x80\x9d', "'")
        except: pass

        # check for valid header row
        if not header.startswith('!!'):
            self.warnings.append('The header row of the table does not start with "!!SBtab". This file cannot be validated.')
        if not re.search("TableType='([^']*)'", header):
            self.warnings.append('The attribute TableType is not defined in the SBtab table; This file cannot be validated.')
        if not re.search("TableName='([^']*)'", header):
            self.warnings.append('The attribute TableName is not defined in the SBtab table.')

        # check for possible table content and main columns
        columns_row = self.rows_file[1]
        columns = ""
        for x in columns_row[:-1]:
            columns += x + ' '
        columns += columns_row[-1]
        # check length of table
        if len(self.rows_file) < 3:
            self.warnings.append('The table contains no information: ' + \
                header)
        else:
            self.main_column_count = None
            # checks for existing main column
            if not columns.startswith('!'):
                self.warnings.append('The main column row of the table does not start with "!": ' + \
                    columns)

    def checkTable(self):
        """
        Validate the table type and mandatory format of the SBtab.
        """
        column_check = True
        # general stuff
        # 1st: check validity of table_type and save table type for later tests
        if not self.sbtab.table_type in self.allowed_table_types:
            self.warnings.append('The SBtab file has an invalid TableType in its header: ' + self.sbtab.table_type)
            column_check = False

        # 2nd: check the important first column
        if self.sbtab.unique_key == 'True':
            first_column = '!' + self.sbtab.table_type
            if not self.rows_file[1][0] == first_column:
                self.warnings.append('The first column of the file does not correspond with the given TableType ' + \
                                     self.sbtab.table_type + ' and will be filled automatically.')

            # 2,5nd: very important: check if the identifiers start with a digit; this is not allowed in SBML!
            for row in self.sbtab.value_rows:
                identifier = row[0]
                try:
                    int(identifier[0])
                    self.warnings.append('There is an identifier that starts with a digit; this is not permitted for the SBML conversion: '+identifier)
                except: pass

        # 3rd: check the validity of the given column names
        if column_check:
            for column in self.sbtab.columns:
                if not column.replace('!', '') in self.allowed_columns[self.sbtab.table_type] and not ('Identifiers:') in column:
                    self.warnings.append('The SBtab file has an unknown column: ' + \
                        column + '.\n \t Please use only supported column types!')
            if not self.sbtab.columns_dict['!' + self.sbtab.table_type] == 0:
                self.warnings.append('The SBtab primary column is at a wrong position.')
        else:
            self.warnings.append('The SBtab TableType is "unknown", therefore the main columns cannot be checked!')

        # 4th: check the length of the different rows
        for row in self.sbtab.value_rows:
            # check the content of the main column (first one) for empty entries
            if row[self.sbtab.columns_dict['!' + self.sbtab.table_type]] == '':
                self.warnings.append('The SBtab includes a row with an undefined identifier in the row: \n' + str(row))
            # check the rows for entries starting with + or -
            if str(row[0]).startswith('+') or str(row[0]).startswith('-'):
                self.warnings.append('An identifier for a data row must not begin with "+" or "-": \n' + str(row))
                # check the rows for entries containing . or :     OMITTED; should be solved, if the user puts the entryfield in quotes "
                #if ',' in list(row[self.sbtab.columns_dict[column]]):
                #    self.warnings.append('A data row must not include commas, but this one does: \n' + \
                #        str(row[self.sbtab.columns_dict[column]]))
                # raise SBtabError('An identifier for a data row must not
                # include ":" or ".": \n'+str(row))

        # 5th: are there duplicate columns?
        for column in collections.Counter(self.sbtab.columns).items():
            if column[1] > 1:
                self.warnings.append('There was a duplicate column in this SBtab file. Please remove it: ' + str(column[0]))
        



    def returnOutput(self):
        '''
        returns stuff
        '''
        return self.warnings


class ValidateFile:
    """
    Validate file and check for valid format.

    Notes
    -----
    To open a file: sbtab_file = open("filepath", "rb")
    """
    def __init__(self, sbtab_file, filename):
        # initialize warning string
        self.warnings = []

        self.file = sbtab_file
        self.filename = filename

        #valid = self.validateExtension(self.filename)
        #if not valid: raise SBtabError('The Parser cannot work with this file! Dude!')
        
        self.validateFile(self.file)

    def validateExtension(self):
        """
        Check the extension of the file for invalid formats.
        """
        valid_extensions = ['tsv','csv','xls','ods']
        if not self.filename[-3:] in valid_extensions: return False
        else: return True

    def validateFile(self, sbtab_file):
        """
        Validate file format and check for possible problems.
        """
        rows = []
        for line in sbtab_file:
            rows.append(line)

        length = len(rows[0])
        for i, row in enumerate(rows):
            if not row:
                self.warnings.append('The file contains an empty row in line: ' + str(i))
            if not len(row) == length:
                self.warnings.append('The lengths of the rows are not identical.\n This will be adjusted automatically.')
            length = len(row)

    def checkSeperator(self, sfile=None):
        '''
        find the seperator of the file; this is fucked up, but crucial
        '''
        sep = False

        for row in self.file.split('\n'):
            if row.startswith('!!'): continue
            if row.startswith('!'):
                s = re.search('(.)(!)',row[1:])
                #if there is only one column, we have to define a default separator.
                #let's use a tab.
                try: sep = s.group(1)
                except: sep = '\t'

        return sep

    def returnOutput(self):
        '''
        returns stuff
        '''
        return self.warnings

