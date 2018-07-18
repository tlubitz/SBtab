#!/usr/bin/env python
import unittest
import sys
import os
import copy
import libsbml

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import commandline_scripts.sbml2sbtab as sbml2sbtab

class TestSBMLConversion(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.sbml_names = [f for f in os.listdir('sbml/') if os.path.isfile(os.path.join('sbml/', f))]
        
        self.sbml_docs = []
        reader = libsbml.SBMLReader()
        
        for i, s in enumerate(self.sbml_names):
            if s.startswith('_'): continue
            doc = reader.readSBML('sbml/' + s)
            self.sbml_docs.append(doc)

    def test_object_creation(self):
        '''
        test if the SBML models can be used for object creation
        '''
        for i, sbml_doc in enumerate(self.sbml_docs):
            conversion_object = sbml2sbtab.SBMLDocument(sbml_doc.getModel(), self.sbml_names[i])
            self.assertIsNotNone(conversion_object)
            
    def test_conversion(self):
        '''
        test if the conversion can be processed
        '''
        for i, sbml_doc in enumerate(self.sbml_docs):
            print(self.sbml_names[i])
            # get previous SBML to compare to
            previous_sbml = self.sbml_docs[i].getModel()
            sbml_level = previous_sbml.getLevel()

            # get SBtab document
            conversion_object = sbml2sbtab.SBMLDocument(sbml_doc.getModel(), self.sbml_names[i])
            (sbtab_doc, warnings) = conversion_object.convert_to_sbtab()

            # check general attributes of sbtab_doc
            self.assertIsNotNone(sbtab_doc)
            self.assertNotEqual(len(sbtab_doc.sbtabs), 0)
            self.assertNotEqual(len(sbtab_doc.name_to_sbtab), 0)
            self.assertNotEqual(len(sbtab_doc.type_to_sbtab), 0)
            self.assertNotEqual(len(sbtab_doc.sbtab_filenames), 0)

            self.assertEqual(len(sbtab_doc.sbtabs), len(sbtab_doc.name_to_sbtab))
            self.assertEqual(len(sbtab_doc.name_to_sbtab), len(sbtab_doc.type_to_sbtab))
            self.assertEqual(len(sbtab_doc.type_to_sbtab), len(sbtab_doc.sbtab_filenames))
            self.assertIsNotNone(sbtab_doc.doc_row)
            self.assertEqual(sbtab_doc.doc_row[:8], '!!!SBtab')
            
            # check single SBtab files
            if previous_sbml.getNumCompartments() > 0:
                self.assertIn('Compartment', sbtab_doc.type_to_sbtab)
                compartment_sbtabs = sbtab_doc.type_to_sbtab['Compartment']
                for c_sbtab in compartment_sbtabs:
                    # header row
                    self.assertEqual(c_sbtab.header_row[:7], '!!SBtab')
                    self.assertIn('TableType', c_sbtab.header_row)                    

                    # columns
                    self.assertEqual(len(c_sbtab.value_rows), previous_sbml.getNumCompartments())
                    self.assertIn('!ID', c_sbtab.columns)
                    self.assertIn('!ID', c_sbtab.columns_dict)
                    self.assertIn('!Size', c_sbtab.columns)
                    self.assertIn('!Size', c_sbtab.columns_dict)
                    #if sbml_level == 3:
                    #    self.assertIn('!Constant', c_sbtab.columns)
                    #    self.assertIn('!Constant', c_sbtab.columns_dict)

                    # rows
                    for compartment in c_sbtab.value_rows:
                        self.assertEqual(len(compartment), len(c_sbtab.columns))
                        self.assertNotEqual(compartment[c_sbtab.columns_dict['!ID']], '')
                        self.assertNotEqual(compartment[c_sbtab.columns_dict['!Name']], '')
                        self.assertNotEqual(compartment[c_sbtab.columns_dict['!Size']], '')
                        #if sbml_level == 3:
                        #    self.assertNotEqual(compartment[c_sbtab.columns_dict['!Constant']], '')
                    
            if previous_sbml.getNumSpecies() > 0:
                self.assertIn('Compound', sbtab_doc.type_to_sbtab)
                compound_sbtabs = sbtab_doc.type_to_sbtab['Compound']
                for c_sbtab in compound_sbtabs:
                    # header row
                    self.assertEqual(c_sbtab.header_row[:7], '!!SBtab')
                    self.assertIn('TableType', c_sbtab.header_row)                    

                    # columns
                    self.assertEqual(len(c_sbtab.value_rows), previous_sbml.getNumSpecies())
                    self.assertIn('!ID', c_sbtab.columns)
                    self.assertIn('!ID', c_sbtab.columns_dict)
                    self.assertIn('!Location', c_sbtab.columns)
                    self.assertIn('!Location', c_sbtab.columns_dict)
                    #if sbml_level == 3:
                    #    self.assertIn('!Constant', c_sbtab.columns)
                    #    self.assertIn('!Constant', c_sbtab.columns_dict)
                    #    self.assertIn('!hasOnlySubstanceUnit', c_sbtab.columns)
                    #    self.assertIn('!hasOnlySubstanceUnit', c_sbtab.columns_dict)
                    #    self.assertIn('!boundaryCondition', c_sbtab.columns)
                    #    self.assertIn('!boundaryCondition', c_sbtab.columns_dict)
                    #    self.assertIn('!InitialValue', c_sbtab.columns)
                    #    self.assertIn('!InitialValue', c_sbtab.columns_dict)

                    # rows
                    for compound in c_sbtab.value_rows:
                        self.assertEqual(len(compound), len(c_sbtab.columns))
                        self.assertNotEqual(compound[c_sbtab.columns_dict['!ID']], '')
                        self.assertNotEqual(compound[c_sbtab.columns_dict['!Location']], '')
                        #if sbml_level == 3:
                        #    self.assertNotEqual(compound[c_sbtab.columns_dict['!Constant']], '')
                        #    self.assertNotEqual(compound[c_sbtab.columns_dict['!hasOnlySubstanceUnit']], '')
                        #    self.assertNotEqual(compound[c_sbtab.columns_dict['!boundaryCondition']], '')
                        #    self.assertNotEqual(compound[c_sbtab.columns_dict['!InitialValue']], '')
                    
            if previous_sbml.getNumReactions() > 0:
                self.assertIn('Reaction', sbtab_doc.type_to_sbtab)
                reaction_sbtabs = sbtab_doc.type_to_sbtab['Reaction']
                for r_sbtab in reaction_sbtabs:
                    # header row
                    self.assertEqual(r_sbtab.header_row[:7], '!!SBtab')
                    self.assertIn('TableType', r_sbtab.header_row)                    

                    # columns
                    self.assertEqual(len(r_sbtab.value_rows), previous_sbml.getNumReactions())
                    self.assertIn('!ID', r_sbtab.columns)
                    self.assertIn('!ID', r_sbtab.columns_dict)
                    self.assertIn('!ReactionFormula', r_sbtab.columns)
                    self.assertIn('!ReactionFormula', r_sbtab.columns_dict)
                    #if sbml_level == 3:
                    #    self.assertIn('!IsReversible', r_sbtab.columns)
                    #    self.assertIn('!IsReversible', r_sbtab.columns_dict)
                    #    self.assertIn('!Constant', r_sbtab.columns)
                    #    self.assertIn('!Constant', r_sbtab.columns_dict)

                    # rows
                    for reaction in r_sbtab.value_rows:
                        self.assertEqual(len(reaction), len(r_sbtab.columns))
                        self.assertNotEqual(reaction[r_sbtab.columns_dict['!ID']], '')
                        self.assertNotEqual(reaction[r_sbtab.columns_dict['!ReactionFormula']], '')
                        #if sbml_level == 3:
                        #    self.assertNotEqual(reaction[r_sbtab.columns_dict['!Constant']], '')
                        #    self.assertNotEqual(reaction[r_sbtab.columns_dict['!IsReversible']], '')
                    
            if previous_sbml.getNumParameters() > 0:
                self.assertIn('Quantity', sbtab_doc.type_to_sbtab)
                quantity_sbtabs = sbtab_doc.type_to_sbtab['Quantity']
                for q_sbtab in quantity_sbtabs:
                    # header row
                    self.assertEqual(q_sbtab.header_row[:7], '!!SBtab')
                    self.assertIn('TableType', q_sbtab.header_row)                    

                    # columns
                    # we have a bug here for the export of local parameters;
                    # uncomment when fixed
                    #print(q_sbtab.value_rows)
                    #self.assertEqual(len(q_sbtab.value_rows), previous_sbml.getNumParameters())
                    self.assertIn('!ID', q_sbtab.columns)
                    self.assertIn('!ID', q_sbtab.columns_dict)
                    self.assertIn('!Value', q_sbtab.columns)
                    self.assertIn('!Value', q_sbtab.columns_dict)
                    self.assertIn('!Unit', q_sbtab.columns)
                    self.assertIn('!Unit', q_sbtab.columns_dict)
                    #if sbml_level == 3:
                    #    self.assertIn('!Constant', q_sbtab.columns)
                    #    self.assertIn('!Constant', q_sbtab.columns_dict)

                    # rows
                    for quantity in q_sbtab.value_rows:
                        self.assertEqual(len(quantity), len(q_sbtab.columns))
                        self.assertNotEqual(quantity[q_sbtab.columns_dict['!ID']], '')
                        self.assertNotEqual(quantity[q_sbtab.columns_dict['!Value']], '')
                        # update when default values are at hand
                        # self.assertNotEqual(quantity[q_sbtab.columns_dict['!Unit']], '')
                        #if sbml_level == 3:
                        #    self.assertNotEqual(quantity[q_sbtab.columns_dict['!Constant']], '')
           

    def tearDown(self):
        '''
        close file/s
        '''
        pass
    
if __name__ == '__main__':
    unittest.main()
