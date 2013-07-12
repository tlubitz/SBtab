#!/usr/bin/env python
import SBtab
import re

'''
allowed_types = ['Reaction', 'Compound', 'Enzyme', 'Compartment', 'QuantityType', 'Regulator', 'Gene', 'Quantity']
reaction_columns = [
    '!Reaction', '!Name', '!SBMLReactionID', '!SumFormula', '!Location', '!Enzyme', '!KineticLaw', '!Enzyme SBMLSpeciesID', '!Enzyme SBMLParameterID', '!MetabolicRegulators', '!BuildReaction', '!BuildEnzyme', 'Model', '!Pathway', '!SubreactionOf', '!IsComplete', '!IsReversible', '!IsInEquilibrium',
    '!IsExchangeReaction', 'Flux', '!IsNonEnzymatic', '!Metabolic', '!Gene', '!Operon', '!Transcription', '!Translation', '!BuildEnzymeProduction']
#'!Description','!Comment','!ReferenceName','!ReferencePubMed','!ReferenceDOI','!SBOTerm','!GeneName' not in SBtab class
compound_columns = [
    'Compound', '!Name', '!SBMLSpeciesID', 'SBMLSpeciestypeID', '!Location', '!Charge', '!Constant', '!State',
    '!CompoundSumFormula', '!StructureFormula', '!Mass', '!Component', '!IsConstant', '!EnzymeRole', '!RegulatorRole']
#'!Description','!Comment','!ReferenceName','!ReferencePubMed','!ReferenceDOI','!SpeciesType',,'!SBOTerm','!InitialConcentration' not in SBtab class
enzyme_columns = ['!Enzyme', '!Name', '!CatalysedReaction', '!KineticLaw', '!MetabolicRegulators', '!Gene', '!GeneBooleanFormula']
#'!Description','!Comment','!ReferenceName','!ReferencePubMed','!ReferenceDOI','!SBOTerm' not in SBtab class
compartment_columns = ['!Compartment', '!Name', 'SBMLCompartmentID', '!Size', '!OuterCompartment', '!OuterCompartment SBMLCompartmentID']
#'!Description','!Comment','!ReferenceName','!ReferencePubMed','!ReferenceDOI','!SBML::compartment::id','!SBOTerm' not in SBtab class
quantitytype_columns = [
    '!QuantityType', '!Quantity', '!Name', '!SBMLReactionID', '!SBMLSpeciesID', '!Median', '!Mean', '!Value', '!Std', '!Unit', '!Provenance', '!Type', '!Source', '!logMean', '!logStd', '!Minimum', '!Maximum',
    '!pH', '!Temperature', '!OrganismName', '!Time', '!SampleName', '!Condition', '!Scale']
gene_columns = ['!Gene', '!Name', '!GeneLocus', '!GeneProduct',
                '!GeneProduct SBMLSpeciesID', '!Operon', '!Transcription', '!Translation']
regulator_columns = ['!Regulator', '!Name', '!State', '!Activity',
                     '!Binding', '!TargetGene', '!TargetOperon', '!TargetPromoter']

type2columns = {'Reaction': reaction_columns,
                'Compound': compound_columns,
                'Enzyme': enzyme_columns,
                'Compartment': compartment_columns,
                'QuantityType': quantitytype_columns,
                'Gene': gene_columns,
                'Regulator': regulator_columns}

allowed_urns = {'SBO': 'urn:miriam:obo.sbo',
                'CheBI': 'urn:miriam:obo.chebi',
                'Enzyme nomenclature': 'ec-code',
                'KEGG Compound': 'urn:miriam:kegg.compound',
                'KEGG Reaction': 'urn:miriam:kegg.reaction',
                'UniProt': 'uniprot',
                'Gene Ontology': 'urn:miriam:obo.go',
                'Taxonomy': 'taxonomy',
                'SGD': 'sgd'}
'''


