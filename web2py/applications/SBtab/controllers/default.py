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
import splitTabs
import tablib.packages.xlrd as xlrd

def index():
    session.ex_warning = None
    if not session.has_key('name2doc'):
        session.name2doc = {}
    redirect(URL('../../static/introduction.html'))

def clearsession():
    session.sbtabs = []
    session.sbtab_filenames = []
    session.sbtab_docnames = []
    session.sbtab_types = []
    session.name2doc = {}

    session.ex_warning = ''
    session.definition_file= []
    session.definition_file_name = []

    session.sbmls = []
    session.sbml_filenames = []

    redirect(URL('../../default/converter'))

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

    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file (.tsv, .csv, .xls)'))

    #update session lists
    if lform.process().accepted:
        response.flash = 'form accepted'
        session.ex_warning = None
        try:
            (sbtab_list,types,docs) = splitTabs.checkTabs([request.vars.File.value],request.vars.File.filename)
            if not session.has_key('sbtabs'):
                session.sbtabs = ['\n'.join(sbtab_list[0])]
                session.sbtab_filenames = [request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]]
                session.sbtab_docnames  = [docs[0]]
                session.sbtab_types     = [types[0]]
                session.todeletename    = [request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:]]
                session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]] = docs[0]
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list[1:]):
                        session.sbtabs.append('\n'.join(sbtab))
                        session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
                        session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.name2doc[request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:]] = docs[i]
            else:
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list):
                        session.sbtabs.append('\n'.join(sbtab))
                        session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
                        session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.name2doc[request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:]] = docs[i]
                else:
                    session.sbtabs.append('\n'.join(sbtab_list[0]))
                    session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:])
                    session.sbtab_docnames.append(docs[0])
                    session.sbtab_types.append(types[0])
                    session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                    session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]] = docs[0]
            #redirect(URL(''))
        except:
            session.ex_warning = 'The file that you uploaded is no SBtab file. Please only use .tsv, .csv, or .xls format. If it still does not work out, please consult the SBtab specification.'
    elif lform.errors:
        response.flash = 'form has errors'

    #pushed validation button
    if request.vars.validate_button:
        try:
            FileValidClass = validatorSBtab.ValidateFile(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)])
            v_output       = FileValidClass.returnOutput()        
            new_tablib_obj = tablibIO.importSetNew(session.sbtabs[int(request.vars.validate_button)],session.sbtab_filenames[int(request.vars.validate_button)])

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
    lform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload SBtab file to convert (.tsv, .csv, .xls)'))

    #update session lists
    if lform.process(formname='form_one').accepted:
            response.flash = 'form accepted'
            #try:
            (sbtab_list,types,docs) = splitTabs.checkTabs([request.vars.File.value],request.vars.File.filename)
            if not session.has_key('sbtabs'):
                session.sbtabs = ['\n'.join(sbtab_list[0])]
                session.sbtab_filenames = [request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]]
                session.sbtab_docnames  = [docs[0]]
                session.sbtab_types     = [types[0]]
                session.todeletename    = [request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]]
                session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]] = docs[0]
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list[1:]):
                        session.sbtabs.append('\n'.join(sbtab))
                        session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
                        session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:])
                        session.name2doc[request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:]] = docs[i]
            else:
                if len(sbtab_list) > 1:
                    for i,sbtab in enumerate(sbtab_list):
                        session.sbtabs.append('\n'.join(sbtab))
                        session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:])
                        session.sbtab_docnames.append(docs[i])
                        session.sbtab_types.append(types[i])
                        session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:])
                        session.name2doc[request.vars.File.filename[:-4]+'_'+types[i]+request.vars.File.filename[-4:]] = docs[i]
                else:
                    session.sbtabs.append('\n'.join(sbtab_list[0]))
                    session.sbtab_filenames.append(request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:])
                    session.sbtab_docnames.append(docs[0])
                    session.sbtab_types.append(types[0])
                    session.todeletename.append(request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:])
                    session.name2doc[request.vars.File.filename[:-4]+'_'+types[0]+request.vars.File.filename[-4:]] = docs[0]
        #except:
        #    session.ex_warning = 'The file that you uploaded is no SBtab file. Please only use .tsv, .csv, or .xls format. If it still does not work out, please consult the SBtab specification.'
    elif lform.errors:
        response.flash = 'form has errors'

    # convert sbtab2sbml button is pushed
    if request.vars.c2sbml_button:
        #try:
            sbtab_document = sbtab2sbml.SBtabDocument(session.sbtabs[int(request.vars.c2sbml_button)],session.sbtab_filenames[int(request.vars.c2sbml_button)])
            new_sbml       = sbtab_document.makeSBML()
            if not session.has_key('sbmls'):
                session.sbmls = [new_sbml]
                session.sbml_filenames = [session.sbtab_filenames[int(request.vars.c2sbml_button)].rstrip('.tcsvxl')+'_SBML.xml']
            else:
                session.sbmls.append(new_sbml)
                session.sbml_filenames.append(session.sbtab_filenames[int(request.vars.c2sbml_button)].rstrip('.tcxlsv')+'_SBML.xml')
        #except:
        #    session.ex_warning = 'The SBtab file could not be converted to SBML. Please check whether you have a valid Reaction SBtab file.'

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
                session.sbml_filenames = [convert_document+'.xml']
            else:
                session.sbmls.append(new_sbml)
                session.sbml_filenames.append(convert_document+'.xml')
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
            session.sbml_filenames.append(request.vars.File.filename)
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
                    session.sbtab_filenames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv']
                    session.sbtab_docnames = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')]
                    session.sbtab_types    = [SBtab[1]]
                    session.todeletename   = [session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv']
                    session.name2doc[session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv'] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')
                else:
                    session.sbtabs.append(SBtab[0])
                    session.sbtab_filenames.append(session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv')
                    session.sbtab_docnames.append(session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml'))
                    session.sbtab_types.append(SBtab[1])
                    session.todeletename.append(session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv')
                    session.name2doc[session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')+'_'+SBtab[1]+'_SBtab.tsv'] = session.sbml_filenames[int(request.vars.c2sbtab_button)].rstrip('.xml')
            #redirect(URL(''))
        except:
            session.ex_warning = 'The SBML file could not be converted to SBtab. Please check whether your SBML file is valid.'

    if request.vars.dl_sbml_button:
        downloader_sbml()
        
    if request.vars.erase_sbtab_button:
        del session.sbtabs[int(request.vars.erase_sbtab_button)]
        del session.sbtab_filenames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_docnames[int(request.vars.erase_sbtab_button)]
        del session.sbtab_types[int(request.vars.erase_sbtab_button)]
        del session.name2doc[session.todeletename[int(request.vars.erase_sbtab_button)]]
        del session.todeletename[int(request.vars.erase_sbtab_button)]

        session.ex_warning = None
        redirect(URL(''))

    return dict(UPL_FORML=lform,UPL_FORMR=rform,SBTAB_LIST=session.sbtabs,SBML_LIST=session.sbmls,NAME_LIST_SBTAB=session.sbtab_filenames,NAME_LIST_SBML=session.sbml_filenames,DOC_NAMES=session.sbtab_docnames,NAME2DOC=session.name2doc,EXWARNING=session.ex_warning,TYPES=session.sbtab_types)


def def_files():
    '''
    upload your own definition SBtab
    '''
    response.title = T('SBtab - Standardised data tables for Systems Biology')
    response.subtitle = T('Upload your own definition files')

    dform = SQLFORM.factory(Field('File', 'upload',uploadfolder="/tmp", label='Upload definition file (.tsv, .csv)'))

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
        attachment = 'attachment;filename=' + session.sbtab_filenames[int(request.vars.dl_sbtab_button)]
        response.headers['Content-Disposition'] = attachment
        
        content = session.sbtabs[int(request.vars.dl_sbtab_button)]
        raise HTTP(200,str(content),
                   **{'Content-Type':'text/csv',
                      'Content-Disposition':attachment + ';'})

def downloader_sbml():
        response.headers['Content-Type'] = 'text/xml'
        attachment = 'attachment;filename=' + session.sbml_filenames[int(request.vars.dl_sbml_button)]
        response.headers['Content-Disposition'] = attachment
        
        content = session.sbmls[int(request.vars.dl_sbml_button)]
        raise HTTP(200,str(content),
                   **{'Content-Type':'text/xml',
                      'Content-Disposition':attachment + ';'})

def show_sbtab_xls():
    '''
    displays xls SBtab file
    '''
    file_name = session.sbtab_filenames[int(request.args(0))]
    xls_sbtab = session.sbtabs[int(request.args(0))]

    nice_sbtab = '<p><h2><b>'+file_name+'</b></h2></p>'

    dbook = tablib.Databook()
    xl = xlrd.open_workbook(file_contents=xls_sbtab)

    for sheetname in xl.sheet_names():
        dset = tablib.Dataset()
        dset.title = sheetname
        sheet = xl.sheet_by_name(sheetname)
        for row in range(sheet.nrows):
            if row == 0:
                new_row = ''
                for thing in sheet.row_values(row):
                    if not thing == '': new_row += thing
                nice_sbtab += '<a style="background-color:#A4A4A4">'+new_row+'</a><br>'
                nice_sbtab += '<table>'
            elif row == 1:
                new_row = ''
                for thing in sheet.row_values(row):
                    if not thing == '': new_row += '<td>'+thing+'</td>'
                nice_sbtab += '<tr bgcolor="#BDBDBD">'+new_row+'</tr>'
            else:
                new_row = ''
                for thing in sheet.row_values(row):
                    new_row += '<td>'+thing+'</td>'
                nice_sbtab += '<tr>'+new_row+'</tr>'
                    
    return nice_sbtab 


def show_sbtab():
    '''
    displays a given SBtab file
    '''
    file_name = session.sbtab_filenames[int(request.args(0))]
    if file_name.endswith('.tsv') or file_name.endswith('.csv'):
        delimiter = '\t'
    else: return show_sbtab_xls()
    
    ugly_sbtab = session.sbtabs[int(request.args(0))].split('\n')
    nice_sbtab = '<p><h2><b>'+session.sbtab_filenames[int(request.args(0))]+'</b></h2></p>'

    nice_sbtab += '<a style="background-color:#A4A4A4">'+ugly_sbtab[0]+'</a><br>'

    nice_sbtab += '<table>'
    for row in ugly_sbtab[1:]:
        if row.startswith('!'): nice_sbtab += '<tr bgcolor="#BDBDBD">'
        else: nice_sbtab += '<tr>'
        for thing in row.split(delimiter):
            new_row = '<td>'+thing+'</\td>'
            nice_sbtab += new_row
        nice_sbtab += '</tr>'
    nice_sbtab += '</table>'
    
    return nice_sbtab

def show_sbml():
    '''
    displays a given SBML file
    '''
    new_sbml = '<xmp>'
    old_sbml = session.sbmls[int(request.args(0))].split('\n')

    for row in old_sbml:
        new_sbml += row +'\n'

    new_sbml += '</xmp>'
        
    return new_sbml


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
