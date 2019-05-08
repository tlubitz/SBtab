# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import validatorSBtab
import sbml2sbtab
import sbtab2sbml
import libsbml
import misc
import SBtab
import os
import copy

def index():
    return dict()

def gettingstarted():
    return dict()

def documentation():
    return dict()

def downloads():
    return dict()

def team():
    return dict()

def clearsession():
    session.sbtabs = []
    session.sbtab_filenames = []
    session.sbtab_docnames = []
    session.types = []
    session.name2doc = {}
    session.todeletename = []
    session.sbtab_fileformat = []    

    session.sbmls = []
    session.sbml_filenames = []
    session.sbml_fileformat = []

    session.definition_file = []
    session.definition_file_name = []
    session.new_def = False

    session.warnings_val = []
    session.warnings_con = []
    session.warnings_def = []
    
    redirect(URL('index.html'))

def validator():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simple replace the two lines below with:
    return auth.wiki()
    """
    response.title    = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Online Validator')

    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp",
                                  label='Upload SBtab file (.csv, .tsv, .xlsx)',
                                  requires=IS_LENGTH(10485760, 1,
                                                     error_message='Max upload size: 10MB')))
    filename = None
    output = []


    # load the definition file which is required for validation
    if not session.definition_file:
        try:
            sbtab_def = misc.open_definitions_file(os.path.dirname(os.path.abspath(__file__)) + '/../static/files/default_files/definitions.tsv')
            session.definition_file = sbtab_def
            session.definition_file_name = sbtab_def.filename
        except:
            session.warnings_val.append('There was an error reading the definition file.')

    
    #update session lists
    if lform.process().accepted:
        response.flash = 'form accepted'

        # initialise session variables
        session.warnings_val = []
        if 'sbtabs' not in session:
            session.sbtabs = []
            session.sbtab_filenames = []
            session.sbtab_docnames = []
            session.types = []
            session.name2doc = {}
            
        # validate file name
        try:
            sbtab_file = request.vars.File.value.decode('utf-8', 'ignore')
        except:
            session.warnings_val.append('The file has a faulty encryption. Please use UTF-8 instead.')
            redirect(URL(''))

        filename = request.vars.File.filename
        if not filename.endswith('.tsv') and not filename.endswith('.csv') and not filename.endswith('.xlsx'):
            session.warnings_val.append('The file does not have a correct file format. Please use csv/tsv/xlsx only.')
            redirect(URL(''))

        # convert from xlsx to csv if required
        if filename.endswith('.xlsx'):
            sbtab_file = request.vars.File.value
            try:
                sbtab_file = misc.xlsx_to_tsv(sbtab_file)
            except:
                session.warnings_val.append('The xlsx file could not be converted to SBtab. Please ensure file format validity.')
                redirect(URL(''))

        # check if there are more than one SBtab files in the file and create SBtabTable or SBtabDocument
        
        try:
            sbtab_amount = misc.count_tabs(sbtab_file)
        except:
            session.warnings_val.append('The SBtab %s could not be read properly.' % sbtab.filename)
            redirect(URL(''))

        if sbtab_amount > 1:
            try:
                sbtab_strings = misc.split_sbtabs(sbtab_file)
                sbtab_doc = SBtab.SBtabDocument(filename)
                session.sbtab_docnames.append(filename)
                for i, sbtab_string in enumerate(sbtab_strings):
                    name_single = filename[:-4] + str(i) + filename[-4:]
                    sbtab = SBtab.SBtabTable(sbtab_string, name_single)
                    new_name = filename[:-4] + '_' + sbtab.table_id + filename[-4:]
                    sbtab.change_filename(new_name)
                    if new_name not in session.sbtab_filenames:
                        sbtab_doc.add_sbtab(sbtab)
                        session.sbtabs.append(sbtab)
                        session.types.append(sbtab.table_type)
                        session.sbtab_filenames.append(new_name)
                        session.name2doc[new_name] = filename

                    else:
                        session.warnings_val.append('The SBtab %s is duplicate.' % sbtab.filename)
                        redirect(URL(''))
            except:
                session.warnings_val.append('The SBtab Document object could not be created properly.')
                redirect(URL(''))
        else:
            try:
                sbtab = SBtab.SBtabTable(sbtab_file, filename)
                session.sbtabs.append(sbtab)
                session.sbtab_filenames.append(sbtab.filename)
                session.types.append(sbtab.table_type)
                session.sbtab_docnames.append(sbtab.filename)
                session.name2doc[sbtab.filename] = sbtab.filename
            except:
                session.warnings_val.append('The SBtab Table object could not be created properly.')
                redirect(URL(''))
    elif lform.errors:
        response.flash = 'form has errors'

    # buttons
    # validate
    if request.vars.validate_button:
        try:
            filename = session.sbtab_filenames[int(request.vars.validate_button)]
            TableValidClass = validatorSBtab.ValidateTable(session.sbtabs[int(request.vars.validate_button)], session.definition_file)
            output = TableValidClass.return_output()
        except:
            session.warnings_val.append('The file could not be validated. It seems to be broken.')
            redirect(URL(''))

    # erase
    if request.vars.erase_button:
        flname = session.sbtab_filenames[int(request.vars.erase_button)]
        del session.sbtabs[int(request.vars.erase_button)]
        del session.sbtab_filenames[int(request.vars.erase_button)]
        del session.types[int(request.vars.erase_button)]
        doc_name = session.name2doc[flname]
        # this IF is important: you must only delete the document from the list
        # IF there are no more files attached to it
        if list(session.name2doc.values()).count(doc_name) == 1:
            session.sbtab_docnames.remove(doc_name)
        del session.name2doc[flname]
        session.warnings_val = []
        redirect(URL(''))

    # erase all
    if request.vars.remove_all_button_val:
        try:
            remove_document = session.sbtab_docnames[int(request.vars.remove_all_button_val)]

            # gather indices of entries to remove
            remove_sbtabs = []
            remove_filenames = []
            for i, s in enumerate(session.sbtabs):
                if session.name2doc[s.filename] == remove_document:
                    remove_sbtabs.append(i)

            # delete sbtabs, names, and types
            remove = sorted(remove_sbtabs,reverse=True)
            for rs in remove:
                remove_filenames.append(session.sbtab_filenames[rs])
                del session.sbtabs[rs]
                del session.sbtab_filenames[rs]
                del session.types[rs]

            # delete document name
            del session.sbtab_docnames[int(request.vars.remove_all_button_val)]

            # delete name2doc entries
            for entry in remove_filenames:
                del session.name2doc[entry]

            session.warnings_val = []
            redirect(URL(''))
        except: redirect(URL(''))


    return dict(UPL_FORM=lform, DEF_FILE_NAME=session.definition_file_name,
                SBTAB_LIST=session.sbtabs, NAME_LIST=session.sbtab_filenames,
                SBTAB_VAL=filename, DOC_NAMES=session.sbtab_docnames,
                NAME2DOC=session.name2doc, OUTPUT=output,
                WARNINGS=session.warnings_val)

def converter():
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('SBML / SBtab Conversion')

    session.sbmlid2label = {'24':'_SBML_L2V4',
                            '31':'_SBML_L3V1'}

    # initialise required variables and files
    if not 'warnings_con' in session:
        session.warnings_con = []

    if not session.definition_file:
        try:
            sbtab_def = misc.open_definitions_file(os.path.dirname(os.path.abspath(__file__)) + '/../static/files/default_files/definitions.tsv')
            #def_path = os.path.dirname(os.path.abspath(__file__)) + '/../static/files/default_files/definitions.tsv'
            #def_file_open = open(def_path)
            #def_file_open = open('/sbtab/static/files/default_files/definitions.tsv') # deprecated?
            #def_file = def_file_open.read()
            #definition_name = 'definitions.tsv'
            #sbtab_def = SBtab.SBtabTable(def_file, definition_name)
            session.definition_file = sbtab_def
            session.definition_file_name = sbtab_def.filename
        except:
            session.warnings_con.append('There was an error reading the definition file.')
            redirect(URL(''))

    if 'sbtabs' not in session:
        session.sbtabs = []
        session.sbtab_filenames = []
        session.sbtab_docnames = []
        session.name2doc = {}
        session.types = []
    
    # #########################################################################
    # form for SBtab files
    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp",
                                  label='Upload SBtab file to convert (.csv, .tsv, .xlsx)',
                                  requires=IS_LENGTH(10485760, 1,
                                                     error_message='Max upload size: 10MB')))
    
    if lform.process(formname='form_one').accepted:
        session.warnings_con = []
        response.flash = 'form accepted'

        # validate file encoding and name
        try: sbtab_file = request.vars.File.value.decode('utf-8', 'ignore')
        except:
            session.warnings_con.append('The file does not adhere to spreadsheet standards.')
            redirect(URL(''))
        
        filename = request.vars.File.filename
        if not filename.endswith('.tsv') and not filename.endswith('.csv') and not filename.endswith('.xlsx'):
            session.warnings_con.append('The file does not have a correct file format. Please use csv/tsv/xlsx only.')
            redirect(URL(''))

        # convert from xlsx to csv if required
        if filename.endswith('.xlsx'):
            sbtab_file = request.vars.File.value
            try:
                sbtab_file = misc.xlsx_to_tsv(sbtab_file)
            except:
                session.warnings_con.append('The xlsx file could not be converted to SBtab. Please ensure file format validity.')
                redirect(URL(''))
                        
        # check if there are more than one SBtab files in the file and create SBtabTable or SBtabDocument
        try: sbtab_amount = misc.count_tabs(sbtab_file)
        except:
            session.warnings_con.append('The SBtab %s could not be read properly.' % sbtab.filename)
            redirect(URL(''))

        if sbtab_amount > 1:
            try:
                sbtab_strings = misc.split_sbtabs(sbtab_file)
                sbtab_doc = SBtab.SBtabDocument(filename)
                session.sbtab_docnames.append(filename)
                for i, sbtab_string in enumerate(sbtab_strings):

                    name_single = filename[:-4] + str(i) + filename[-4:]
                    sbtab = SBtab.SBtabTable(sbtab_string, name_single)
                    new_name = filename[:-4] + '_' + sbtab.table_id + filename[-4:]
                    sbtab.change_filename(new_name)

                    if new_name not in session.sbtab_filenames:
                        sbtab_doc.add_sbtab(sbtab)
                        session.sbtabs.append(sbtab)
                        session.types.append(sbtab.table_type)
                        session.sbtab_filenames.append(new_name)
                        session.name2doc[new_name] = filename

                    else:
                        session.warnings_con.append('The SBtab %s is duplicate.' % sbtab.filename)
                        redirect(URL(''))
            except:
                session.warnings_con.append('The SBtab Document object could not be created properly.')
                redirect(URL(''))
        else:
            try:
                sbtab = SBtab.SBtabTable(sbtab_file, filename)
                session.sbtabs.append(sbtab)
                session.sbtab_filenames.append(sbtab.filename)
                session.types.append(sbtab.table_type)
                session.sbtab_docnames.append(sbtab.filename)
                session.name2doc[sbtab.filename] = sbtab.filename
            except:
                session.warnings_con.append('The SBtab Table object could not be created properly.')
                redirect(URL(''))
        redirect(URL(''))
    elif lform.errors:
        response.flash = 'form has errors'

    # #########################################################################
    # form for SBML files
    
    rform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBML file to convert (.xml)',requires=IS_LENGTH(52428800, 1, error_message='Max upload size: 50MB')))

    if rform.process(formname='form_two').accepted:
        response.flash = 'form accepted'
        session.warnings_con = []

        filename = request.vars.File.filename
        sbml_file = request.vars.File.value.decode('utf-8', 'ignore')
        if filename[-3:] != 'xml' and filename[-4:] != 'sbml':
            session.warnings_con.append('The uploaded file has a wrong extension for an SBML file.')
            redirect(URL(''))
        
        if 'sbmls' not in session:
            session.sbmls = [sbml_file]
            session.sbml_filenames = [filename]
        else:
            if filename not in session.sbml_filenames:
                session.sbmls.append(sbml_file)
                session.sbml_filenames.append(filename)
            else:
                session.warnings_con.append('An SBML file with the name %s is already stored.' % filename)
                redirect(URL(''))
        redirect(URL(''))
    elif rform.errors:
        response.flash = 'form has errors'

    # #########################################################################
    # buttons
    # convert (single) sbtab to sbml
    if request.vars.c2sbml_button24 or request.vars.c2sbml_button31:
        # determine requested SBML version
        if request.vars.c2sbml_button24 != None:
            sbml_version = '24'
            c2sbml_button = request.vars.c2sbml_button24
        else:
            sbml_version = '31'
            c2sbml_button = request.vars.c2sbml_button31

        session.warnings_con = []

        # get SBtab and add to SBtab document
        try:
            sbtab = session.sbtabs[int(c2sbml_button)]
            sbtab_doc = SBtab.SBtabDocument(sbtab.filename, sbtab)
        except:
            session.warnings_con = ['The SBtab %s could not be added to the document.' % sbtab.filename]
            redirect(URL(''))
            
        # convert SBtab document to SBML and add details to session
        try:
            ConvSBtabClass = sbtab2sbml.SBtabDocument(sbtab_doc)
            (sbml,
             session.warnings_con) = ConvSBtabClass.convert_to_sbml(sbml_version)

            filename_new = sbtab.filename[:-4] + '.xml'
            # if the sbml build up crashed:
            if not sbml:
                session.warnings_con.append('The SBtab file %s could not be c'\
                                            'onverted to SBML. Please check file'\
                                            'validity.' % sbtab.filename)
                redirect(URL(''))

            if 'sbmls' not in session:
                session.sbmls = [sbml]
                session.sbml_filenames = [filename_new]
            else:
                if not filename_new in session.sbml_filenames:
                    session.sbmls.append(sbml)
                    session.sbml_filenames.append(filename_new)
                else:
                    session.warnings_con.append('A file with the name %s has alre'\
                                                'ady been uploaded. Please rename'\
                                                ' your SBtab file/s before SBML c'\
                                                'reation.' % filename_new)
            redirect(URL(''))
        except:
            session.warnings_con.append('The conversion of SBtab %s to SBML was n'\
                                        'ot successful.' % sbtab.filename)
            redirect(URL(''))

    # convert multiple sbtabs to sbml
    if request.vars.convert_all_button24 or request.vars.convert_all_button31:
        if request.vars.convert_all_button24 != None:
            sbml_version = '24'
            convert_all_button = request.vars.convert_all_button24
        else:
            sbml_version = '31'
            convert_all_button = request.vars.convert_all_button31

        session.warnings_con = []

        # get SBtabs and add them to an SBtab document
        convert_document = session.sbtab_docnames[int(convert_all_button)]
        sbtabs = []
        try:
            for i, filename in enumerate(session.sbtab_filenames):
                if session.name2doc[filename] == convert_document:
                    sbtabs.append(session.sbtabs[i])
            sbtab_doc = SBtab.SBtabDocument(convert_document)
            for sbtab in sbtabs:
                sbtab_doc.add_sbtab(sbtab)
        except:
            session.warnings_con = ['The SBtabs could not be added to SBML.']
            redirect(URL(''))
                
        # convert SBtab document to SBML and add details to session
        try:
            ConvSBtabClass = sbtab2sbml.SBtabDocument(sbtab_doc)
            (sbml,
             session.warnings_con) = ConvSBtabClass.convert_to_sbml(sbml_version)
            filename_new = sbtab_doc.name[:-4] + '.xml'
            # if the sbml build up crashed:
            if not sbml:
                session.warnings_con.append('The SBtab file %s could not be c'\
                                            'onverted to SBML. Please check file'\
                                            'validity.' % sbtab_doc.name)
                redirect(URL(''))
                
            if 'sbmls' not in session:
                session.sbmls = [sbml]
                session.sbml_filenames = [filename_new]
            else:
                if not filename_new in session.sbml_filenames:
                    session.sbmls.append(sbml)
                    session.sbml_filenames.append(filename_new)
                else:
                    session.warnings_con.append('A file with the name %s has alre'\
                                                'ady been uploaded. Please rename'\
                                                ' your SBtab file/s before SBML c'\
                                                'reation.' % filename_new)
                    redirect(URL(''))
        except:
            session.warnings_con.append('The conversion of SBtab %s to SBML was n'\
                                        'ot successful.' % sbtab_doc.filename)
            redirect(URL(''))

    # download sbtab
    if request.vars.dl_sbtab_button:
        downloader_sbtab()

    # download sbtab.xlsx
    if request.vars.dl_xlsx_sbtab_button:
        downloader_sbtab_xlsx()

    # download all sbtabs
    if request.vars.download_all_button:
        download_document = session.sbtab_docnames[int(request.vars.download_all_button)]
        sbtab_list = []
        for i, filename in enumerate(session.sbtab_filenames):
            if session.name2doc[filename] == download_document:
                sbtab_list.append(session.sbtabs[i])
        downloader_sbtab_doc(sbtab_list, int(request.vars.download_all_button))

    # remove all sbtabs
    if request.vars.remove_all_button:
        try:
            remove_document = session.sbtab_docnames[int(request.vars.remove_all_button)]

            # gather indices of entries to remove
            remove_sbtabs = []
            remove_filenames = []
            for i, s in enumerate(session.sbtabs):
                if session.name2doc[s.filename] == remove_document:
                    remove_sbtabs.append(i)

            # delete sbtabs, names, and types
            remove = sorted(remove_sbtabs, reverse=True)
            for i in remove:
                remove_filenames.append(session.sbtab_filenames[i])
                del session.sbtabs[i]
                del session.sbtab_filenames[i]
                del session.types[i]

            # delete document name
            del session.sbtab_docnames[int(request.vars.remove_all_button)]

            # delete name2doc entries
            for entry in remove_filenames:
                del session.name2doc[entry]

            session.warnings_con = []
            redirect(URL(''))
        except:
            redirect(URL(''))

    # erase single SBML
    if request.vars.erase_sbml_button:
        del session.sbmls[int(request.vars.erase_sbml_button)]
        del session.sbml_filenames[int(request.vars.erase_sbml_button)]
        session.warnings_con = []
        redirect(URL(''))

    # convert sbml to sbtab
    if request.vars.c2sbtab_button:
        session.warnings_con = []
        try:
            # initialise variables and parser
            reader = libsbml.SBMLReader()
            sbml_model = reader.readSBMLFromString(session.sbmls[int(request.vars.c2sbtab_button)])
            filename = session.sbml_filenames[int(request.vars.c2sbtab_button)]
            # convert SBML to SBtab Document
            ConvSBMLClass = sbml2sbtab.SBMLDocument(sbml_model.getModel(),filename)
            (sbtab_doc, session.warnings_con) = ConvSBMLClass.convert_to_sbtab()
            if sbtab_doc.sbtabs == []:
                session.warnings_con = ['The SBML file seems to be invalid and could not be converted to SBtab.']
                redirect(URL(''))
            # append generated SBtabs to session variables
            for sbtab in sbtab_doc.sbtabs:
                if 'sbtabs' not in session:
                    session.sbtabs = [sbtab]
                    session.sbtab_filenames = [sbtab.filename]
                    if sbtab_doc.name not in session.sbtab_docnames:
                        session.sbtab_docnames.append(sbtab_doc.name)
                    session.types = [sbtab.table_type]
                    session.name2doc = {}
                    session.name2doc[sbtab.filename] = sbtab_doc.name
                else:
                    if sbtab.filename not in session.sbtab_filenames:
                        session.sbtabs.append(sbtab)
                        session.sbtab_filenames.append(sbtab.filename)
                        session.name2doc[sbtab.filename] = sbtab_doc.name
                        if sbtab_doc.name not in session.sbtab_docnames:
                            session.sbtab_docnames.append(sbtab_doc.name)
                        session.types.append(sbtab.table_type)
        except:
            session.warnings_con = ['The SBML file seems to be invalid and could not be converted to SBtab.']
            redirect(URL(''))

    # erase single SBtab
    if request.vars.erase_sbtab_button:
        del session.sbtabs[int(request.vars.erase_sbtab_button)]
        # this IF is important: you must only delete the document from the list
        # IF there are no more files attached to it
        doc_name = session.name2doc[session.sbtab_filenames[int(request.vars.erase_sbtab_button)]]
        if list(session.name2doc.values()).count(doc_name) == 1:
            session.sbtab_docnames.remove(doc_name)
        del session.name2doc[session.sbtab_filenames[int(request.vars.erase_sbtab_button)]]
        del session.sbtab_filenames[int(request.vars.erase_sbtab_button)]
        del session.types[int(request.vars.erase_sbtab_button)]
        session.warnings_con = []
        redirect(URL(''))

    if request.vars.dl_sbml_button:
        downloader_sbml()
        
    return dict(UPL_FORML=lform, UPL_FORMR=rform, SBTAB_LIST=session.sbtabs,
                SBML_LIST=session.sbmls, NAME_LIST_SBTAB=session.sbtab_filenames,
                NAME_LIST_SBML=session.sbml_filenames,
                DOC_NAMES=session.sbtab_docnames, NAME2DOC=session.name2doc,
                WARNINGS_CON=session.warnings_con, TYPES=session.types)

def def_files():
    '''
    upload your own definition SBtab
    '''
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Upload your own definition files')

    dform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp",
                                  label='Upload new definition file (.csv, .tsv, .xlsx)',
                                  requires=IS_LENGTH(10485760, 1,
                                                     error_message='Max upload size: 10MB')))

    session.warnings_def = []
    if not session.definition_file:
        try:
            sbtab_def = misc.open_definitions_file(os.path.dirname(os.path.abspath(__file__)) + '/../static/files/default_files/definitions.tsv')
            #def_path = os.path.dirname(os.path.abspath(__file__)) + '/../static/files/default_files/definitions.tsv'
            #def_file_open = open(def_path)
            #def_file_open = open('/sbtab/static/files/default_files/definitions.tsv')
            #def_file = def_file_open.read()
            #definition_name = 'definitions.tsv'
            #sbtab_def = SBtab.SBtabTable(def_file, definition_name)
            session.definition_file = sbtab_def
            session.definition_file_def = copy.deepcopy(sbtab_def)
            session.definition_file_name = sbtab_def.filename
            session.definition_file_name_def = copy.deepcopy(sbtab_def.filename)
            session.new_def = False
        except:
            session.warnings_def.append('There was an error reading the definition file.')

    #update session lists 
    if dform.process().accepted:
        response.flash = 'form accepted'
        
        try: sbtab_def_file = request.vars.File.value.decode('utf-8', 'ignore')
        except:
            session.warnings_def.append('The file is not a valid SBtab file.')
            redirect(URL(''))
        filename = request.vars.File.filename
        try: sbtab_def = SBtab.SBtabTable(sbtab_def_file, filename)
        except:
            session.warnings_def.append('The file could not be used as a valid SBtab Table.')
            redirect(URL(''))

        session.definition_file_def = copy.deepcopy(session.definition_file)
        session.definition_file_name_def = copy.deepcopy(session.definition_file_name)
           
        session.definition_file = sbtab_def
        session.definition_file_name = filename        
        session.new_def = True
    elif dform.errors:
        response.flash = 'form has errors'

    #pushed erase button
    if request.vars.erase_def_button:
        # set def file back to default
        session.definition_file = session.definition_file_def
        session.definition_file_name = session.definition_file_name_def
        session.new_def = False
        redirect(URL(''))

    return dict(UPL_FORM=dform, DEF_FILE=session.definition_file,
                DEF_NAME=session.definition_file_name, NEW=session.new_def,
                WARNINGS_DEF=session.warnings_def)

def downloader_sbtab():
        response.headers['Content-Type'] = 'text/csv'
        attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]
        response.headers['Content-Disposition'] = attachment
        sbtab = session.sbtabs[int(request.vars.dl_sbtab_button)]
        content = sbtab.to_str()

        raise HTTP(200,str(content),
                   **{'Content-Type':'text/csv',
                      'Content-Disposition':attachment + ';'})

def downloader_sbtab_xlsx():
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        sbtab = session.sbtabs[int(request.vars.dl_xlsx_sbtab_button)]

        if not session.sbtab_filenames[int(request.vars.dl_xlsx_sbtab_button)].endswith('.xlsx'):
            attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_xlsx_sbtab_button)][:-4]+'.xlsx'
            try:
                content_xlsx = misc.tab_to_xlsx(sbtab)
            except:
                print('The SBtab could not be converted to xlsx.')
                redirect(URL(''))
        else:
            attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_xlsx_sbtab_button)]
            content_xlsx = session.sbtabs[int(request.vars.dl_xlsx_sbtab_button)]
        
        raise HTTP(200, content_xlsx,
                   **{'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      'Content-Disposition':attachment})

    
def downloader_sbtab_doc(sbtab_list, i):

    response.headers['Content-Type'] = 'text/csv'
    if not session.sbtab_docnames[i].endswith('tsv') and \
       not session.sbtab_docnames[i].endswith('csv') and \
       not session.sbtab_docnames[i].endswith('xls'):
        attachment = 'attachment;filename=' + session.sbtab_docnames[i] + '.tsv'
    else:
        attachment = 'attachment;filename=' + session.sbtab_docnames[i]
    response.headers['Content-Disposition'] = attachment
        
    content = ''
    for sbtab in sbtab_list:
        try:
            content += sbtab.to_str() + '\n\n'
        except:
            print('Could not read SBtab %s' % sbtab.filename)

    raise HTTP(200, str(content),
               **{'Content-Type':'application/vnd.ms-excel',
                  'Content-Disposition':attachment + ';'})


def downloader_sbml():
    response.headers['Content-Type'] = 'text/xml'
    if not session.sbml_filenames[int(request.vars.dl_sbml_button)].endswith('.xml') and not session.sbml_filenames[int(request.vars.dl_sbml_button)].endswith('.sbml'):
        attachment = 'attachment;filename=' + session.sbml_filenames[int(request.vars.dl_sbml_button)]+'.xml'
    else: attachment = 'attachment;filename=' + session.sbml_filenames[int(request.vars.dl_sbml_button)]
    response.headers['Content-Disposition'] = attachment
        
    content = session.sbmls[int(request.vars.dl_sbml_button)]
    raise HTTP(200,str(content),
            **{'Content-Type':'text/xml',
               'Content-Disposition':attachment + ';'})

    
def show_sbtab_def():
    '''
    displays a given SBtab definition file in html
    '''
    try: sbtab_def = session.definition_file
    except: return 'There is something wrong with this SBtab file. It cannot be loaded properly. Please reload session (Troubleshooting page).'

    try: return misc.sbtab_to_html(sbtab_def)
    except: return 'There is something wrong with this SBtab file. It cannot be loaded properly.'


def show_sbtab():
    '''
    displays a given SBtab file in html
    '''
    try: sbtab = session.sbtabs[int(request.args(0))]
    except: return 'There is something wrong with this SBtab file. It cannot be loaded properly.'

    try: return misc.sbtab_to_html(sbtab)
    except: return 'There is something wrong with this SBtab file. It cannot be loaded properly.'


def show_sbtab_xls(def_file,def_file_name):
    '''
    displays xls SBtab file
    '''
    xls_sbtab = session.sbtabs[int(request.args(0))]
    file_name = session.sbtab_filenames[int(request.args(0))]
    sbtype    = session.sbtab_types[int(request.args(0))]

    return misc.xls2html(xls_sbtab,file_name,sbtype,def_file,def_file_name)


def show_sbml():
    '''
    displays a given SBML file
    '''
    return misc.xml_to_html(session.sbmls[int(request.args(0))])


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in 
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
