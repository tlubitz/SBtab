#!/usr/bin/env python
import unittest
import sys
import os
import copy

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import sbtab2sbml

class TestSBtabConversion(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]

        self.sbtab_docs = []
        self.convert_document_objects = []

        for i, t in enumerate(self.table_names):
            if t.startswith('_'): continue
            p = open('tables/' + t, 'r')
            p_content = p.read()
            sbtab_doc = SBtab.SBtabDocument('test_' + str(i), sbtab_init=p_content, filename=t)
            if 'Reaction' in sbtab_doc.type_to_sbtab.keys() or 'Compound' in sbtab_doc.type_to_sbtab.keys():
                conv = sbtab2sbml.SBtabDocument(sbtab_doc)
                self.convert_document_objects.append(conv)
                self.sbtab_docs.append(sbtab_doc)
            p.close()
            
        for i, d in enumerate(self.doc_names):
            if not d.startswith('_'):
                p = open('docs/' + d, 'r')
                p_content = p.read()
                sbtab_doc = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
                if 'Reaction' in sbtab_doc.type_to_sbtab.keys() or 'Compound' in sbtab_doc.type_to_sbtab.keys():
                    conv = sbtab2sbml.SBtabDocument(sbtab_doc)
                    self.convert_document_objects.append(conv)
                    self.sbtab_docs.append(sbtab_doc)
                p.close()

    def test_object_creation(self):
        '''
        test if the SBtabs have arrived safely in the conversion object
        '''
        for i, vto in enumerate(self.convert_document_objects):
            previous_sbtab_doc = self.sbtab_docs[i]
            self.assertEqual(previous_sbtab_doc, vto.sbtab_doc)
            self.assertEqual(previous_sbtab_doc.doc_row, vto.sbtab_doc.doc_row)
            self.assertEqual(previous_sbtab_doc.sbtabs, vto.sbtab_doc.sbtabs)
            for j, sbtab in enumerate(vto.sbtab_doc.sbtabs):
                previous_sbtab = previous_sbtab_doc.sbtabs[j]
                self.assertEqual(previous_sbtab, sbtab)
                self.assertEqual(previous_sbtab.header_row, sbtab.header_row)
                self.assertEqual(previous_sbtab.columns, sbtab.columns)
                self.assertEqual(previous_sbtab.columns_dict, sbtab.columns_dict)
                self.assertEqual(previous_sbtab.value_rows, sbtab.value_rows)
                self.assertEqual(previous_sbtab.table_type, sbtab.table_type)

    def test_conversion(self):
        '''
        test if the conversion can be processed
        '''
        for i, vto in enumerate(self.convert_document_objects):
            previous_sbtab_doc = self.sbtab_docs[i]
            for v in ['24', '31']:
                (sbml_string, warnings) = vto.convert_to_sbml(v)

                # this can be uncommented to check the sbml files manually
                # for syntactic correctness, e.g. via SBML online validator
                # f = open('sbml/' + vto.sbtab_doc.filename[:-4]+v+'.xml','w')
                # f.write(sbml_string)
                # f.close()
                
                sbml_doc = vto.new_document
                sbml_model = sbml_doc.getModel()

                # check document and model details
                level = sbml_doc.getLevel()
                version = sbml_doc.getVersion()
                self.assertEqual(level, int(v[0]))
                self.assertEqual(version, int(v[1]))
                #self.assertTrue(sbml_model.isSetId())
                self.assertTrue(sbml_model.isSetName())

                # check compartment details
                self.assertNotEqual(sbml_model.getNumCompartments(), 0)
                if 'Compartment' in previous_sbtab_doc.type_to_sbtab.keys():
                    sbtab_compartments = previous_sbtab_doc.type_to_sbtab['Compartment']
                    for sbtab_compartment in sbtab_compartments:
                        self.assertEqual(len(sbtab_compartment.value_rows), sbml_model.getNumCompartments())
                    for compartment in sbml_model.getListOfCompartments():
                        self.assertTrue(compartment.isSetId())
                        self.assertTrue(compartment.isSetName())
                        self.assertTrue(compartment.isSetSize())
                        self.assertTrue(compartment.isSetConstant())

                # check compound details
                self.assertNotEqual(sbml_model.getNumSpecies(), 0)
                if 'Compound' in previous_sbtab_doc.type_to_sbtab.keys():
                    sbtab_compounds = previous_sbtab_doc.type_to_sbtab['Compound']
                    for sbtab_compound in sbtab_compounds:
                        self.assertEqual(len(sbtab_compound.value_rows), sbml_model.getNumSpecies())

                    for species in sbml_model.getListOfSpecies():
                        self.assertTrue(species.isSetId())
                        self.assertTrue(species.isSetName())
                        self.assertTrue(species.isSetCompartment())
                        self.assertTrue(species.isSetConstant())
                        self.assertTrue(species.isSetBoundaryCondition())

                # check reaction details
                if 'Reaction' in previous_sbtab_doc.type_to_sbtab.keys():
                    self.assertNotEqual(sbml_model.getNumReactions(), 0)
                    sbtab_reactions = previous_sbtab_doc.type_to_sbtab['Reaction']
                    for sbtab_reaction in sbtab_reactions:
                        self.assertEqual(len(sbtab_reaction.value_rows), sbml_model.getNumReactions())

                    for reaction in sbml_model.getListOfReactions():
                        self.assertTrue(reaction.isSetId())
                        self.assertTrue(reaction.isSetName())
                        self.assertTrue(reaction.isSetFast())
                        self.assertTrue(reaction.isSetReversible())
                        for substrate in reaction.getListOfReactants():
                            self.assertTrue(substrate.isSetSpecies())
                            if v == '31': self.assertTrue(substrate.isSetConstant())
                        for product in reaction.getListOfProducts():
                            self.assertTrue(product.isSetSpecies())
                            if v == '31': self.assertTrue(product.isSetConstant())
                
    def tearDown(self):
        '''
        close file/s
        '''
        for table in self.table_names:
            try:
                os.remove(table)
            except OSError:
                pass

        for doc in self.doc_names:
            try:
                os.remove(doc)
            except OSError:
                pass

    
if __name__ == '__main__':
    unittest.main()
