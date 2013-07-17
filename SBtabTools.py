import tablib
import copy
import SBtab
import os.path
import tablibIO


def oneOrMany(spreadsheet_file):
    '''
    Check for multiple tables and cut them into different tablib object.
    Return list of tablib object.

    Parameters
    ----------
    spreadsheet_file : tablib object
        Tablib object of the whole table.

    Returns
    -------
    sbtabs : list
        List of single tablib objects.
    '''
    sbtabs = []

    # copy file, one for iteration, one for cutting
    sbtab_document = copy.deepcopy(spreadsheet_file)
    # create new tablib object
    sbtab = tablib.Dataset()

    # cutting sbtab_document, write tablib objects in list
    if len(spreadsheet_file) != 0:  # if file not empty
        for row in spreadsheet_file:
            if len(sbtab) == 0:  # if first line, append line w/o checking
                sbtab.rpush(sbtab_document.lpop())
            else:
                for i, entry in enumerate(row):
                    # if header row (!!), write to new tablib object and store the last one
                    if entry.startswith('!!'):
                        sbtabs.append(sbtab)
                        sbtab = tablib.Dataset()
                        sbtab.rpush(sbtab_document.lpop())
                        break
                    # if not header row, append line to tablib object
                    if len(row) == i + 1:
                        sbtab.rpush(sbtab_document.lpop())
        sbtabs.append(sbtab)

    # return list of tablib objects
    return sbtabs


def WCM_Export(modules_list):
    """
    Write all WCM modules in SBtab format.
    Create 4 SBtab dictionaries, species, compartments, parameters, solver.

    Parameters
    ----------
    modules_list : list
        list of WCM modules

    Returns
    -------
    sbtab_species : SBtab object
        SBtab containing species information.
    sbtab_compartments : SBtab object
        SBtab containing compartment information
    sbtab_parameters : SBtab object
        SBtab containing parameters
    sbtab_solver : SBtab object
        SBtab containig solver information

    Notes
    -----
    WCM module:
        - name
        - timescale
        - species
        - dt
        - c_factor
        - t_factor
        - modeldict
            - name
            - vars
            - initvars
            - pars
            - initpars
            - odes
            - sp_annotations
            - sp_compartment
            - com_annotations
    """
    # Set extension
    extension = 'xls'

    # Name of the table
    name = 'WCM'

    # -----------------------------Species----------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Species' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Species')
    columns.append('!Species')
    columns.append('!Annotation')
    columns.append('!ModuleName')
    columns.append('!InitialValue')
    columns.append('!Compartment')
    columns.append('!ODE')

    # Set value rows
    value_rows = []
    number = 0
    for WCM_module in modules_list:
        for i, species in enumerate(WCM_module.species):
            tag = 'WCM_sp_' + str(i + 1 + number)
            annotation = WCM_module.modeldict['sp_annotations'][species]
            if WCM_module.name:
                m_name = WCM_module.name
            else:
                m_name = WCM_module.modeldict['name']
            initval = WCM_module.modeldict['initvars'][species]
            compartment = WCM_module.modeldict['sp_compartment'][species]
            ode = WCM_module.modeldict['odes'][species]
            value_rows.append([tag, species, annotation, m_name, initval, compartment, ode])
        number = i + 1 + number

    # Create SBtab
    tablename = name + '_sp.' + extension
    sbtab_species = createDataset(header, columns, value_rows, tablename)

    # -----------------------------Compartment--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Compartment' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Compartment')
    columns.append('!Compartment')
    columns.append('!Annotation')
    columns.append('!ModuleName')

    # Set value rows
    value_rows = []
    number = 0
    for WCM_module in modules_list:
        for i, compartment in enumerate(WCM_module.modeldict['com_annotations'].keys()):
            tag = 'WCM_com_' + str(i + 1 + number)
            annotation = WCM_module.modeldict['com_annotations'][compartment]
            if WCM_module.name:
                m_name = WCM_module.name
            else:
                m_name = WCM_module.modeldict['name']
            value_rows.append([tag, compartment, annotation, m_name])
        number = i + 1 + number

    # Create SBtab
    tablename = name + '_com.' + extension
    sbtab_compartments = createDataset(header, columns, value_rows, tablename)

    # -----------------------------Parameter--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Parameter' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Parameter')
    columns.append('!Parameter')
    columns.append('!InitialValue')
    columns.append('!ModuleName')

    # Set value rows
    value_rows = []
    number = 0
    for WCM_module in modules_list:
        for i, parameter in enumerate(WCM_module.modeldict['initpars'].keys()):
            tag = 'WCM_par_' + str(i + 1 + number)
            initval = WCM_module.modeldict['initpars'][parameter]
            if WCM_module.name:
                m_name = WCM_module.name
            else:
                m_name = WCM_module.modeldict['name']
            value_rows.append([tag, parameter, initval, m_name])
        number = i + 1 + number

    # Create SBtab
    tablename = name + '_par.' + extension
    sbtab_parameters = createDataset(header, columns, value_rows, tablename)

    # -----------------------------SolverInfo--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-SolverInfo' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-SolverInfo')
    columns.append('!ModuleName')
    columns.append('!Timescale')
    columns.append('!dt')
    columns.append('!c_factor')
    columns.append('!t_factor')
    # Set value rows
    value_rows = []
    for i, WCM_module in enumerate(modules_list):
        tag = 'Info_' + str(i + 1)
        if WCM_module.name:
            m_name = WCM_module.name
        else:
                m_name = WCM_module.modeldict['name']
        timescale = WCM_module.timescale
        dt = WCM_module.dt
        c_fac = WCM_module.c_factor
        t_fac = WCM_module.t_factor
        value_rows.append([tag, m_name, timescale, dt, c_fac, t_fac])

    # Create SBtab
    tablename = name + '_solv.' + extension
    sbtab_solver = createDataset(header, columns, value_rows, tablename)

    folder = './sbtab/'
    filename = folder + name

    sbtab_species.writeSBtab(extension, filename + '_sp')
    sbtab_compartments.writeSBtab(extension, filename + '_com')
    sbtab_parameters.writeSBtab(extension, filename + '_par')
    sbtab_solver.writeSBtab(extension, filename + '_solv')

    return sbtab_species, sbtab_compartments, sbtab_parameters, sbtab_solver


