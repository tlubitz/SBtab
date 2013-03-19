#!/usr/bin/env python
import re

allowed_types = ['Reaction', 'Compound', 'Enzyme', 'Compartment', 'QuantityType', 'Regulator', 'Gene']
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

        # identification of seperator (tsv/csv) (self.separator)
        if str(filename).endswith('.tsv'):
            self.separator = '\t'
        elif str(filename).endswith('.csv'):
            self.separator = ';'
        else:
            raise SBtabError('The given file format is not supported: ' +
                             filename + '. Please use ".tsv" or ".csv" instead')

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
        initializes the column indices
        '''
        if self.table_type in allowed_types:
            typeFunction = 'self.initializeColumns' + self.table_type + '()'
            eval(typeFunction)
        else:
            self.definitionTable()
            # raise SBtabError('\''+ self.table_type+'\' is not a valid SBtab
            # TableType.')

    def changeValue(self, row, column, new):
        '''
        change single value in the SBtab
        '''
        pass

    def createSBtab(self):
        '''
        write the python object into a SBtab file, tsv format
        '''

    def initializeColumnsReaction(self):
        '''
        initialize specific columns for the SBtab type Reaction
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Reaction':
                self.ini_columns['!Reaction'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!SBMLReactionID':
                self.ini_columns['!SBMLReactionID'] = i
            elif column == '!SumFormula':
                self.ini_columns['!SumFomula'] = i
            elif column == '!Location':
                self.ini_columns['!Location'] = i
            elif column == '!Enzyme':
                self.ini_columns['!Enzyme'] = i
            elif column == '!KineticLaw':
                self.ini_columns['!KineticLaw'] = i
            elif column == '!Enzyme SBMLSpeciesID':
                self.ini_columns['!Enzyme SMBLSpeciesID'] = i
            elif column == '!Enzyme SBMLParameterID':
                self.ini_columns['!Enzyme SBMLParameterID'] = i
            elif column == '!MetabolicRegulators':
                self.ini_columns['!MetabolicRegulators'] = i
            elif column == '!BuildReaction':
                self.ini_columns['!BuildReaction'] = i
            elif column == '!BuildEnzyme':
                self.ini_columns['!BuildEnzymes'] = i
            elif column == '!Model':
                self.ini_columns['Model'] = i
            elif column == '!Pathway':
                self.ini_columns['!Pathway'] = i
            elif column == '!SubreactionOf':
                self.ini_columns['SubreactionOf'] = i
            elif column == '!IsComplete':
                self.ini_columns['!IsComplete'] = i
            elif column == '!IsReversible':
                self.ini_columns['!IsReversible'] = i
            elif column == '!IsInEquilibrium':
                self.ini_columns['!IsInEquilibrium'] = i
            elif column == '!IsExchangeReaction':
                self.ini_columns['!IsExchangeReaction'] = i
            elif column == '!Flux':
                self.ini_columns['!Flux'] = i
            elif column == '!IsNonEnzymatic':
                self.ini_columns['!IsNonEnzymatic'] = i
            elif column == '!Metabolic':
                self.ini_columns['!Metabolic'] = i
            elif column == '!Gene':
                self.ini_columns['!Gene'] = i
            elif column == '!Operon':
                self.ini_columns['!Operon'] = i
            elif column == '!Transcription':
                self.ini_columns['!Transcription'] = i
            elif column == '!Translation':
                self.ini_columns['!Translation'] = i
            elif column == '!BuildEnzymeProduction':
                self.ini_columns['!BuildEnzymeProduction'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsCompound(self):
        '''
        initialize specific columns for the SBtab type Compound
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Compound':
                self.ini_columns['!Compound'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!SBMLSpeciesID':
                self.ini_columns['!SBMLSpeciesID'] = i
            elif column == '!SBMLSpeciestypeID':
                self.ini_columns['!SBMLSpeciestypeID'] = i
            elif column == '!Location':
                self.ini_columns['!Location'] = i
            elif column == '!Charge':
                self.ini_columns['!Charge'] = i
            elif column == '!Constant':
                self.ini_columns['!Constant'] = i
            elif column == '!State':
                self.ini_columns['!State'] = i
            elif column == '!CompoundSumFormula':
                self.ini_columns['!CompundSumFormula'] = i
            elif column == '!StructureFormula':
                self.ini_columns['!StructureFormula'] = i
            elif column == '!Mass':
                self.ini_columns['!Mass'] = i
            elif column == '!Component':
                self.ini_columns['!Component'] = i
            elif column == '!IsConstant':
                self.ini_columns['!IsConstant'] = i
            elif column == '!EnzymeRole':
                self.ini_columns['!EnzymeRole'] = i
            elif column == '!RegulatorRole':
                self.ini_columns['!RegulatorRole'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsEnzyme(self):
        '''
        initialize specific columns for the SBtab type Enzyme
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Enzyme':
                self.ini_columns['!Enzyme'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!CatalysedReaction':
                self.ini_columns['!CatalysedReaction'] = i
            elif column == '!KineticLaw':
                self.ini_columns['!KineticLaw'] = i
            elif column == '!MetabolicRegulators':
                self.ini_columns['!MetabolicRegulators'] = i
            elif column == '!Gene':
                self.ini_columns['!Gene'] = i
            elif column == '!GeneBooleanFormula':
                self.ini_columns['!GeneBooleanFomula'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsCompartment(self):
        '''
        initialize specific columns for the SBtab type Compartment
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Compartment':
                self.ini_columns['!Compartment'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!SBMLCompartmentID':
                self.ini_columns['!SBMLCompartmentID'] = i
            elif column == '!Size':
                self.ini_columns['!Size'] = i
            elif column == '!OuterCompartment':
                self.ini_columns['!OuterCompartment'] = i
            elif column == '!OuterCompartment SBMLCompartmentID':
                self.ini_columns['!OuterCompartment SBMLCompartmentID'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsQuantityType(self):
        '''
        initialize specific columns for the SBtab type QuantityType
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!QuantityType':
                self.ini_columns['!QuantityType'] = i
            elif column == '!Quantity':
                self.ini_columns['!Quantity'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!SBMLReactionID':
                self.ini_columns['!SBMLReactionID'] = i
            elif column == '!SBMLSpeciesID':
                self.ini_columns['!SBMLSpeciesID'] = i
            elif column == '!Median':
                self.ini_columns['!Median'] = i
            elif column == '!Mean':
                self.ini_columns['!Mean'] = i
            elif column == '!Value':
                self.ini_columns['!Value'] = i
            elif column == '!Std':
                self.ini_columns['!Std'] = i
            elif column == '!Unit':
                self.ini_columns['!Unit'] = i
            elif column == '!Provenance':
                self.ini_columns['!Provenance'] = i
            elif column == '!Type':
                self.ini_columns['!Type'] = i
            elif column == '!Source':
                self.ini_columns['!Source'] = i
            elif column == '!logMean':
                self.ini_columns['!logMean'] = i
            elif column == '!logStd':
                self.ini_columns['!logStd'] = i
            elif column == '!Minimum':
                self.ini_columns['!Minimum'] = i
            elif column == '!Maximum':
                self.ini_columns['!Maximum'] = i
            elif column == '!pH':
                self.ini_columns['!pH'] = i
            elif column == '!Temperature':
                self.ini_columns['!Temperature'] = i
            elif column == '!OrganismName':
                self.ini_columns['!OrganismName'] = i
            elif column == '!Time':
                self.ini_columns['!Time'] = i
            elif column == '!SampleName':
                self.ini_columns['!SampleName'] = i
            elif column == '!Condition':
                self.ini_columns['!Condition'] = i
            elif column == '!Scale':
                self.ini_columns['!Scale'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsGene(self):
        '''
        initialize specific columns for the SBtab type Gene
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Gene':
                self.ini_columns['!Gene'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!GeneLocus':
                self.ini_columns['!GeneLocus'] = i
            elif column == '!GeneProduct':
                self.ini_columns['!GeneProduct'] = i
            elif column == '!GeneProduct SBMLSpeciesID':
                self.ini_columns['!GeneProduct SBMLSpeciesID'] = i
            elif column == '!Operon':
                self.ini_columns['!Operon'] = i
            elif column == '!Transcription':
                self.ini_columns['!Transcription'] = i
            elif column == '!Tranlation':
                self.ini_columns['!Translation'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsRegulator(self):
        '''
        initialize specific columns for the SBtab type Regulator
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column == '!Regulator':
                self.ini_columns['!Regulator'] = i
            elif column == '!Name':
                self.ini_columns['!Name'] = i
            elif column == '!State':
                self.ini_columns['!State'] = i
            elif column == '!Activity':
                self.ini_columns['!Activity'] = i
            elif column == '!Binding':
                self.ini_columns['!Binding'] = i
            elif column == '!TargetGene':
                self.ini_columns['!TargetGene'] = i
            elif column == '!TargetOperon':
                self.ini_columns['!TargetOperon'] = i
            elif column == '!TargetPromoter':
                self.ini_columns['!TargetPromoter'] = i
            elif column.startswith('!MiriamID'):
                self.ini_columns['!MiriamID'] = i
            elif column.rstrip():
                self.ini_columns['unknown: ' + column.rstrip()] = i

    def initializeColumnsNewTable(self):
        '''
        initialize specific columns for unknown SBtab types
        '''
        self.ini_columns = {}

        for i, column in enumerate(self.column_names):
            if column.rstrip():
                self.ini_columns[column.rstrip()] = i

    def checkColumns(self):
        '''
        checks whether the given column names are known (according to the specification)
        '''
        specific_columns = self.table_type + '_columns.keys()'
        for column in self.column_names:
            if column in eval(specific_columns):
                pass
            else:
                print 'The column ', column, ' is unknown according to the SBtab specification.'

    def definitionTable(self):
        self.initializeColumnsNewTable()
