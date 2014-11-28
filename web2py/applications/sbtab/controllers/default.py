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
import splitTabs
import makehtml
import tablib.packages.xlrd as xlrd
import xlrd

def index():
    session.ex_warning = None
    redirect(URL('../../static/introduction.html'))

def clearsession():
    session.sbtabs = []
    session.sbtab_filenames = []
    session.sbtab_docnames = []
    session.sbtab_types = []
    session.name2doc = {}
    session.todeletename = []
    session.sbtab_fileformat = []    
    session.ex_warning = ''

    session.sbmls = []
    session.sbml_filenames = []
    session.sbml_fileformat = []

    session.definition_file = []
    session.definition_file_name = []

    redirect(URL('../../sbtab/static/introduction.html'))

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

    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file (.csv, .xls)'))

    #update session lists
    if lform.process().accepted:
        response.flash = 'form accepted'
        session.ex_warning = None
        try:
            FileValidClass = validatorSBtab.ValidateFile(request.vars.File.value,request.vars.File.filename)
            seperator      = FileValidClass.checkSeperator(request.vars.File.value)
            (sbtab_list,types,docs) = splitTabs.checkTabs([request.vars.File.value],request.vars.File.filename,seperator=seperator)
            if not session.has_key('sbtabs'):
                session.sbtabs = ['\n'.join(sbtab_list[0])]
                session.sbtab_filenames = [request.vars.File.filename[:-4]+'_'+types[0]]
                session.sbtab_fileformat = [request.vars.File.filename[-4:]]
                session.sbtab_docnames  = [docs[0]]
                session.sbtab_types     = [types[0]]
                session.todeletename    = [request.vars.File.filename[:-4]+'_'+types[0]]
                session.name2doc = {}
                session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]] = docs[0]
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list[1:]):
                        session.sbtabs.append('\n'.join(sbtab))
                        fn = request.vars.File.filename[:-4]+'_'+types[i]
                        if not fn in session.sbtab_filenames:
                            session.sbtab_filenames.append(fn)
                            session.todeletename.append(fn)
                            session.name2doc[fn] = docs[i]
                        else:
                            random_number = str(random.randint(0,1000))
                            session.sbtab_filenames.append(fn+'_'+random_number)
                            session.todeletename.append(fn+'_'+random_number)
                            session.name2doc[fn+'_'+random_number] = docs[i]
                        session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
            else:
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list):
                        session.sbtabs.append('\n'.join(sbtab))
                        fn = request.vars.File.filename[:-4]+'_'+types[i]
                        if not fn in session.sbtab_filenames:
                            session.sbtab_filenames.append(fn)
                            session.todeletename.append(fn)
                            session.name2doc[fn] = docs[i]
                        else:
                            random_number = str(random.randint(0,1000))
                            session.sbtab_filenames.append(fn+'_'+random_number)
                            session.todeletename.append(fn+'_'+random_number)
                            session.name2doc[fn+'_'+random_number] = docs[i]
                        session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
                else:
                    session.sbtabs.append('\n'.join(sbtab_list[0]))
                    fn = request.vars.File.filename[:-4]+'_'+types[0]
                    if not fn in session.sbtab_filenames:
                        session.sbtab_filenames.append(fn)
                        session.todeletename.append(fn)
                        session.name2doc[fn] = docs[0]
                    else:
                        random_number = str(random.randint(0,1000))
                        session.sbtab_filenames.append(fn+'_'+random_number)
                        session.todeletename.append(fn+'_'+random_number)
                        session.name2doc[fn+'_'+random_number] = docs[0]
                    session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                    session.sbtab_docnames.append(docs[0])
                    session.sbtab_types.append(types[0])


                #redirect(URL(''))
        except:
            session.ex_warning = 'The file that you uploaded is no valid SBtab file. Please only use .csv or .xls format. If it still does not work out, please consult the SBtab specification.'
    elif lform.errors:
        response.flash = 'form has errors'

    #pushed validation button
    if request.vars.validate_button:
        try:
            FileValidClass = validatorSBtab.ValidateFile(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)])
            v_output       = FileValidClass.returnOutput()
            try: seperator      = FileValidClass.checkSeperator(session.sbtabs[int(request.vars.validate_button)])
            except: pass
            if seperator: new_tablib_obj = tablibIO.importSetNew(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)],seperator=seperator)
            else:
                xx_filename = session.sbtab_filenames[int(request.vars.validate_button)]+session.sbtab_fileformat[int(request.vars.validate_button)]
                new_tablib_obj = tablibIO.importSetNew(session.sbtabs[int(request.vars.validate_button)],xx_filename)

            if new_tablib_obj:
                if session.definition_file:
                    TableValidClass = validatorSBtab.ValidateTable(new_tablib_obj,session.sbtab_filenames[int(request.vars.validate_button)],session.definition_file[0],session.definition_file_name[0])
                    for itemx in TableValidClass.returnOutput():
                        v_output.append(itemx)
                else:
                    TableValidClass = validatorSBtab.ValidateTable(new_tablib_obj,session.sbtab_filenames[int(request.vars.validate_button)])
                    for itemx in TableValidClass.returnOutput():
                        v_output.append(itemx)
            sbtab2val  = session.sbtab_filenames[int(request.vars.validate_button)]
            #redirect(URL(''))
            session.ex_warning = None
        except:
            session.ex_warning = 'Your file is corrupt. Even too corrupt to be validated. Please remove it and see the SBtab specification to try and create a better SBtab file.'
            v_output  = ''
            sbtab2val = ''
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
        session.ex_warning = None
        redirect(URL(''))

    return dict(UPL_FORM=lform,SBTAB_LIST=session.sbtabs,NAME_LIST=session.sbtab_filenames,V_OUTPUT=v_output,SBTAB2VAL=sbtab2val,DOC_NAMES=session.sbtab_docnames,NAME2DOC=session.name2doc,EXWARNING=session.ex_warning)

