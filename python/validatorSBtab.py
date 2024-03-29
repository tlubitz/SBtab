#!/usr/bin/env python
"""
SBtab Validator
===============

Validator for SBtab files.

See specification for further information.
"""
try:
    from . import SBtab
    from . import misc
except:
    import SBtab
    import misc
import re
import collections
import sys
import os


class SBtabError(Exception):
    '''
    Base class for errors in the SBtab validation class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ValidateTable:
    '''
    Validates SBtabTable object.
    '''
    def __init__(self, sbtab, def_table=None):
        '''
        Initialises validator and starts check for file and table format.

        Parameters
        ----------
        sbtab: SBtab.SBtabTable
            SBtab data file as SBtab table object.
        def_table: SBtab.SBtabTable
            SBtab definition table as SBtab table object.
        '''
        # initialize warning string
        self.warnings = []
        # define self variables
        self.sbtab = sbtab
        try: self.filename = sbtab.filename
        except: raise SBtabError('The SBtab object cannot be validated. Please set the filename first and try again.')

        # read definition table
        self.read_definition(def_table)

        # create set of valid table types
        self.allowed_table_types = list(set([row[2] for row in self.definitions[2:][0]]))
        
        # create dict of valid column names per table type
        self.allowed_columns = {}
        for table_type in self.allowed_table_types:
            self.allowed_columns[table_type] = [row[0] for row in self.definitions[2:][0] if row[2] == table_type]

        # check file format and header row
        try: self.check_general_format()
        except: raise SBtabError('The SBtab object cannot be validated. Please add content to it first and try again.')
        self.column2format = {}
        defs = self.definitions[2]

        for row in defs:
            if row[2] == self.sbtab.table_type:
                self.column2format[row[0]] = row[3]

        # remove empty column headers
        columns = []
        for element in self.sbtab.columns:
            if element == '': pass
            else: columns.append(element)
        self.sbtab.columns = columns

        # check SBtab object for validity
        self.check_table_content()

    def read_definition(self, def_table):
        '''
        read the required definition file; either it is provided by the user
        or the default definition file is read in; otherwise program exit
        '''
        # read in provided definition table or open default
        if def_table:
            try:
                self.sbtab_def = def_table
                self.definitions = self.sbtab_def.create_list()
            except:
                print('Provided definition file could not be read, so the validation'\
                      'could not be started.')
                sys.exit() 
        else:
            try:
                self.sbtab_def = misc.open_definitions_file()
                self.definitions = self.sbtab_def.create_list()
            except:
                print('''Definition file could not be loaded, so the validation
                could not be started. Please provide definition file
                as argument''')
                sys.exit()
            
    def check_general_format(self):
        '''
        Validates format of SBtab file, checks file format and header row.
        '''
        header = self.sbtab.header_row

        # Construct consistent quotes to make the header readable
        quotes = ['"', '\xe2\x80\x9d', '\xe2\x80\x98', '\xe2\x80\x99',
                  '\xe2\x80\x9b', '\xe2\x80\x9c', '\xe2\x80\x9f',
                  '\xe2\x80\xb2', '\xe2\x80\xb3', '\xe2\x80\xb4',
                  '\xe2\x80\xb5', '\xe2\x80\xb6', '\xe2\x80\xb7']

        for quote in quotes:
            try:
                header = header.replace(quote, "'")
            except: pass

        # check for valid header row
        if not header.startswith('!!'):
            self.warnings.append('''Error: The header row of the table does not
                                 start with "!!SBtab". This file cannot be v
                                 alidated.''')
        if not re.search("TableType='([^']*)'", header):
            self.warnings.append('''Error: The attribute TableType is not defin
                                 ed in the SBtab table; This file cannot be
                                 validated.''')
        if not re.search("TableName='([^']*)'", header):
            self.warnings.append('''Warning: The (optional) attribute TableName
                                 is not defined in the SBtab table.''')

        # check columns for preceding exclamation mark
        for column in self.sbtab.columns:
            if not column.startswith('!') and column != '':
                self.warnings.append('''Warning: Column %s does not start with
                an exclamation mark. It will not be processed.''' % (column))

        # check if there are value rows
        if len(self.sbtab.value_rows) < 1:
            self.warnings.append('''Warning: Column %s does not start with
            an exclamation mark. It will not be processed.''' % (column))

        # check if length of value rows correspond to amount of columns
        for vr in self.sbtab.value_rows:
            if len(vr) != len(self.sbtab.columns):
                self.warnings.append('Warning: The length of row %s does not'\
                                     'correspond to the amount of columns,'\
                                     'which is %s.''' % (vr, len(self.sbtab.columns)))


    def check_table_content(self):
        '''
        Validates the mandatory format of the SBtab in accordance to the
        TableType attribute.
        '''
        # 1st: check validity of table_type and save table type for later tests
        if self.sbtab.table_type not in self.allowed_table_types:
            self.warnings.append('Warning: The SBtab file has an invalid Tabl'\
                                 'eType in its header: %s. Thus, the validity'\
                                 ' of its columns cannot'\
                                 ' be checked' % (self.sbtab.table_type))
            return

        # 2nd: very important: check if the identifiers start with a digit;
        # this is not allowed in SBML!
        # also check if the identifiers are unique throughout the table
        unique = []
        for row in self.sbtab.value_rows:
            try: identifier = row[self.sbtab.columns_dict['!ID']]
            except: break
            
            if identifier not in unique: unique.append(identifier)
            else:
                warning = 'Warning: There is an identifier that is not unique'\
                          '. Please change that: %s' % identifier
                self.warnings.append(warning)

            try:
                int(identifier[0])
                self.warnings.append('Warning: There is an identifier that st'\
                                     'arts with a digit; this is not permitte'\
                                     'd for the SBML conversion:'\
                                     '%s' % (identifier))
            except: pass

        # if the SBtab is TableType="Reaction", check if there is at least a
        # SumFormula or an identifier column to characterise the reaction
        if self.sbtab.table_type == 'Reaction':
            if '!ReactionFormula' not in self.sbtab.columns_dict:
                ident = False
                for it in self.sbtab.columns_dict:
                    if it.startswith('!Identifier'):
                        ident = True
                        break
                if not ident:
                    warning = 'Error: A Reaction SBtab needs at least a colum'\
                              'n !ReactionFormula or an !Identifier column to'\
                              'be characterised.'
                    self.warnings.append(warning)

        if self.sbtab.table_type == 'Quantity':
            if '!Unit' not in self.sbtab.columns_dict:
                warning = 'Error: A Quantity SBtab requires the column'\
                          ' "'"Unit"'". Please add this column to the'\
                          ' SBtab file.'
                self.warnings.append(warning)

        # 3rd: check the validity of the given column names
        for column in self.sbtab.columns:
            if column.replace('!', '') not in self.allowed_columns[self.sbtab.table_type] \
               and ('Identifiers:') not in column \
               and ('ID:urn.') not in column:
                self.warnings.append('Warning: The SBtab file has an unknown '\
                                     'column: %s.\nPlease use only supported '\
                                     'column types!' % (column))

        # 4th: check the length of the different rows
        for row in self.sbtab.value_rows:
            # check the rows for entries starting with + or -
            if '!ID' in self.sbtab.columns_dict:
                if str(row[self.sbtab.columns_dict['!ID']]).startswith('+') \
                   or str(row[self.sbtab.columns_dict['!ID']]).startswith('-'):
                    self.warnings.append('Warning: An identifier for a data r'\
                                         'ow must not begin with "+" or "-": '\
                                         '\n%s''' % (row))
            if '!ReactionFormula' in self.sbtab.columns_dict:
                if '<=>' not in row[self.sbtab.columns_dict['!ReactionFormula']]:
                    warning = 'There is a sum formula that does not adhere to'\
                              ' the sum formula syntax from the SBtab specifi'\
                              'cation: %s' % (str(row[self.sbtab.columns_dict['!ReactionFormula']]))
                    self.warnings.append(warning)

            for i, entry in enumerate(row):
                if entry == '': continue
                if self.sbtab.columns[i][1:].startswith('Identifier'):
                    req_format = 'string'
                else:
                    try:
                        req_format = self.column2format[self.sbtab.columns[i][1:]]
                    except: continue
                if req_format == 'Boolean':
                    if entry != 'True' and entry != 'False' and entry != 'TRUE' \
                       and entry != 'FALSE' and entry != '0' and entry != '1':
                        warning = 'Warning: The column %s holds a value that '\
                                  'does not conform with the assigned column '\
                                  'format %s: %s' % (self.sbtab.columns[i][1:],
                                                     req_format, entry)
                        self.warnings.append(warning)
                elif req_format == 'float':
                    try: float(entry)
                    except:
                        warning = 'Warning: The column %s holds a value that '\
                                  'does not conform with the assigned column '\
                                  'format %s: %s' % (self.sbtab.columns[i][1:],
                                                     req_format, entry)
                        self.warnings.append(warning)
                elif req_format == '{+,-,0}':
                    if entry != '+' and entry != '-' and entry != '0':
                        warning = 'Warning: The column %s holds a value that '\
                                  'does not conform with the assigned column '\
                                  'format %s: %s' % (self.sbtab.columns[i][1:],
                                                     req_format, entry)
                        self.warnings.append(warning)

        # 5th: are there duplicate columns?
        for column in collections.Counter(self.sbtab.columns).items():
            if column[1] > 1:
                self.warnings.append('''Warning: There was a duplicate column i
                                     n this SBtab file. Please remove it:
                                     %s''' % (str(column[0])))

                
    def return_output(self):
        '''
        Returns the warnings from the validation process.

        Returns: list
            List of warnings of the validator in string representation.
        '''
        return self.warnings


class ValidateDocument:
    '''
    Validates SBtabDocument object
    '''
    def __init__(self, sbtab_doc, def_table=None):
        '''
        Initialises validator and starts check for file and table format.


        Parameters
        ----------
        sbtab_doc: SBtab.SBtabDocument
            SBtab data file as SBtab table object.
        def_table: SBtab.SBtabTable
            SBtab definition table as SBtab table object.
        '''
        self.sbtab_doc = sbtab_doc
        if len(self.sbtab_doc.sbtabs) == 0:
            raise SBtabError('This SBtab Document cannot be validated. It is empty.')
        self.sbtab_def = def_table
        # self.validate_document()

    def validate_document(self):
        '''
        Validates SBtabDocument.

        Returns: list
            List of lists with warnings for each of the SBtab tables comprised in the SBtab document.
        '''
        warnings = []
        for sbtab in self.sbtab_doc.sbtabs:
            warnings_s = ['Warnings for %s:\n' % sbtab.filename]
            self.vt = ValidateTable(sbtab, self.sbtab_def)
            try:
                warnings_s.append(self.vt.return_output())
            except:
                raise SBtabError('SBtab %s cannot be validated.' % (sbtab.filename))
            warnings.append(warnings_s)
            
        return warnings


