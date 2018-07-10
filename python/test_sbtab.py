#!/usr/bin/env python
import unittest
import SBtab
import copy
import os
      
            

class TestSBtabTable(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.tables = ['teusink_compartment.csv',
                       'teusink_compound.csv',
                       'teusink_data.tsv',
                       'teusink_reaction.tsv']

        docs = ['ecoli_ccm_aerobic_ProteinComposition_haverkorn_ECM_Model.tsv']
        
        self.sbtabs = []
        for t in self.tables:
            p = open('tests/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

        self.docs = []
        for i, d in enumerate(docs):
            p = open('tests/' + d, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
            self.docs.append(sbtab)
            p.close()
            
    def test_extension_validator(self):
        '''
        test if the extension is correct or not
        '''
        correct = ['test.tsv', 'test.csv', 'test.xls']
        incorrect = ['test.xlsx', 'test.xml', 'test.txt', 'test.rtf']

        random_sbtab = self.sbtabs[0]
        for c in correct:
            self.assertTrue(random_sbtab.validate_extension(test=c))

        for ic in incorrect:
            with self.assertRaises(SBtab.SBtabError):
                random_sbtab.validate_extension(test=ic)

    def test_return_table_string(self):
        '''
        test the function that returns the table string
        '''
        for sbtab in self.sbtabs:
            table_string = sbtab.return_table_string()
            rows = table_string.split('\n')
            self.assertEqual(rows[0][:2],'!!')
            self.assertEqual(rows[1][:1],'!')
            self.assertTrue(len(rows)>2)
            for row in rows[2:]:
                self.assertEqual(len(row.split('\t')),len(sbtab.columns))

    def test_doc_row(self):
        '''
        test if the document has a doc row (!!!) and extract it
        '''
        # single SBtabs usually have no doc row
        for sbtab in self.sbtabs:
            self.assertIsNone(sbtab.doc_row)

        # SBtabDocuments always have a doc row; either given in
        # the file or generated automatically in the initialisation
        for sbtab in self.docs:
            self.assertIsNotNone(sbtab.doc_row)
            self.assertEqual(sbtab.doc_row[:8], '!!!SBtab')
            # test doc attributes here
            # self.assertIsNotNone(sbtab.doc_name, e.g.)
            # ...

    def test_header_row(self):
        '''
        test if the SBtab has a valid header row
        '''
        valid_table_types = ['Reaction', 'Compound', 'Quantity',
                             'QuantityType', 'Compartment']
        
        for sbtab in self.sbtabs:
            self.assertIsNotNone(sbtab._get_header_row())
            self.assertIsNotNone(sbtab.table_type)
            self.assertIn(sbtab.table_type, valid_table_types)
            self.assertIsNotNone(sbtab.table_name)
            self.assertEqual(sbtab.header_row[:7], '!!SBtab')
            self.assertIsNotNone(sbtab.header_row.find("'"))
            self.assertEqual(sbtab.header_row.find('"'), -1)

    def test_custom_table_information(self):
        '''
        test if custom table information can be extracted
        '''
        for sbtab in self.sbtabs:
            self.assertIsNotNone(sbtab.get_custom_table_information('TableType'))
            self.assertEqual(sbtab.get_custom_table_information('TableType'), sbtab.table_type)
            with self.assertRaises(SBtab.SBtabError):
                sbtab.get_custom_table_information('Rubbish')

    def test_dequote(self):
        '''
        test if this function can find and replace bad quotes
        '''
        test_rows = ['"test"', '\xe2\x80\x9dtest\xe2\x80\x9d',
                     '\xe2\x80\x99test\xe2\x80\x99']
        random_sbtab = self.sbtabs[0]
        for row in test_rows:
            self.assertEqual((random_sbtab.dequote(row)).find('"'), -1)
            self.assertEqual((random_sbtab.dequote(row)).find('\xe2\x80\x9d'), -1)
            self.assertEqual((random_sbtab.dequote(row)).find('\xe2\x80\x99'), -1)
            self.assertNotEqual((random_sbtab.dequote(row)).find("'"), -1)

    def test_get_columns(self):
        '''
        test if the columns are extracted correctly
        '''
        for sbtab in self.sbtabs:
            (column_names, columns) = sbtab.get_columns()
            self.assertIsNotNone(column_names)
            self.assertIsNotNone(columns)
            self.assertNotIn('', column_names)
            for index in columns.values():
                self.assertEqual(type(index), int)
            self.assertEqual(len(column_names), len(columns))
            self.assertEqual(sorted(sbtab.columns), sorted(sbtab.columns_dict.keys()))

    def test_get_rows(self):
        '''
        test if the value rows are extracted correctly
        '''
        for sbtab in self.sbtabs:
            value_rows = sbtab.get_rows()
            self.assertIsNotNone(value_rows)
            self.assertNotEqual(len(value_rows), 0)
            for row in value_rows:
                self.assertEqual(len(row), len(sbtab.columns))

    def test_to_data_frame(self):
        '''
        test export to pandas dataframe (still rather simple)
        '''
        for sbtab in self.sbtabs:
            df = sbtab.to_data_frame()
            self.assertIsNotNone(df)
            
    def test_change_value(self):
        '''
        function changes a value in the SBtab file
        change value receives (row_number, column_number, new_value)
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.change_value(1,1,'new_value'))
                       

    def test_change_value_by_name(self):
        '''
        function changes a value in the SBtab file by given row id and column name
        change value by name receives (row_id (=first column), column_name (!x), new_value)
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.change_value_by_name(sbtab.value_rows[0][0],
                                                       sbtab.columns[0], '2'))

    def test_create_list(self):
        '''
        function creates a list object of the SBtab contents
        [[header],[columns],[[row],[row],[row],[row]]]
        '''
        for sbtab in self.sbtabs:
            sbtab_list = sbtab.create_list()
            self.assertEqual(len(sbtab_list), 3)
            self.assertEqual(sbtab_list[0][0], sbtab.header_row)
            self.assertEqual(sbtab_list[1], sbtab.columns)
            self.assertEqual(sbtab_list[2], sbtab.value_rows)
            
    def test_add_row(self):
        '''
        function adds a row to the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.add_row(sbtab.value_rows[0]))
            self.assertTrue(sbtab.add_row(sbtab.value_rows[0], 4))
            with self.assertRaises(SBtab.SBtabError): sbtab.add_row(sbtab.value_rows[0], '4')
        
    def test_remove_row(self):
        '''
        function removes a row from the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.remove_row(1))
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_row('4')
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_row(5000)

    def test_add_column(self):
        '''
        function adds a column to the SBtab table
        '''
        for sbtab in self.sbtabs:
            test_column = ['X'] * (len(sbtab.value_rows) + 1)
            self.assertTrue(sbtab.add_column(test_column))
            self.assertTrue(sbtab.add_column(test_column, 0))
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[0])
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[:(len(test_column)-1)])
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[0], '4')
            
    def test_remove_row(self):
        '''
        function removes a column from the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.remove_column(1))
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_column('4')
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_column(5000)

    def test_write_sbtab(self):
        '''
        function writes SBtab to hard drive
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.write(sbtab.filename))

            get_back = open(sbtab.filename, 'r')
            get_back_content = get_back.read()
            get_back_sbtab = SBtab.SBtabTable(get_back_content, sbtab.filename)
            get_back.close()

            self.assertEqual(sbtab.header_row.rstrip(), get_back_sbtab.header_row.rstrip())
            self.assertEqual(sbtab.columns, get_back_sbtab.columns)
            self.assertEqual(sbtab.value_rows, get_back_sbtab.value_rows)

    def test_transpose_table(self):
        '''
        function transposes the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.transpose_table())
            sbtab_transposed = copy.deepcopy(sbtab)
            sbtab_transposed.transpose_table()
            self.assertEqual((len(sbtab.value_rows) + 1),
                             len(sbtab_transposed.columns))
            self.assertEqual((len(sbtab_transposed.value_rows) + 1),
                             len(sbtab.columns))
        
    def tearDown(self):
        '''
        close file/s
        '''
        for table in self.tables:
            try:
                os.remove(table)
            except OSError:
                pass


class TestSBtabDocument(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabDocument class with files from test directory
        '''
        docs = ['ecoli_ccm_aerobic_ProteinComposition_haverkorn_ECM_Model.tsv']

        self.sbtab_documents = []
        for d in docs:
            p = open('tests/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

    def tearDown(self):
        '''
        tear down function
        '''
        pass

    
if __name__ == '__main__':
    unittest.main()