def converter():
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('SBML / SBtab Conversion')

    #Form for SBtab files
    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file to convert (.csv, .xls)'))

    #update session lists
    if lform.process(formname='form_one').accepted:
            response.flash = 'form accepted'
            try:
                FileValidClass = validatorSBtab.ValidateFile(request.vars.File.value,request.vars.File.filename)
                seperator      = FileValidClass.checkSeperator(request.vars.File.value)            
                (sbtab_list,types,docs) = splitTabs.checkTabs([request.vars.File.value],request.vars.File.filename,seperator=seperator)
                if not session.has_key('sbtabs'):
                    session.sbtabs = ['\n'.join(sbtab_list[0])]
                    session.sbtab_filenames = [request.vars.File.filename[:-4]+'_'+types[0]]
                    session.sbtab_fileformat = [request.vars.File.filename[-4:]]
                    session.sbtab_docnames  = [docs[0]]
                    session.sbtab_types     = [types[0]]
                    session.todeletename    = [request.vars.File.filename[:-4]+'_'+types[0]]
                    session.name2doc = {}
                    session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]] = docs[0]
                    if len(sbtab_list) > 1:
                        for i,sbtab in enumerate(sbtab_list[1:]):
                            session.sbtabs.append('\n'.join(sbtab))
                            fn = request.vars.File.filename[:-4]+'_'+types[i]
                            if not fn in session.sbtab_filenames:
                                session.sbtab_filenames.append(fn)
                                session.todeletename.append(fn)
                                session.name2doc[fn] = docs[i]
                            else:
                                random_number = str(random.randint(0,1000))
                                session.sbtab_filenames.append(fn+'_'+random_number)
                                session.todeletename.append(fn+'_'+random_number)
                                session.name2doc[fn+'_'+random_number] = docs[i]
                            session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                            session.sbtab_docnames.append(docs[i])
                            session.sbtab_types.append(types[i])
                else:
                    if len(sbtab_list) > 1:
                        for i,sbtab in enumerate(sbtab_list):
                            session.sbtabs.append('\n'.join(sbtab))
                            fn = request.vars.File.filename[:-4]+'_'+types[i]
                            if not fn in session.sbtab_filenames:
                                session.sbtab_filenames.append(fn)
                                session.todeletename.append(fn)
                                session.name2doc[fn] = docs[i]
                            else:
                                random_number = str(random.randint(0,1000))
                                session.sbtab_filenames.append(fn+'_'+random_number)
                                session.todeletename.append(fn+'_'+random_number)
                                session.name2doc[fn+'_'+random_number] = docs[i]
                            session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                            session.sbtab_docnames.append(docs[i])
                            session.sbtab_types.append(types[i])
                    else:
                        session.sbtabs.append('\n'.join(sbtab_list[0]))
                        fn = request.vars.File.filename[:-4]+'_'+types[0]
                        if not fn in session.sbtab_filenames:
                            session.sbtab_filenames.append(fn)
                            session.todeletename.append(fn)
                            session.name2doc[fn] = docs[0]
                        else:
                            random_number = str(random.randint(0,1000))
                            session.sbtab_filenames.append(fn+'_'+random_number)
                            session.todeletename.append(fn+'_'+random_number)
                            session.name2doc[fn+'_'+random_number] = docs[0]
                        session.sbtab_fileformat.append(request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[0])
                        session.sbtab_types.append(types[0])
            except:
                session.ex_warning = 'The file that you uploaded is no SBtab file. Please only use .csv or .xls format. If it still does not work out, please consult the SBtab specification.'
    elif lform.errors:
        response.flash = 'form has errors'

    # convert sbtab2sbml button is pushed
    if request.vars.c2sbml_button:
        try:
            fn = session.sbtab_filenames[int(request.vars.c2sbml_button)]+session.sbtab_fileformat[int(request.vars.c2sbml_button)]
            sbtab_document = sbtab2sbml.SBtabDocument(session.sbtabs[int(request.vars.c2sbml_button)],fn)
            new_sbml       = sbtab_document.makeSBML()
            if not session.has_key('sbmls'):
                session.sbmls = [new_sbml]
                session.sbml_filenames = [session.sbtab_filenames[int(request.vars.c2sbml_button)]+'_SBML']
            else:
                session.sbmls.append(new_sbml)
                fn = session.sbtab_filenames[int(request.vars.c2sbml_button)]+'_SBML'
                if not fn in session.sbml_filenames:
                    session.sbml_filenames.append(fn)
                else:
                    random_number = str(random.randint(0,1000))
                    session.sbml_filenames.append(fn+'_'+random_number)
        except:
            session.ex_warning = 'The SBtab file could not be converted to SBML. Please check whether you have a valid Reaction SBtab file.'

    if request.vars.dl_sbtab_button:
        downloader_sbtab()

    if request.vars.convert_all_button:
        try:
            convert_document = session.sbtab_docnames[int(request.vars.convert_all_button)]
            merged_sbtabs    = []
            for i,docname in enumerate(session.sbtab_docnames):
                if docname == convert_document:
                    merged_sbtabs.append(session.sbtabs[i])
            sbtab_document = sbtab2sbml.SBtabDocument(merged_sbtabs,'merged_unknown.tsv',tabs=2)
            new_sbml       = sbtab_document.makeSBML()
            if not session.has_key('sbmls'):
                session.sbmls = [new_sbml]
                session.sbml_filenames = [convert_document]
            else:
                session.sbmls.append(new_sbml)
                fn = convert_document
                if not fn in session.sbml_filenames:
                    session.sbml_filenames.append(fn)
                else:
                    random_number = str(random.randint(0,1000))
                    session.sbml_filenames.append(fn+'_'+random_number)
        except:
            session.ex_warning = 'The SBtab file could not be converted to SBML. Please check whether you have a valid Reaction SBtab file.'

    #Form for SBML files
    rform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBML file to convert (.xml)'))

    if rform.process(formname='form_two').accepted:
        response.flash = 'form accepted'
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
    elif rform.errors:
        response.flash = 'form has errors'

    if request.vars.erase_sbml_button:
        del session.sbmls[int(request.vars.erase_sbml_button)]
        del session.sbml_filenames[int(request.vars.erase_sbml_button)]
        session.ex_warning = None
        redirect(URL(''))

    # convert sbml2sbtab button is pushed
    if request.vars.c2sbtab_button:
        try:
            reader     = libsbml.SBMLReader()
            sbml_model = reader.readSBMLFromString(session.sbmls[int(request.vars.c2sbtab_button)])
            ConvSBMLClass = sbml2sbtab.SBMLDocument(sbml_model.getModel(),session.sbml_filenames[int(request.vars.c2sbtab_button)])
            tab_output    = ConvSBMLClass.makeSBtabs()
            # append generated SBtabs to session variables
            for SBtab in tab_output:
                if not session.has_key('sbtabs'):
                    session.sbtabs = [SBtab[0]]
                    session.sbtab_filenames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]]
                    session.sbtab_fileformat = ['.csv']
                    session.sbtab_docnames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')]
                    session.sbtab_types    = [SBtab[1]]
                    session.todeletename   = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]]
                    session.name2doc = {}
                    session.name2doc[session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')
                else:
                    session.sbtabs.append(SBtab[0])
                    fn = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]
                    if not fn in session.sbtab_filenames:
                        session.sbtab_filenames.append(fn)
                        session.todeletename.append(fn)
                        session.name2doc[fn] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')      #needs +'_'+SBtab[1]??
                    else:
                        random_number = str(random.randint(0,1000))
                        session.sbtab_filenames.append(fn+'_'+random_number)
                        session.todeletename.append(fn+'_'+random_number)
                        session.name2doc[fn+'_'+random_number] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')      #needs +'_'+SBtab[1]??
                    session.sbtab_fileformat.append('.csv')
                    session.sbtab_docnames.append(session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml'))
                    session.sbtab_types.append(SBtab[1])
        except:
            session.ex_warning = 'The SBML file could not be converted to SBtab. Please check whether your SBML file is valid.'

    if request.vars.erase_sbtab_button:
        del session.sbtabs[int(request.vars.erase_sbtab_button)]
        del session.sbtab_filenames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_fileformat[int(request.vars.erase_sbtab_button)]
        del session.sbtab_docnames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_types[int(request.vars.erase_sbtab_button)]
        del session.name2doc[session.todeletename[int(request.vars.erase_sbtab_button)]]
        del session.todeletename[int(request.vars.erase_sbtab_button)]
        session.ex_warning = None
        redirect(URL(''))

    if request.vars.dl_sbml_button:
        downloader_sbml()
        
    return dict(UPL_FORML=lform,UPL_FORMR=rform,SBTAB_LIST=session.sbtabs,SBML_LIST=session.sbmls,NAME_LIST_SBTAB=session.sbtab_filenames,NAME_LIST_SBML=session.sbml_filenames,DOC_NAMES=session.sbtab_docnames,NAME2DOC=session.name2doc,EXWARNING=session.ex_warning,TYPES=session.sbtab_types)


def def_files():
    '''
    upload your own definition SBtab
    '''
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Upload your own definition files')

    dform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload definition file (.csv, .tsv)'))

    #update session lists
    if dform.process().accepted:
        response.flash = 'form accepted'
        session.definition_file      = [request.vars.File.value]
        session.definition_file_name = [request.vars.File.filename]
    elif dform.errors:
        response.flash = 'form has errors'

    #pushed erase button
    if request.vars.erase_def_button:
        del session.definition_file[int(request.vars.erase_def_button)]
        del session.definition_file_name[int(request.vars.erase_def_button)]
        redirect(URL(''))

    return dict(UPL_FORM=dform,DEF_FILE=session.definition_file,DEF_NAME=session.definition_file_name)

def downloader_sbtab():
        response.headers['Content-Type'] = 'text/csv'
        if not session.sbtab_filenames[int(request.vars.dl_sbtab_button)].endswith('.csv') and not session.sbtab_filenames[int(request.vars.dl_sbtab_button)].endswith('.tsv'):
            attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]+'.csv'
        else: attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]
        response.headers['Content-Disposition'] = attachment
        
        content = session.sbtabs[int(request.vars.dl_sbtab_button)]
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

def show_sbtab():
    '''
    displays a given SBtab file in html
    '''
    sbtab_file = session.sbtabs[int(request.args(0))]
    file_name  = session.sbtab_filenames[int(request.args(0))]
    sbtype     = session.sbtab_types[int(request.args(0))]

    try:
        FileValidClass = validatorSBtab.ValidateFile(sbtab_file,file_name)
        delimiter      = FileValidClass.checkSeperator(sbtab_file)
    except:
        delimiter = None
        
    try:
        def_file      = session.definition_file
        def_file_name = session.definition_file_name
    except:
        def_file      = None
        def_file_name = None

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