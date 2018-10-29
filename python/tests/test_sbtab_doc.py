#!/usr/bin/env python
import unittest
import os
import sys            

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import misc

class TestSBtabDocument(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabDocument class with files from test directory
        '''
        #self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.table_names = ['teusink_compartment.csv', 'teusink_compound.csv',
                            'teusink_data.tsv', 'teusink_reaction.tsv']
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]

        self.sbtabs = []
        for t in self.table_names:
            p = open('tables/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

        self.docs = []
        for i, d in enumerate(self.doc_names):
            if not d.startswith('_'):
                p = open('docs/' + d, 'r')
                p_content = p.read()
                sbtab_doc = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
                self.docs.append(sbtab_doc)
                p.close()

    def test_add_sbtab(self):
        '''
        test if sbtab objects can be added to the document correctly
        '''
        for doc in self.docs:
            # add sbtabs, test if amount is correct
            amount_sbtabs_before = len(doc.sbtabs)
            for sbtab in self.sbtabs:
                self.assertTrue(doc.add_sbtab(sbtab))
                self.assertIn(sbtab, doc.sbtabs)
                self.assertIn(sbtab.table_name, doc.name_to_sbtab)
                self.assertIn(sbtab.table_type, doc.type_to_sbtab)
                self.assertIn(sbtab.filename, doc.sbtab_filenames)
                self.assertIsNotNone(doc.doc_row)
                self.assertEqual(doc.sbtabs[-1].header_row, sbtab.header_row)
                self.assertEqual(doc.sbtabs[-1].columns, sbtab.columns)
                self.assertEqual(doc.sbtabs[-1].value_rows, sbtab.value_rows)
                self.assertEqual(doc.sbtabs[-1].table_type, sbtab.table_type)                
            amount_sbtabs_after = len(doc.sbtabs)
            self.assertEqual(amount_sbtabs_before + len(self.sbtabs),
                             amount_sbtabs_after)

        # is an Error raised if the table type is corrupt?
        sbtab.table_type = 'rubbish'
        with self.assertRaises(SBtab.SBtabError):
            doc.add_sbtab(sbtab)
            
    def test_add_sbtab_string(self):
        '''
        test if sbtab strings can be added to the document correctly
        '''
        for doc in self.docs:
            # add sbtabs, test if amount is correct
            amount_sbtabs_before = len(doc.sbtabs)
            for sbtab in self.sbtabs:
                self.assertTrue(doc.add_sbtab_string(sbtab.to_str(), sbtab.filename))
                self.assertIn(sbtab.table_name, doc.name_to_sbtab)
                self.assertIn(sbtab.table_type, doc.type_to_sbtab)
                self.assertIn(sbtab.filename, doc.sbtab_filenames)
                self.assertIsNotNone(doc.doc_row)
                self.assertEqual(doc.sbtabs[-1].header_row, sbtab.header_row)
                self.assertEqual(doc.sbtabs[-1].columns, sbtab.columns)
                self.assertEqual(doc.sbtabs[-1].value_rows, sbtab.value_rows)
                self.assertEqual(doc.sbtabs[-1].table_type, sbtab.table_type)                
            amount_sbtabs_after = len(doc.sbtabs)
            self.assertEqual(amount_sbtabs_before + len(self.sbtabs),
                             amount_sbtabs_after)

        # is an Error raised if the table type is corrupt?
        sbtab.table_type = 'rubbish'
        with self.assertRaises(SBtab.SBtabError):
            doc.add_sbtab(sbtab)
       
    def test_check_type_validity(self):
        '''
        test if the table types are checked accurately
        '''
        valid_table_types = misc.extract_supported_table_types()
        
        for t in valid_table_types:
            self.assertTrue(self.docs[0].check_type_validity(t))
        with self.assertRaises(SBtab.SBtabError):
            self.docs[0].check_type_validity('Rubbish')
        
    def test_doc_row_attributes(self):
        '''
        test if doc row attributes are read correctly
        '''
        pass

    def test_set_version(self):
        '''
        test if version is set correctly
        '''
        version = '1.0'
        for doc in self.docs:
            doc.set_version(version)
            self.assertEqual(doc.version, version)

    def test_set_date(self):
        '''
        test if date is set correctly
        '''
        date = '1.1.1990'
        for doc in self.docs:
            doc.set_date(date)
            self.assertEqual(doc.date, date)
        
    def test_set_doc_type(self):
        '''
        test if doc_type is set correctly
        '''
        doc_type = 'ReactionCollection'
        for doc in self.docs:
            doc.set_doc_type(doc_type)
            self.assertEqual(doc.doc_type, doc_type)
        
    def test_set_name(self):
        '''
        test if name is set correctly
        '''
        name = 'New Name'
        for doc in self.docs:
            doc.set_name(name)
            self.assertEqual(doc.name, name)


    def test_remove_sbtab_by_name(self):
        '''
        test if SBtab can be removed by name
        '''
        # test files
        document = self.docs[0]
        sbtab = document.sbtabs[0]
        
        # initialise before status
        sbtab_name = sbtab.table_name
        sbtab_type = sbtab.table_type
        amount_sbtabs = len(document.sbtabs)
        amount_name_to_sbtab = len(document.name_to_sbtab)
        amount_type_to_sbtab = len(document.type_to_sbtab[sbtab_type])
        amount_sbtab_filenames = len(document.sbtab_filenames)

        # remove sbtab by name
        self.assertTrue(document.remove_sbtab_by_name(sbtab_name))

        # verify after status
        self.assertEqual(amount_sbtabs - 1, len(document.sbtabs))
        self.assertEqual(amount_name_to_sbtab - 1, len(document.name_to_sbtab))
        self.assertEqual(amount_type_to_sbtab - 1, len(document.type_to_sbtab[sbtab_type]))
        self.assertEqual(amount_sbtab_filenames - 1, len(document.sbtab_filenames))
        self.assertNotIn(sbtab, document.sbtabs)
        self.assertNotIn(sbtab_name, document.name_to_sbtab)

    def test_get_sbtab_by_name(self):
        '''
        test if SBtabs can be fetched by name
        '''
        for doc in self.docs:
            names = doc.name_to_sbtab.keys()
            for name in names:
                self.assertIsNotNone(doc.get_sbtab_by_name(name))
                sbtab = doc.get_sbtab_by_name(name)
                self.assertEqual(name, sbtab.table_name)


    def test_get_sbtab_by_type(self):
        '''
        test if SBtabs can be fetched by type
        '''
        for doc in self.docs:
            types = doc.type_to_sbtab.keys()
            for t in types:
                self.assertIsNotNone(doc.get_sbtab_by_type(t))
                sbtabs_tt = doc.get_sbtab_by_type(t)
                for sbtab_tt in sbtabs_tt:
                    self.assertEqual(t, sbtab_tt.table_type)
                    
    def test_write_sbtab_doc(self):
        '''
        function writes SBtabDocument to hard drive
        '''
        for doc in self.docs:
            self.assertTrue(doc.write())

            get_back = open(doc.filename, 'r')
            get_back_content = get_back.read()
            get_back_doc = SBtab.SBtabDocument(doc.name, get_back_content, doc.filename)
            get_back.close()

            self.assertEqual(doc.doc_row.rstrip(), get_back_doc.doc_row.rstrip())
            
            old_sbtabs = doc.sbtabs
            new_sbtabs = get_back_doc.sbtabs
            for i, os in enumerate(old_sbtabs):
                self.assertEqual(os.header_row, new_sbtabs[i].header_row)
                self.assertEqual(os.columns, new_sbtabs[i].columns)
                self.assertEqual(os.value_rows, new_sbtabs[i].value_rows)
                self.assertEqual(os.table_type, new_sbtabs[i].table_type)
                self.assertEqual(os.table_name, new_sbtabs[i].table_name)

    def test_set_doc_row(self):
        '''
        test if doc_row can be set properly
        '''
        test_doc_row = "!!!SBtab SBtabVersion='1.0' DocumentType='ReactionCollection' Date='1.1.1990' Document='DocumentName'"

        for doc in self.docs:
            doc.set_doc_row(test_doc_row)
            self.assertEqual(doc.version, '1.0')
            self.assertEqual(doc.doc_type, 'ReactionCollection')
            self.assertEqual(doc.date, '1.1.1990')
            self.assertEqual(doc.name, 'DocumentName')

    def test_get_custom_attributes(self):
        '''
        test if doc row can be read properly
        '''
        test_doc_row = "!!!SBtab SBtabVersion='1.0' DocumentType='ReactionCollection' Date='1.1.1990' Document='DocumentName'"

        for doc in self.docs:
            self.assertEqual(doc.get_custom_doc_information('SBtabVersion', test_row=test_doc_row), '1.0')
            self.assertEqual(doc.get_custom_doc_information('DocumentType', test_row=test_doc_row), 'ReactionCollection')
            self.assertEqual(doc.get_custom_doc_information('Date', test_row=test_doc_row), '1.1.1990')
            self.assertEqual(doc.get_custom_doc_information('Document', test_row=test_doc_row), 'DocumentName')
            
    def tearDown(self):
        '''
        tear down function
        '''
        for doc in self.doc_names:
            try:
                os.remove(doc)
            except OSError:
                pass

    
if __name__ == '__main__':
    unittest.main()