class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Validator:
    '''
    validator v11 (02/13)
    This class checks all types of SBtabFiles for validity criteria
    '''
    def __init__(self, SBtab_table, SBtab_name):
        self.warnings = ''
        self.table = SBtab_table
        self.filename = SBtab_name
        self.validateFile()

        try:
            self.sbtab = SBtab.SBtabTable(
                self.rows_file, self.filename)  # libSBtab. ??
            self.validate()
        except:
            self.warnings += 'The Parser can not work with this file!'
            pass

        if len(self.warnings) > 0:
            print self.warnings
                    # raise SBtabError(self.warnings)? why?
        else:
            print 'No warnings detected!'

    def validateFile(self):
        '''
        validates format of SBtab file, mandatory stuff
        '''
        # saves table rows in variable
        self.rows_file = []
        for i, row in enumerate(self.table):
            self.rows_file.append(row.strip('\n'))

        # remove empty rows in list
        while '' in self.rows_file:
            self.rows_file.remove('')

        # checks file format and saves separator
        if str(self.filename).endswith('.tsv'):
            self.separator = '\t'
        elif str(self.filename).endswith('.csv'):
            self.separator = ';'
        else:
            self.warnings += 'The given file format is not supported: ' + \
                self.filename + '. Please use ".tsv" or ".csv" instead.\n'

        # checks for valid header rows
        if not self.rows_file[0].startswith('!!'):
            self.warnings += 'The header row of the table does not start with "!!SBtab": ' + \
                self.rows_file[0] + '\n'
        if not re.search('TableType="([^"])*"', self.rows_file[0]):
            self.warnings += 'The table type of the SBtab is not defined. Line: ' + \
                self.rows_file[0] + '\n'
        if not re.search('Table="([^"])*"', self.rows_file[0]):
            self.warnings += 'The name of the SBtab table is not defined. Line: ' + \
                self.rows_file[0] + '\n'

        # checks for possible table content and main columns
        # checks length of table
        if len(self.rows_file) < 3:
            self.warnings += 'The table contains no information: ' + \
                self.rows_file[0] + '\n'
        else:
            self.main_column_count = None
            # checks for existing main column
            if not self.rows_file[1].startswith('!'):
                self.warnings += 'The entity row of the table does not start with "!": ' + \
                    self.rows_file[1] + '\n'
            # counts number of defined columns
            self.main_column_count = len(
                self.rows_file[1].split(self.separator))
            # compares length of columns with defined columns
            for row in self.rows_file[2:]:
                if not len(row.rstrip(self.separator).split(self.separator)) == self.main_column_count:
                    self.warnings += 'The number of entries does not fit the number of defined columns: ' + \
                        row + '\n'

    def validate(self):
        '''
        #validates at first general stuff, then the specific stuff
        '''
        # general stuff
        # 1st: check validity of table_type
        if not self.sbtab.table_type in allowed_types:
            self.warnings += 'The SBtab file has an invalid TableType in its header: ' + \
                self.sbtab.table_type + '.\n'
            # raise SBtabError('The SBtab file has an invalid (or no) TableType
            # in its header: '+self.sbtab.table_type)

        # 2nd: check the important first column
        first_column = '!' + self.sbtab.table_type
        if not ((self.rows_file[1]).split(self.separator))[0] == first_column:
            self.warnings += 'The first column of the file does not correspond with the given TableType ' + \
                self.sbtab.table_type + 'and will be filled automatically.\n'

        # 3rd: check the validity of the given column names
        try:
            columns = type2columns[self.sbtab.table_type]
            for column in self.sbtab.column_names:
                if not column in columns and not column.startswith('!MiriamID'):
                    self.warnings += 'The SBtab file has an unknown column: ' + \
                        column + '.\n'

            if not self.sbtab.ini_columns['!' + self.sbtab.table_type] == 0:
                self.warnings += 'The SBtab primary column is on a wrong position.\n'
        except:
            self.warnings += 'The SBtab TableType is "unknown", therefor the main columns can not be checked! \n'

        # 4th: check the length of the different rows
        for row in self.sbtab.value_rows:
            if not len(row) == len(self.sbtab.column_names):
                self.warnings += 'The SBtab includes a row that has not the right length according to the column header row: \n' + \
                    str(row) + '.\n'
                # check the content of the main column (first one)
            if row[self.sbtab.ini_columns['!' + self.sbtab.table_type]] == '':
                self.warnings += 'The SBtab includes a row with an undefined identifier in the main row: \n' + \
                    str(row) + '.\n'
                # raise SBtabError('The SBtab includes a row with an undefined
                # identifier in the main row: \n'+str(row))
            elif row[self.sbtab.ini_columns['!' + self.sbtab.table_type]].startswith('+') or row[self.sbtab.ini_columns['!' + self.sbtab.table_type]].startswith('-'):
                self.warnings += 'An identifier for a data row must not begin with "+" or "-": \n' + \
                    str(row) + '.\n'
                # raise SBtabError('An identifier for a data row must not begin
                # with "+" or "-": \n'+str(row))
            if ':' in row[self.sbtab.ini_columns['!' + self.sbtab.table_type]] or '.' in row[self.sbtab.ini_columns['!' + self.sbtab.table_type]]:
                self.warnings += 'An identifier for a data row must not include ":" or ".": \n' + \
                    str(row) + '.\n'
                # raise SBtabError('An identifier for a data row must not
                # include ":" or ".": \n'+str(row))
    '''
            #checks primary keys for unambiguity
        if self.sbtab.table_type == 'QuantityType':
                primary = [row[self.sbtab.ini_columns['!'+self.sbtab.table_type]]]
                primary.append(row[self.sbtab.ini_columns['!SBMLReactionID']])
                primary.append(row[self.sbtab.ini_columns['!SBMLSpeciesID']])
            if not primary in primaries: primaries.append(primary)
            else: self.warnings += 'Duplicate use of the identifier '+primary+'.\n'
                    #raise SBtabError('Duplicate use of the identifier '+primary)
            else: if not row[self.sbtab.ini_columns['!'+self.sbtab.table_type]] in primaries:
                primaries.append(row[self.sbtab.ini_columns['!'+self.sbtab.table_type]])
                else:
                    self.warnings += 'Duplicate use of the identifier '+row[self.sbtab.ini_columns['!'+self.sbtab.table_type]]+'.\n'
                    #raise SBtabError('Duplicate use of the identifier '+row[self.sbtab.main_column])

        #5th: check validity of used URNs in possible Miriam column
        if self.sbtab.miriam_column:
            urn = re.search('!MiriamID::([^"]*)',self.sbtab.column_names[self.sbtab.miriam_column]).group(1)
            if not urn in allowed_urns.values():
                self.warnings += 'Use of unknown URN in the column names: "'+self.sbtab.column_names[self.sbtab.miriam_column]+'".\n'
                #raise SBtabError('Use of unknown URN in the column names: "'+self.sbtab.column_names[self.sbtab.miriam_column]+'".')
            #self.checkMiriamSyntax(urn,row[self.sbtab.miriam_column])

        #specific stuff
        if self.sbtab.table_type == 'QuantityData': function_name = 'self.validateQuantityData()'
        else: function_name = 'self.validate'+self.sbtab.table_type+'()'

        eval(function_name)

    def checkMiriamSyntax(self,urn,identifier):
        '''
    # checks the syntax validity of the Miriam identifier corresponding to its
    # urn
    '''
        if not identifier == '':
            pass

    def validateReaction(self):
        '''
    # validates the SBtab type Reaction
    '''
        if self.sbtab.sumformula_column:
            for row in self.sbtab.value_rows:
                if not '<=>' in row[self.sbtab.sumformula_column]:
                    print 'The sumformula of reaction ',row[self.sbtab.main_column],' is not formatted correctly. It needs to contain "<=>" to separate the reactants from the products.'
        if self.sbtab.sumformula_column == None and self.sbtab.miriam_column == None:
            self.warnings += 'Mandatory column missing! You need either a "!SumFormula" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".\n'
            #raise SBtabError('Mandatory column missing! You need either a "!SumFormula" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".')

    def validateCompound(self):
        '''
    # validates the SBtab type Compound
    '''
        if self.sbtab.name_column == None and self.sbtab.miriam_column == None:
            self.warnings += 'Mandatory column missing! You need either a "!Name" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".\n'
            #raise SBtabError('Mandatory column missing! You need either a "!Name" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".')

    def validateEnzyme(self):
        '''
    # validates the SBtab type Enzyme
    '''
        if self.sbtab.name_column == None and self.sbtab.miriam_column == None:
            self.warnings += 'Mandatory column missing! You need either a "!Name" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".\n'
            #raise SBtabError('Mandatory column missing! You need either a "!Name" or a "!MiriamID..." column for TableType "'+self.sbtab.table_type+'".')

    def validateCompartment(self):
        '''
    # validates the SBtab type Compartment
    '''
        pass

    def validateQuantityData(self):
        '''
    # validates the SBtab type QuantityData
    '''
        allowed_quantities = {'standard chemical potential':'C','Michaelis constant':'RC','inhibitory constant':'RC','activation constant':'RC','concentration':'C','concentration of enzyme':'R','equilibrium constant':'R','product catalytic rate constant':'R','substrate catalytic rate constant':'R','forward maximal velocity':'R','reverse maximal velocity':'R','chemical potential':'C','reaction affinity':'R'}

        for row in self.sbtab.value_rows:
            #is the quantitytype known?
            if row[self.sbtab.main_column] not in allowed_quantities.keys():
                self.warnings += 'There is an unknown QuantityType in the SBtab: '+row[self.sbtab.main_column]+'.\n'
                #raise SBtabError('There is an unknown QuantityType in the SBtab: '+row[self.sbtab.main_column])
            #does the row hold a mean value?
            if row[self.sbtab.m_column] == '' or row[self.sbtab.m_column] == '-' or row[self.sbtab.m_column] == 'nan':
                self.warnings += 'One of the QuantityTypes does not have a valid mean value: '+row[self.sbtab.main_column]+', '+row[self.sbtab.r_column]+', '+row[self.sbtab.c_column]+', '+row[self.sbtab.m_column]+'.\n'
                #raise SBtabError('One of the QuantityTypes does not have a valid mean value: '+row[self.sbtab.main_column]+', '+row[self.sbtab.r_column]+', '+row[self.sbtab.c_column]+', '+row[self.sbtab.m_column]+'.')
            #are the required compounds and/or reactions given for the quantitytypes?
            if row[self.sbtab.main_column] in allowed_quantities.keys():
                if allowed_quantities[row[self.sbtab.main_column]] == 'C' and row[self.sbtab.c_column] == '':
                    self.warnings += 'A '+row[self.sbtab.main_column]+' does not have an assigned compound.\n'
                    #raise SBtabError('A '+row[self.sbtab.main_column]+' does not have an assigned compound.')
                elif allowed_quantities[row[self.sbtab.main_column]] == 'R' and row[self.sbtab.r_column] == '':
                    self.warnings += 'A '+row[self.sbtab.main_column]+' does not have an assigned reaction.\n'
                    #raise SBtabError('A '+row[self.sbtab.main_column]+' does not have an assigned reaction.')
                elif allowed_quantities[row[self.sbtab.main_column]] == 'RC' and (row[self.sbtab.c_column] == '' or row[self.sbtab.r_column] == ''):
                    self.warnings += 'A '+row[self.sbtab.main_column]+' does either not have an assigned compound or reaction.\n'
                    #raise SBtabError('A '+row[self.sbtab.main_column]+' does either not have an assigned compound or reaction.')


if __name__ == '__main__':

    sbtab_reaction = open('sbtabs/sbtab_reaction_full.tsv','r')
    sbtab_compound = open('sbtabs/sbtab_compound_full.tsv','r')
    sbtab_enzyme = open('sbtabs/sbtab_enzyme_full.tsv','r')
    sbtab_compartment = open('sbtabs/sbtab_compartment_full.tsv','r')

    validator = Validator(sbtab_reaction.read().split('\n'),'sbtabs/sbtab_reaction_full.tsv')
'''
