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
        self.sbml_strings = []
        reader = libsbml.SBMLReader()
        for i, s in enumerate(self.sbml_names):
            if s.startswith('_'): continue
            # save SBML objects
            doc = reader.readSBML('python/tests/sbml/' + s)
            self.sbml_docs.append(doc)

            # also save the strings
            sbml = open('python/tests/sbml/' + s, 'r')
            self.sbml_strings.append(sbml.read())
            sbml.close()
            
    def test_count_tabs(self):
        '''
        test if the amount of SBtabs in one file can be determined
        '''
        for sbtab in self.sbtabs:
            amount = misc.count_tabs(sbtab.to_str())
            self.assertEqual(amount, 1)

        for doc in self.docs:
            amount = misc.count_tabs(doc.to_str())
            self.assertGreaterEqual(amount, 1)

    def test_validate_file_extension(self):
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

    def test_check_delimiter(self):
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
        
    def test_split_sbtabs(self):
        '''
        test if multiple sbtabs in one input file can be splitted correctly
        '''
        for doc in self.docs:
            amount = misc.count_tabs(doc.to_str())
            sbtabs = misc.split_sbtabs(doc.to_str())
            self.assertEqual(amount, len(sbtabs))
            for sbtab in sbtabs:
                self.assertEqual(sbtab[0:7],'!!SBtab')    

    def test_sbtab_to_html(self):
        '''
        test if SBtab tables and documents can be converted to an HTML view
        '''
        self.assertFalse(misc.sbtab_to_html(self.sbtabs[0].to_str()))
        self.assertFalse(misc.sbtab_to_html(self.sbtabs[0], mode='TrashMode'))
        
        for sbtab in self.sbtabs:
            sbtab_html = misc.sbtab_to_html(sbtab, mode='standalone')
            self.assertEqual(str, type(sbtab_html))
            self.assertTrue(sbtab_html.startswith('<html'))
            self.assertTrue(sbtab_html.endswith('</html>'))
            self.assertIn('<h2>%s</h2>' % sbtab.filename, sbtab_html)

        for doc in self.docs:
            sbtab_html = misc.sbtab_to_html(doc, mode='standalone')
            self.assertEqual(str, type(sbtab_html))
            self.assertTrue(sbtab_html.startswith('<html'))
            self.assertTrue(sbtab_html.endswith('</html>'))
            self.assertIn('<h2>%s</h2>' % doc.filename, sbtab_html)
            
    def test_open_definitions_file(self):
        '''
        PART 1 OF 3:
        test if the definitions file can be read and correctly processed
        '''
        self.assertFalse(misc.open_definitions_file(_path='/trashpath/definitions.tsv'))
        sbtab_def = misc.open_definitions_file()
        self.assertEqual(type(sbtab_def),SBtab.SBtabTable)
        self.assertEqual(sbtab_def.filename, 'definitions.tsv')
        self.assertEqual(sbtab_def.table_type, 'Definition')
        self.assertIn('!ComponentName', sbtab_def.columns)
        self.assertIn('!ComponentType', sbtab_def.columns)
        self.assertIn('!IsPartOf', sbtab_def.columns)
        self.assertIn('!isShortname', sbtab_def.columns)
        self.assertIn('!Format', sbtab_def.columns)
        self.assertIn('!Description', sbtab_def.columns)
        self.assertGreater(len(sbtab_def.value_rows), 1)

    def test_extract_supported_table_types(self):
        '''
        PART 2 OF 3:
        test (with examples) if the definitions file can be used to extract the supported table types
        '''
        table_types = misc.extract_supported_table_types()
        self.assertIn('Reaction', table_types)
        self.assertIn('Compound', table_types)
        self.assertIn('Quantity', table_types)
        
    def test_find_descriptions(self):
        '''
        PART 3 OF 3:
        test if the descriptions can be read from the definitions file and
        the correct table types are inherent
        '''
        sbtab_def = misc.open_definitions_file()
        table_types = misc.extract_supported_table_types()
        for tt in table_types:
            (col2description, col2link) = misc.find_descriptions(sbtab_def, tt)
            self.assertNotEqual(col2description, {})
            self.assertNotEqual(col2link, {})
            for entry in col2link:
                self.assertEqual(entry[0], '!')
                self.assertTrue(col2link[entry] == 'True' or col2link[entry] == 'False')

    def test_xlsx_to_tsv_and_tab_to_xlsx(self):
        '''
        test if xlsx files can be converted to tsv files
        (ALSO test if SBtab files can be converted to xlsx)
        '''
        for sbtab in self.sbtabs:
            # first convert SBtab objects to xlsx
            sbtab_xlsx = misc.tab_to_xlsx(sbtab)
            self.assertEqual(type(sbtab_xlsx),bytes)

            # then convert to tsv string
            sbtab_tsv = misc.xlsx_to_tsv(sbtab_xlsx)
            self.assertEqual(type(sbtab_tsv),str)
            self.assertEqual(sbtab_tsv[0:2], '!!')

            # last: try to convert the string to an SBtab document,
            # also test if the final sbtab equals the initial one
            sbtab_doc = SBtab.SBtabDocument(sbtab.filename, sbtab_tsv, sbtab.filename)
            self.assertEqual(type(sbtab_doc), SBtab.SBtabDocument)
            self.assertEqual(sbtab.filename, sbtab_doc.filename)
            self.assertEqual(sbtab.columns, sbtab_doc.sbtabs[0].columns)

    def test_xml_to_html(self):
        '''
        test if xml (SBML) files can be converted to an html view
        '''
        for sbml in self.sbml_strings:
            sbml_html = misc.xml_to_html(sbml)
            self.assertEqual(str, type(sbml_html))
            self.assertTrue(sbml_html.startswith('<xmp>'))
            self.assertTrue(sbml_html.endswith('</xmp>'))
            self.assertGreater(len(sbml_html), 10)
    
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
