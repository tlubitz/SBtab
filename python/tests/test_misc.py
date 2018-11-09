#!/usr/bin/env python
import unittest
import os
import sys
import libsbml

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import misc
import SBtab

class TestMiscFunctions(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('python/tests/tables/') if os.path.isfile(os.path.join('python/tests/tables/', f))]
        self.doc_names = [f for f in os.listdir('python/tests/docs/') if os.path.isfile(os.path.join('python/tests/docs/', f))]
        self.sbml_names = [f for f in os.listdir('python/tests/sbml/') if os.path.isfile(os.path.join('python/tests/sbml/', f))]
        
        self.sbtabs = []
        for t in self.table_names:
            if not t.startswith('_'):
                p = open('python/tests/tables/' + t, 'r')
                p_content = p.read()
                sbtab = SBtab.SBtabTable(p_content, t)
                self.sbtabs.append(sbtab)
                p.close()

        self.docs = []
        for i, d in enumerate(self.doc_names):
            if not d.startswith('_'):
                p = open('python/tests/docs/' + d, 'r')
                p_content = p.read()
                sbtab = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
                self.docs.append(sbtab)
                p.close()


        self.sbml_docs = []
        reader = libsbml.SBMLReader()
        for i, s in enumerate(self.sbml_names):
            if s.startswith('_'): continue
            doc = reader.readSBML('python/tests/sbml/' + s)
            self.sbml_docs.append(doc)
            

    def test_tab_counter(self):
        '''
        test if the amount of SBtabs in one file can be determined
        '''
        for sbtab in self.sbtabs:
            amount = misc.count_tabs(sbtab.to_str())
            self.assertEqual(amount,1)

    def test_extension_validator(self):
        '''
        test if the file extension can be validated
        '''
        for sbtab_name in self.table_names:
            self.assertTrue(misc.validate_file_extension(sbtab_name, 'sbtab'))

        for sbtab_name in self.doc_names:
            self.assertTrue(misc.validate_file_extension(sbtab_name, 'sbtab'))
            
        for sbml_name in self.sbml_names:
            self.assertTrue(misc.validate_file_extension(sbml_name, 'sbml'))
        
        for bad_name in ['test.txt', 'test.xls', 'test.rtf', 'test.pdf', 'test.m']:
            self.assertFalse(misc.validate_file_extension(bad_name, 'sbml'))
            self.assertFalse(misc.validate_file_extension(bad_name, 'sbtab'))

    def test_delimiter_check(self):
        '''
        test if the delimiter can be determined
        '''
        for sbtab in self.sbtabs:
            self.assertNotEqual(misc.check_delimiter(sbtab.to_str()), False)

        for doc in self.docs:
            for sbtab in doc.sbtabs:
                self.assertNotEqual(misc.check_delimiter(sbtab.to_str()), False)

        for sbml in self.sbml_docs:
            self.assertFalse(misc.check_delimiter(sbml))

        
    def test_sbtab_splitter(self):
        '''
        test if multiple sbtabs in one input file can be splitted correctly
        '''
        p = open('python/tests/docs/teusink.tsv', 'r')
        p_content = p.read()
        sbtabs = misc.split_sbtabs(p_content)
        self.assertEqual(4, len(sbtabs))
        for sbtab in sbtabs:
            self.assertEqual(sbtab[0:7],'!!SBtab')
        p.close()       
        
    
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