def WCM_module(WCM_module):
    """
    Write WCM module in SBtab format.
    Create 4 SBtab dictionaries, species, compartments, parameters, solver.

    Parameters
    ----------
    WCM_dict : dict
        WCM_dict, dict of dicts.

    Returns
    -------
    sbtab_species : SBtab object
        SBtab containing species information.
    sbtab_compartments : SBtab object
        SBtab containing compartment information
    sbtab_parameters : SBtab object
        SBtab containing parameters
    sbtab_solver : SBtab object
        SBtab containig solver information

    Notes
    -----
    WCM module:
        - name
        - timescale
        - species
        - dt
        - c_factor
        - t_factor
        - modeldict
            - name
            - vars
            - initvars
            - pars
            - initpars
            - odes
            - sp_annotations
            - sp_compartment
            - com_annotations
    """
    if WCM_module.name:
        name = WCM_module.name
    else:
        name = WCM_module.modeldict['name']

    # Set extension
    extension = 'xls'

    # -----------------------------Species----------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Species' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Species')
    columns.append('!Species')
    columns.append('!Annotation')
    columns.append('!InitialValue')
    columns.append('!Compartment')
    columns.append('!ODE')

    # Set value rows
    value_rows = []
    for i, species in enumerate(WCM_module.species):
        tag = 'WCM_sp_' + str(i + 1)
        annotation = WCM_module.modeldict['sp_annotations'][species]
        initval = WCM_module.modeldict['initvars'][species]
        compartment = WCM_module.modeldict['sp_compartment'][species]
        ode = WCM_module.modeldict['odes'][species]
        value_rows.append([tag, species, annotation, initval, compartment, ode])

    # Create SBtab
    tablename = name + '_sp.' + extension
    sbtab_species = createDataset(header, columns, value_rows, tablename)

    # -----------------------------Compartment--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Compartment' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Compartment')
    columns.append('!Compartment')
    columns.append('!Annotation')

    # Set value rows
    value_rows = []
    for i, compartment in enumerate(WCM_module.modeldict['com_annotations'].keys()):
        tag = 'WCM_com_' + str(i + 1)
        annotation = WCM_module.modeldict['com_annotations'][compartment]
        value_rows.append([tag, compartment, annotation])

    # Create SBtab
    tablename = name + '_com.' + extension
    sbtab_compartments = createDataset(header, columns, value_rows, tablename)

    # -----------------------------Parameter--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-Parameter' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-Parameter')
    columns.append('!Parameter')
    columns.append('!InitialValue')

    # Set value rows
    value_rows = []
    for i, parameter in enumerate(WCM_module.modeldict['initpars'].keys()):
        tag = 'WCM_par_' + str(i + 1)
        initval = WCM_module.modeldict['initpars'][parameter]
        value_rows.append([tag, parameter, initval])

    # Create SBtab
    tablename = name + '_par.' + extension
    sbtab_parameters = createDataset(header, columns, value_rows, tablename)

    # -----------------------------SolverInfo--------------------------------------
    # Set header
    header = "!!SBtab TableType='WCM-SolverInfo' Document='WCM' Table='" + name + "'"

    # Set main columns
    columns = []
    columns.append('!WCM-SolverInfo')
    columns.append('!Timescale')
    columns.append('!dt')
    columns.append('!c_factor')
    columns.append('!t_factor')
    # Set value rows
    value_rows = []
    timescale = WCM_module.timescale
    dt = WCM_module.dt
    c_fac = WCM_module.c_factor
    t_fac = WCM_module.t_factor
    value_rows.append(['Info_1', timescale, dt, c_fac, t_fac])

    # Create SBtab
    tablename = name + '_solv.' + extension
    sbtab_solver = createDataset(header, columns, value_rows, tablename)

    folder = './sbtab/'
    filename = folder + name
    sbtab_species.writeSBtab(extension, filename + '_sp')
    sbtab_compartments.writeSBtab(extension, filename + '_com')
    sbtab_parameters.writeSBtab(extension, filename + '_par')
    sbtab_solver.writeSBtab(extension, filename + '_solv')

    return sbtab_species, sbtab_compartments, sbtab_parameters, sbtab_solver


