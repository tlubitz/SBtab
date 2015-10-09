# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
import tablib
import tablibIO
import validatorSBtab
import sbml2sbtab
import sbtab2sbml
import libsbml
import random
import string
import splitTabs
import makehtml
import misc
import tablib.packages.xlrd as xlrd
import xlrd

def index():
    session.ex_warning_val  = None
    session.ex_warning_con = None
    redirect(URL('../static/introduction.html'))

def clearsession():
    session.sbtabs = []
    session.sbtab_filenames = []
    session.sbtab_docnames = []
    session.sbtab_types = []
    session.name2doc = {}
    session.todeletename = []
    session.sbtab_fileformat = []    
    session.ex_warning_val = None
    session.ex_warning_con = None

    session.sbmls = []
    session.sbml_filenames = []
    session.sbml_fileformat = []

    session.definition_file = []
    session.definition_file_name = []
    session.new_def = False

    redirect('http://www.sbtab.net')

def validator():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simple replace the two lines below with:
    return auth.wiki()
    """
    #response.flash = T("Welcome to web2py!")
    #session.clear()
    response.title    = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Online Validator')

    if not session.definition_file:
        def_file_open = open('./definitions/definitions.csv','r')    
        session.definition_file      = [def_file_open.read()]
        session.definition_file_name = ['definitions.csv']

    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file (.csv, .xls)'))

    #update session lists
    if lform.process().accepted:
        response.flash = 'form accepted'
        session.ex_warning_val = []
        valid = True
        FileValidClass = validatorSBtab.ValidateFile(request.vars.File.value,request.vars.File.filename)
        while valid:
            #1: Is the file extension valid?
            if not FileValidClass.validateExtension():
                session.ex_warning_val.append('The file format was not supported. Please use .csv or .xls.')
                break

            #2: Can the separator be determined?
            if request.vars.File.filename[-3:] == 'xls':
                try: csv_file  = misc.xls2csv(request.vars.File.value,request.vars.File.filename)
                except:
                    session.ex_warning_val.append('This xls file could not be imported. Please ensure the validity of the xls format.')
                    break
                sbtabber  = misc.removeDoubleQuotes(csv_file)
                separator = ','
            elif not FileValidClass.checkseparator():
                session.ex_warning_val.append('The delimiter of the file could not be determined. Please use comma or tabs as consistent separators.')
                break
            else:
                separator = FileValidClass.checkseparator()
                sbtabber  = misc.removeDoubleQuotes(request.vars.File.value)
                
            #3: If there are more than one SBtab files in the uploaded documents, try to split them
            try: (sbtab_list,types,docs,tnames) = splitTabs.checkTabs([sbtabber],request.vars.File.filename,separator=separator)
            except:
                session.ex_warning_val.append('The SBtab document could not be split into single SBtab tables. Please try uploading them separately.')
                break

            #4: Now save all the required files, names, and variables in the session
            if not session.has_key('sbtabs'):
                session.sbtabs           = []
                session.name2doc         = {}
                session.sbtab_filenames  = []
                session.todeletename     = []
                session.sbtab_fileformat = []
                session.sbtab_docnames   = []
                session.sbtab_types      = []
            for i,sbtab in enumerate(sbtab_list):
                fn = misc.create_filename(request.vars.File.filename,types[i],tnames[i])
                if not fn in session.sbtab_filenames:
                    session.sbtabs.append('\n'.join(sbtab))
                    session.sbtab_filenames.append(fn)
                    session.todeletename.append(fn)
                    session.name2doc[fn] = docs[i]
                    session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                    session.sbtab_docnames.append(docs[i])
                    session.sbtab_types.append(types[i])
                else:
                    warning = 'A file with the name %s has already been uploaded. Please rename your file before upload.'%fn
                    session.ex_warning_val.append(warning)
            break
    elif lform.errors:
        response.flash = 'form has errors'

    #pushed validation button
    if request.vars.validate_button:
        #session.ex_warning_val = None
        valid    = True
        v_output = []
        FileValidClass = validatorSBtab.ValidateFile(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)])
        sbtab2val = session.sbtab_filenames[int(request.vars.validate_button)]
        while valid:
            #1: Can the separator be determined?
            if not FileValidClass.checkseparator():
                session.ex_warning_val = ['The delimiter of the file could not be determined. Please use commas or tabs as consistent separators.']
                break
            else: separator = FileValidClass.checkseparator()
            try: new_tablib_obj = tablibIO.importSetNew(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)],separator=separator)
            except:
                try:
                    add_extension  = session.sbtab_filenames[int(request.vars.validate_button)]+session.sbtab_fileformat[int(request.vars.validate_button)]
                    new_tablib_obj = tablibIO.importSetNew(session.sbtabs[int(request.vars.validate_button)],add_extension)
                except: pass
                session.ex_warning_val = ['The file is corrupted and cannot be validated. A tablib object could not be created.']
                break

            #2: Get definition file
            try:
                if session.definition_file:
                    iss = True
                    TableValidClass = validatorSBtab.ValidateTable(new_tablib_obj,session.sbtab_filenames[int(request.vars.validate_button)],session.definition_file[0],session.definition_file_name[0])
                    for warning in TableValidClass.returnOutput():
                        v_output.append(warning)
                else:
                    iss = False
                    def_file_open = open('./definitions/definitions.csv','r')    
                    session.definition_file      = [def_file_open.read()]
                    session.definition_file_name = ['definitions.csv']
                    TableValidClass = validatorSBtab.ValidateTable(new_tablib_obj,session.sbtab_filenames[int(request.vars.validate_button)],session.definition_file[0],session.definition_file_name[0])
                    for itemx in TableValidClass.returnOutput():
                        v_output.append(itemx)
            except:
                if iss: session.ex_warning_val = ['The file could not be validated, it seems to be broken. Please see example files, the troubleshooting page, or the specification for help.']
                else: session.ex_warning_val = ['The definition file could not be loaded. Please reload session by restarting your browser.']
                break
   
            #session.ex_warning_val = ['The SBtab file is valid.']
            if v_output == [] or v_output == '': v_output = ['The SBtab file is valid.']
            break
    else:
        v_output  = ''
        sbtab2val = ''

    #pushed erase button
    if request.vars.erase_button:
        del session.sbtabs[int(request.vars.erase_button)]
        del session.sbtab_filenames[int(request.vars.erase_button)]
        del session.sbtab_fileformat[int(request.vars.erase_button)]
        del session.sbtab_docnames[int(request.vars.erase_button)]
        del session.sbtab_types[int(request.vars.erase_button)]
        del session.name2doc[session.todeletename[int(request.vars.erase_button)]]
        del session.todeletename[int(request.vars.erase_button)]
        session.ex_warning_val = None
        redirect(URL(''))

    if request.vars.remove_all_button_val:
        try:
            remove_document = session.sbtab_docnames[int(request.vars.remove_all_button_val)]
            remove_sbtabs   = []
            for i,docname in enumerate(session.sbtab_docnames):
                if docname == remove_document:
                    remove_sbtabs.append(i)
            remove = sorted(remove_sbtabs,reverse=True)                    
            for i in remove:
                del session.sbtabs[i]
                del session.sbtab_filenames[i]
                del session.sbtab_fileformat[i]
                del session.sbtab_docnames[i]
                del session.sbtab_types[i]
                del session.name2doc[session.todeletename[i]]
                del session.todeletename[i]
                session.ex_warning_val = None
            redirect(URL(''))
        except:
            redirect(URL(''))
            pass

    return dict(UPL_FORM=lform,DEF_FILE_NAME=session.definition_file_name,SBTAB_LIST=session.sbtabs,NAME_LIST=session.sbtab_filenames,V_OUTPUT=v_output,SBTAB2VAL=sbtab2val,DOC_NAMES=session.sbtab_docnames,NAME2DOC=session.name2doc,EXWARNING=session.ex_warning_val)

def converter():
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('SBML / SBtab Conversion')

    #Form for SBtab files
    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file to convert (.csv, .xls)'))

    #update session lists
    if lform.process(formname='form_one').accepted:
        response.flash = 'form accepted'
        session.ex_warning_con = None
        valid = True
        FileValidClass = validatorSBtab.ValidateFile(request.vars.File.value,request.vars.File.filename)
        while valid:
            #1: Is the file extension valid?
            if not FileValidClass.validateExtension():
                session.ex_warning_con = ['The file format was not supported. Please use .csv or .xls.']
                break

            #2: Can the separator be determined?
            if request.vars.File.filename[-3:] == 'xls':
                try: csv_file  = misc.xls2csv(request.vars.File.value,request.vars.File.filename)
                except:
                    session.ex_warning_con = ['This xls file could not be imported. Please ensure the validity of the xls format.']
                    break
                sbtabber  = misc.removeDoubleQuotes(csv_file)
                separator = ','
            elif not FileValidClass.checkseparator():
                session.ex_warning_con = ['The delimiter of the file could not be determined. Please use comma or tabs as consistent separators.']
                break
            else:
                separator = FileValidClass.checkseparator()
                sbtabber  = misc.removeDoubleQuotes(request.vars.File.value)
                
            #3: If there are more than one SBtab files in the uploaded documents, try to split them
            try: (sbtab_list,types,docs,tnames) = splitTabs.checkTabs([sbtabber],request.vars.File.filename,separator=separator)
            except:
                session.ex_warning_con = ['The SBtab document could not be split into single SBtab tables. Please try uploading them separately.']
                break

            #4: Now save all the required files, names, and variables in the session
            if not session.has_key('sbtabs'):
                session.sbtabs           = []
                session.name2doc         = {}
                session.sbtab_filenames  = []
                session.todeletename     = []
                session.sbtab_fileformat = []
                session.sbtab_docnames   = []
                session.sbtab_types      = []
            for i,sbtab in enumerate(sbtab_list):
                fn = misc.create_filename(request.vars.File.filename,types[i],tnames[i])
                if not fn in session.sbtab_filenames:
                    session.sbtabs.append('\n'.join(sbtab))
                    session.sbtab_filenames.append(fn)
                    session.todeletename.append(fn)
                    session.name2doc[fn] = docs[i]
                    session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                    session.sbtab_docnames.append(docs[i])
                    session.sbtab_types.append(types[i])
                else:
                    warning = 'A file with the name %s has already been uploaded. Please rename your file before upload.'%fn
                    session.ex_warning_con = [warning]
            break
    elif lform.errors:
        response.flash = 'form has errors'

    # convert sbtab2sbml button is pushed
    if request.vars.c2sbml_button:
        session.ex_warning_con = None
        valid = True
        fn = session.sbtab_filenames[int(request.vars.c2sbml_button)]+session.sbtab_fileformat[int(request.vars.c2sbml_button)]
        sbtab_document = sbtab2sbml.SBtabDocument(session.sbtabs[int(request.vars.c2sbml_button)],fn)
        while valid:
            (new_sbml,session.ex_warning_con) = sbtab_document.makeSBML()
            if not new_sbml: break
            if not session.has_key('sbmls'):
                session.sbmls = [new_sbml]
                session.sbml_filenames = [session.sbtab_filenames[int(request.vars.c2sbml_button)]+'_SBML']
            else:
                fn = session.sbtab_filenames[int(request.vars.c2sbml_button)]+'_SBML'
                if not fn in session.sbml_filenames:
                    session.sbmls.append(new_sbml)
                    session.sbml_filenames.append(fn)
                else:
                    warning = 'A file with the name %s has already been uploaded. Please rename your SBtab file/s before SBML creation.'%fn
                    session.ex_warning_con = [warning]
            break
        redirect(URL(''))

    if request.vars.dl_sbtab_button:
        downloader_sbtab()

    if request.vars.dl_xls_sbtab_button:
        downloader_sbtab_xls()

    if request.vars.download_all_button:
        download_document = session.sbtab_docnames[int(request.vars.download_all_button)]
        sbtab_list        = []
        for i,docname in enumerate(session.sbtab_docnames):
            if docname == download_document:
                sbtab_list.append(session.sbtabs[i])
        downloader_sbtab_doc(sbtab_list,int(request.vars.download_all_button))

    if request.vars.convert_all_button:
        session.ex_warning_con = None
        valid = True
        convert_document = session.sbtab_docnames[int(request.vars.convert_all_button)]
        merged_sbtabs    = []
        for i,docname in enumerate(session.sbtab_docnames):
            if docname == convert_document:
                merged_sbtabs.append(session.sbtabs[i])
        sbtab_document = sbtab2sbml.SBtabDocument(merged_sbtabs,'merged_unknown.tsv',tabs=2)
        while valid:
            (new_sbml,session.ex_warning_con) = sbtab_document.makeSBML()
            if not new_sbml: break
            if convert_document == None: convert_document = 'Unnamed_document'
            if not session.has_key('sbmls'):
                session.sbmls = [new_sbml]
                session.sbml_filenames = [convert_document]
            else:
                fn = convert_document
                if not fn in session.sbml_filenames:
                    session.sbmls.append(new_sbml)
                    session.sbml_filenames.append(fn)
                else:
                    warning = 'A file with the name %s has already been uploaded. Please rename your SBtab file/s before SBML creation.'%fn
                    session.ex_warning_con = [warning]
            break
        redirect(URL(''))

    if request.vars.remove_all_button:
        try:
            remove_document = session.sbtab_docnames[int(request.vars.remove_all_button)]
            remove_sbtabs   = []
            for i,docname in enumerate(session.sbtab_docnames):
                if docname == remove_document:
                    remove_sbtabs.append(i)
            remove = sorted(remove_sbtabs,reverse=True)                    
            for i in remove:
                del session.sbtabs[i]
                del session.sbtab_filenames[i]
                del session.sbtab_fileformat[i]
                del session.sbtab_docnames[i]
                del session.sbtab_types[i]
                del session.name2doc[session.todeletename[i]]
                del session.todeletename[i]
                session.ex_warning_con = None
            redirect(URL(''))
        except:
            redirect(URL(''))
            pass

    #Form for SBML files
    rform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBML file to convert (.xml)'))

    if rform.process(formname='form_two').accepted:
        response.flash         = 'form accepted'
        session.ex_warning_con = None
        valid = True
        while valid:
            if request.vars.File.filename[-3:] != 'xml':
                session.ex_warning_con = ['The uploaded file has a different extension than .xml and does not seem to be an SBML file.']
                break
            if not session.has_key('sbmls'):
                session.sbmls = [request.vars.File.value]
                session.sbml_filenames = [request.vars.File.filename]
            else:
                session.sbmls.append(request.vars.File.value)
                fn = request.vars.File.filename
                if not fn in session.sbml_filenames:
                    session.sbml_filenames.append(fn)
                else:
                    random_number = str(random.randint(0,1000))
                    session.sbml_filenames.append(fn+'_'+random_number)
            break
        redirect(URL(''))
    elif rform.errors:
        response.flash = 'form has errors'

    if request.vars.erase_sbml_button:
        del session.sbmls[int(request.vars.erase_sbml_button)]
        del session.sbml_filenames[int(request.vars.erase_sbml_button)]
        session.ex_warning_con = None
        redirect(URL(''))

    # convert sbml2sbtab button is pushed
    if request.vars.c2sbtab_button:
        session.ex_warning_con = None
        try:
            reader     = libsbml.SBMLReader()
            sbml_model = reader.readSBMLFromString(session.sbmls[int(request.vars.c2sbtab_button)])
            filename   = session.sbml_filenames[int(request.vars.c2sbtab_button)]
            if not filename.endswith('.xml'): filename += '.xml'
            ConvSBMLClass                   = sbml2sbtab.SBMLDocument(sbml_model.getModel(),filename)
            (tab_output,session.ex_warning_con) = ConvSBMLClass.makeSBtabs()
            # append generated SBtabs to session variables
            for SBtab in tab_output:
                if SBtab == False: continue
                if not session.has_key('sbtabs'):
                    session.sbtabs = [SBtab[0]]
                    session.sbtab_filenames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]]
                    session.sbtab_fileformat = ['.csv']
                    session.sbtab_docnames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')]
                    session.sbtab_types    = [string.capitalize(SBtab[1])]
                    session.todeletename   = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]]
                    session.name2doc = {}
                    session.name2doc[session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')
                else:
                    fn = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]
                    if not fn in session.sbtab_filenames:
                        session.sbtabs.append(SBtab[0])
                        session.sbtab_filenames.append(fn)
                        session.todeletename.append(fn)
                        session.name2doc[fn] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')      #needs +'_'+SBtab[1]??
                        session.sbtab_fileformat.append('.csv')
                        session.sbtab_docnames.append(session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml'))
                        session.sbtab_types.append(string.capitalize(SBtab[1]))
            #redirect(URL(''))
        except:
            session.ex_warning_con = ['The SBML file seems to be invalid and could not be converted to SBtab. Please validate it on the SBML validator homepage.']

    if request.vars.erase_sbtab_button:
        del session.sbtabs[int(request.vars.erase_sbtab_button)]
        del session.sbtab_filenames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_fileformat[int(request.vars.erase_sbtab_button)]
        del session.sbtab_docnames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_types[int(request.vars.erase_sbtab_button)]
        del session.name2doc[session.todeletename[int(request.vars.erase_sbtab_button)]]
        del session.todeletename[int(request.vars.erase_sbtab_button)]
        session.ex_warning_con = None
        redirect(URL(''))

    if request.vars.dl_sbml_button:
        downloader_sbml()
        
    return dict(UPL_FORML=lform,UPL_FORMR=rform,SBTAB_LIST=session.sbtabs,SBML_LIST=session.sbmls,NAME_LIST_SBTAB=session.sbtab_filenames,NAME_LIST_SBML=session.sbml_filenames,DOC_NAMES=session.sbtab_docnames,NAME2DOC=session.name2doc,EXWARNING=session.ex_warning_con,TYPES=session.sbtab_types)

def def_files():
    '''
    upload your own definition SBtab
    '''
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Upload your own definition files')

    dform   = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload new definition file (.csv, .tsv)'))
    #new_def = False
    
    if not session.definition_file:
        def_file_open = open('./definitions/definitions.csv','r')    
        session.definition_file      = [def_file_open.read()]
        session.definition_file_name = ['definitions.csv']

    #update session lists
    if dform.process().accepted:
        response.flash = 'form accepted'
        session.definition_file      = [request.vars.File.value]
        session.definition_file_name = [request.vars.File.filename]
        session.new_def              = True
    elif dform.errors:
        response.flash = 'form has errors'

    #pushed erase button
    if request.vars.erase_def_button:
        del session.definition_file[int(request.vars.erase_def_button)]
        del session.definition_file_name[int(request.vars.erase_def_button)]
        session.new_def = False
        redirect(URL(''))

    return dict(UPL_FORM=dform,DEF_FILE=session.definition_file,DEF_NAME=session.definition_file_name,NEW=session.new_def)

def troubles():
    '''
    some static troubleshooting
    '''
    redirect(URL('../static/troubles.html'))

def downloader_sbtab():
        response.headers['Content-Type'] = 'text/csv'
        if not session.sbtab_filenames[int(request.vars.dl_sbtab_button)].endswith('.csv') and not session.sbtab_filenames[int(request.vars.dl_sbtab_button)].endswith('.tsv') and not session.sbtab_filenames[int(request.vars.dl_sbtab_button)].endswith('.xls'):
            attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]+'.csv'
        else: attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]
        response.headers['Content-Disposition'] = attachment

        #here we remove the extra tabs/comma from the first row for export
        content_raw = session.sbtabs[int(request.vars.dl_sbtab_button)]
        try:
            #FileValidClass = validatorSBtab.ValidateFile(content_raw,session.sbtab_filenames[int(request.vars.dl_sbtab_button)])
            delimiter = misc.getDelimiter(content_raw) #FileValidClass.checkseparator(content_raw)
        except:
            delimiter = '\t'
        content = misc.first_row(content_raw,delimiter)

        raise HTTP(200,str(content),
                   **{'Content-Type':'text/csv',
                      'Content-Disposition':attachment + ';'})

def downloader_sbtab_xls():
        response.headers['Content-Type'] = 'application/vnd.ms-excel'#'xls'
        if not session.sbtab_filenames[int(request.vars.dl_xls_sbtab_button)].endswith('.xls'):
            attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_xls_sbtab_button)]+'.xls'
            content_raw = session.sbtabs[int(request.vars.dl_xls_sbtab_button)]
            try:
                FileValidClass = validatorSBtab.ValidateFile(content_raw,session.sbtab_filenames[int(request.vars.dl_xls_sbtab_button)])
                delimiter      = FileValidClass.checkseparator(content_raw)
            except:
                delimiter = None
            try:
                content_csv = misc.first_row(content_raw,delimiter)
                content_xls = misc.csv2xls(content_csv,delimiter)
            except:
                attachment  = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_xls_sbtab_button)]+'.xls'
                content_xls = session.sbtabs[int(request.vars.dl_xls_sbtab_button)]
        else:
            attachment  = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_xls_sbtab_button)]
            content_xls = session.sbtabs[int(request.vars.dl_xls_sbtab_button)]
        #response.headers['Content-Disposition'] = attachment

        raise HTTP(200,content_xls,
                   **{'Content-Type':'application/vnd.ms-excel',#'text/xls',
                      'Content-Disposition':attachment + ';'})

def downloader_sbtab_doc(sbtab_list,iter):
        response.headers['Content-Type'] = 'text/csv'
        if not session.sbtab_docnames[iter].endswith('.csv') and not session.sbtab_docnames[iter].endswith('.tsv'):
            attachment = 'attachment;filename=' + session.sbtab_docnames[iter]+'.csv'
        else: attachment = 'attachment;filename=' + session.sbtab_docnames[iter]
        response.headers['Content-Disposition'] = attachment
        
        #here we remove the extra tabs/comma from the first row for export
        #content_raw = sbtab_list
        content = ''
        for sbtab in sbtab_list:
            try:
                FileValidClass = validatorSBtab.ValidateFile(sbtab,session.sbtab_docnames[iter])
                delimiter      = FileValidClass.checkseparator(sbtab)
            except:
                delimiter = None
            content += misc.first_row(sbtab,delimiter)+'\n'

        raise HTTP(200,str(content),
                   **{'Content-Type':'text/csv',
                      'Content-Disposition':attachment + ';'})

def downloader_sbml():
        response.headers['Content-Type'] = 'text/xml'
        if not session.sbml_filenames[int(request.vars.dl_sbml_button)].endswith('.xml'):
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
    def_file      = session.definition_file[int(request.args(0))]
    def_file_name = session.definition_file_name[int(request.args(0))]
    sbtype        = 'Definition'

    try:
        FileValidClass = validatorSBtab.ValidateFile(def_file,def_file_name)
        delimiter      = FileValidClass.checkseparator()
    except: delimiter = None

    if delimiter:
        try: return makehtml.csv2html(def_file,def_file_name,delimiter,sbtype,def_file,def_file_name)
        except: return 'There is something wrong with this SBtab file. It cannot be displayed.'
    else:
        try: return show_sbtab_xls(def_file,def_file_name)
        except: return 'There is something wrong with this SBtab file. It cannot be displayed.'

def show_sbtab():
    '''
    displays a given SBtab file in html
    '''
    sbtab_file = session.sbtabs[int(request.args(0))]
    file_name  = session.sbtab_filenames[int(request.args(0))]
    sbtype     = session.sbtab_types[int(request.args(0))]

    try:
        FileValidClass = validatorSBtab.ValidateFile(sbtab_file,file_name)
        delimiter      = FileValidClass.checkseparator()
    except:
        delimiter = None
        
    try:
        def_file      = session.definition_file[0]
        def_file_name = session.definition_file_name[0]
    except:
        def_file_open = open('./definitions/definitions.csv','r')    
        def_file      = def_file_open.read()
        def_file_name = 'definitions.csv'

    if delimiter:
        try: return makehtml.csv2html(sbtab_file,file_name,delimiter,sbtype,def_file,def_file_name)
        except: return 'There is something wrong with this SBtab file. It cannot be displayed.'
    else:
        try: return show_sbtab_xls(def_file,def_file_name)
        except: return 'There is something wrong with this SBtab file. It cannot be displayed.'


def show_sbtab_xls(def_file,def_file_name):
    '''
    displays xls SBtab file
    '''
    xls_sbtab = session.sbtabs[int(request.args(0))]
    file_name = session.sbtab_filenames[int(request.args(0))]
    sbtype    = session.sbtab_types[int(request.args(0))]

    return makehtml.xls2html(xls_sbtab,file_name,sbtype,def_file,def_file_name)


def show_sbml():
    '''
    displays a given SBML file
    '''
    return makehtml.xml2html(session.sbmls[int(request.args(0))])

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