def WCM_timecourse(timecourses, trange):
    """
    Create a SBtab object of the time course in the WCM.

    Parameters
    ----------
    timecourses : dict
        Dictionary of the timecourses
    trange : list
        Time points for plot

    Returns
    -------
    sbtab_timecourse : SBtab object
        SBtab containing time courses
    """
    name = "WCM"
    extension = "xls"
    # Set header
    header = "!!SBtab TableType='WCM-Timecourses' Document='WCM' Table='" + name + "'"
    # Set main columns
    columns = []
    columns.append('!WCM-Timecourses')
    columns.append('!Species')
    columns.append('!Compartments')
    trange = [str(x) for x in trange]
    columns = columns + trange
    # Set value rows
    value_rows = []
    number = 0
    for species in timecourses.keys():
        for i, compartment in enumerate(timecourses[species].keys()):
            tag = 'WCM_tc' + str(i + 1 + number)
            value = [str(x) for x in timecourses[species][compartment]]
            value_rows.append([tag, species, compartment] + value)
            print value_rows
        number = i + 1 + number
    # Create SBtab
    filename = name + '_tc.' + extension
    sbtab_timecourse = createDataset(header, columns, value_rows, filename)

    folder = './sbtab/'
    filename = folder + name + '_tc'

    sbtab_timecourse.writeSBtab(extension, filename)

    return sbtab_timecourse


def WCM_module_timecourses(WCM_module):
    """
    Create a SBtab object of the time course in the WCM module.

    Parameters
    ----------
    timecourses : dict
        Dictionary of the timecourses
    trange : list
        Time points for plot

    Returns
    -------
    sbtab_timecourse : SBtab object
        SBtab containing time courses
    """
    extension = "xls"
    if WCM_module.name:
        name = WCM_module.name
    else:
        name = WCM_module.modeldict['name']
    # Set header
    header = "!!SBtab TableType='WCM-Timecourses' Document='WCM' Table='" + name + "'"
    # Set main columns
    columns = []
    columns.append('!WCM-Timecourses')
    columns.append('!Species')
    columns.append('!Compartments')
    trange = [str(x) for x in WCM_module.trange]
    columns = columns + trange
    # Set value rows
    value_rows = []
    for i, species in enumerate(WCM_module.species):
        tag = 'WCM_tc' + str(i + 1)
        value = WCM_module.timecourses[species]
        value_rows.append([tag, species] + value)

    # Create SBtab
    filename = name + '_tc.' + extension
    sbtab_timecourse = createDataset(header, columns, value_rows, filename)

    folder = './sbtab/'
    filename = folder + name + '_tc'
    sbtab_timecourse.writeSBtab(extension, filename)

    return sbtab_timecourse


def WCM_initialValueTable(WCM_instance):
    """
    Create initial value table.
    If SBtab file doesn't exist, create it with initial values from WCM.
    If it exists but does not contain all species, add new ones to table.

    Parameters
    ----------
    WCM_modules : list
        List of WCM module

    Returns
    -------
    sbtab_state_vec : SBtab object
    """
    extension = 'xls'
    folder = './sbtab/'
    filename = folder + 'WCM-initialValue'
    filepath = filename + '.' + extension
    if not os.path.isfile(filepath):
        # Name of the table
        name = 'WCM'

        # -----------------------------Species----------------------------------------
        # Set header
        header = "!!SBtab TableType='WCM-InitialValue' Document='WCM' Table='" + name + "'"

        # Set main columns
        columns = []
        columns.append('!WCM-InitialValue')
        columns.append('!Species')
        columns.append('!Compartment')
        columns.append('!InitialValue')
        columns.append('!Source')

        # Set value rows
        value_rows = []
        number = 0
        for species in WCM_instance.v.keys():
            for i, compartment in enumerate(WCM_instance.v[species].keys()):
                tag = 'WCM_sp' + str(i + 1 + number)
                value = [str(WCM_instance.v[species][compartment])]
                new_row = [tag, species, compartment] + value + ['WCM']
                value_rows.append(new_row)
            number = i + 1 + number

        # Create SBtab
        tablename = name + '_initialValue.' + extension
        sbtab_state_vec = createDataset(header, columns, value_rows, tablename)
        sbtab_state_vec.writeSBtab(extension, filename)
        return sbtab_state_vec
    else:
        pass
        table = tablibIO.importSet(filepath)
        sbtab = SBtab.SBtabTable(table, filepath)
        table_dict = sbtab.createDict()
        for species in WCM_instance.v.keys():
            for compartment in WCM_instance.v[species].keys():
                if not species in table_dict['!Species'].values():
                    sbtab.addRow(['WCM_sp' + str(len(sbtab.value_rows) + 1), species, compartment, WCM_instance.v[species][compartment], 'WCM'])
                elif not compartment in table_dict['!Compartment'].values():
                    sbtab.addRow(['WCM_sp' + str(len(sbtab.value_rows) + 1), species, compartment, WCM_instance.v[species][compartment], 'WCM'])
                elif species in table_dict['!Species'].values():
                    is_in = False
                    for sp in table_dict['!Species']:
                        if table_dict['!Species'][sp] == species and table_dict['!Compartment'][sp] == compartment:
                            is_in = True
                    if not is_in:
                        sbtab.addRow(['WCM_sp' + str(len(sbtab.value_rows) + 1), species, compartment, WCM_instance.v[species][compartment], 'WCM'])
        sbtab.update()
        sbtab_state_vec = sbtab
        sbtab_state_vec.writeSBtab(extension, filename)
        return sbtab_state_vec


def createDataset(header_row, columns, value_rows, filename):
    """
    Create a tablib object of the SBtab Python object.

    Parameters
    ----------

    Returns
    -------
    sbtab_dataset : tablib object
        Tablib dataset of the SBtab Python object.

    """
    # Initialise variables
    sbtab_temp = []
    sbtab_dataset = tablib.Dataset()
    header = header_row.split(' ')

    # Delete spaces in header, main column and data rows
    header = [x.strip(' ') for x in header]
    columns = [x.strip(' ') for x in columns]
    for row in value_rows:
        try:
            for entry in row:
                entry = entry.strip(' ')
        except:
            continue

    # Add header, main column and data rows to temporary list object
    sbtab_temp.append(header)
    sbtab_temp.append(columns)
    for row in value_rows:
        sbtab_temp.append(row)

    # Delete all empty entries at the end of the rows
    for row in sbtab_temp:
        if len(row) > 1:
            while not row[-1]:
                del row[-1]

    # Make all rows the same length
    longest = max([len(x) for x in sbtab_temp])
    for row in sbtab_temp:
        if len(row) < longest:
            for i in range(longest - len(row)):
                row.append('')
            sbtab_dataset.append(row)
        else:
            sbtab_dataset.append(row)

    # Save as tablib header as additional information
    sbtab_dataset.header = header

    sbtab = SBtab.SBtabTable(sbtab_dataset, filename)
    return sbtab
