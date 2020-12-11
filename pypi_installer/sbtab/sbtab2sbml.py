"""
SBtab2SBML Converter
====================

A converter for SBtab Documents to SBML.

See specification for further details.
"""
#!/usr/bin/env python
import re
import libsbml
import string
import sys

# all allowed secondary SBtab table types
sbtab_types = ['Event', 'Rule']
urns = ['obo.chebi', 'kegg.compound', 'kegg.reaction', 'obo.go', 'obo.sgd',
        'biomodels.sbo', 'ec-code', 'kegg.orthology', 'uniprot', 'hmdb',
        'metanetx.chemical', 'metanetx.reaction', 'ncbigi', 'rhea',
        'seed.compound', 'unipathway.compound', 'unipathway.reaction',
        'umbbd.compound', 'asap', 'ecogene', 'ncbigene', 'ncbigi',
        'bigg.reaction']

class ConversionError(Exception):
    '''
    Base class for errors in the SBtab conversion class.
    '''
    def __init__(self,message):
        self.message = message
        
    def __str__(self):
        return self.message

class SBtabDocument:
    '''
    SBtab document to be converted to SBML model
    '''
    def __init__(self, sbtab_doc):
        '''
        Initalizes SBtab document, checks it for SBtab count.
        If there are more than 1 SBtab file to be converted, provide a "tabs" parameter higher than 1.

        Parameters
        ----------
        sbtab : SBtab Document object
           SBtab Document Class.
        '''
        self.sbtab_doc = sbtab_doc
        if len(self.sbtab_doc.sbtabs) == 0:
            raise ConversionError('The given SBtab Object cannot be converted. It is empty.')
        self.filename = sbtab_doc.name
        self.warnings = []
        self.model_ids = []
        self.parameters_local = []
        self.parameters_global = []
        self.gene_products = []
        self.unit_definitions = []
        self.unit_mM = False
        self.fbc = False
        self.layout = False

    def convert_to_sbml(self, sbml_version):
        '''
        Generates the SBML file using the provided SBtab file/s.

        Parameters
        ----------
        sbtab : SBtab Document object
           SBtab Document Class.

        Returns: list
           The first element of the list is the SBML file in string representation.
           The second element of the list is a list of warnings in string representation.
        '''
        # initialize SBML document
        if 'FbcObjective' in self.sbtab_doc.type_to_sbtab.keys() or 'Gene' in self.sbtab_doc.type_to_sbtab.keys():
            if sbml_version == '24':
                sbmlns = libsbml.SBMLNamespaces(2,4)
                self.new_document = libsbml.SBMLDocument(sbmlns)
                self.warnings.append('The FBC package is only supported by SBML Level 3 and higher.')
            else:
                sbmlns = libsbml.SBMLNamespaces(3,1,'fbc',2)
                self.new_document = libsbml.SBMLDocument(sbmlns)
                self.new_document.setPackageRequired("fbc", False)
                self.fbc = True
        elif 'Layout' in self.sbtab_doc.type_to_sbtab.keys():
            if sbml_version == '24':
                sbmlns = libsbml.SBMLNamespaces(2,4)
                self.new_document = libsbml.SBMLDocument(sbmlns)
                self.warnings.append('The Layout package is only supported by SBML Level 3 and higher.')
            else:
                sbmlns = libsbml.SBMLNamespaces(3,1,'layout',1)
                self.new_document = libsbml.SBMLDocument(sbmlns)
                self.new_document.setPackageRequired("fbc", True)
                self.layout = True
        else:
            if sbml_version == '24':
                sbmlns = libsbml.SBMLNamespaces(2,4)
                self.new_document = libsbml.SBMLDocument(sbmlns)
            else:
                sbmlns = libsbml.SBMLNamespaces(3,1)
                self.new_document = libsbml.SBMLDocument(sbmlns)

        # initialize new model
        self.new_model = self.new_document.createModel()
        self.new_model.setId(self.sbtab_doc.name)
        self.new_model.setName(self.sbtab_doc.name)
        #self.new_document.setModel(self.new_model)
        
        if self.fbc:
            mplugin = self.new_model.getPlugin('fbc')
            mplugin.setStrict(True)
            self.fbc_objectives_list = []
            self.fbc_genes_list = []
        
        # initialize some required variables for conversion
        self.reaction_list = []
        self.species_list = []
        self.compartment_list = []
        self.modifier_list = []
        self.id2sbmlid = {}

        # 1. build compartment
        try:
            compartment = self.check_compartments()
            if not compartment:
                self.warnings.append('No compartment could be initialised for'\
                                     'the model. Please check provided'\
                                     'compartment information.')
                return (False, self.warnings)
        except:
            self.warnings.append('Error: The compartment initialisation crash'\
                                 'ed. Please check for valid compartment info'\
                                 'rmation.')
            return (False, self.warnings)

        # 2. build compounds
        #try:
        if 'Compound' in self.sbtab_doc.type_to_sbtab.keys():
            self.compound_sbtab()
        #except:
        #    self.warnings.append('Warning: The provided compounds could not b'\
        #                         'e initialised properly. Please check for va'\
        #                         'lid compound information.')

        # 2b. build quantities/parameters
        try:
            if 'Quantity' in self.sbtab_doc.type_to_sbtab.keys():
                self.quantity_sbtab()
        except:
            self.warnings.append('Warning: The provided quantities could not b'\
                                 'e initialised properly. Please check for va'\
                                 'lid quantity information.') 
        
        # 2c. build FBC gene products
        try:
            if 'Gene' in self.sbtab_doc.type_to_sbtab.keys():
                self.gene_sbtab()
        except:
            self.warnings.append('Warning: The provided genes could not b'\
                                 'e initialised properly. Please check for va'\
                                 'lid gene information.') 
            
        # 3. build reactions
        try:
            if 'Reaction' in self.sbtab_doc.type_to_sbtab.keys():
                self.reaction_sbtab()
        except:
            self.warnings.append('Error: The provided reaction information co'\
                                 'uld not be converted. Please check for vali'\
                                 'd reaction information.')

        # 4. check for secondary SBtab table types
        for table_type in sbtab_types:
            if table_type in self.sbtab_doc.type_to_sbtab.keys():
                try:
                    name = 'self.' + table_type.lower() + '_sbtab()'
                    eval(name)
                except:
                    self.warnings.append('Warnings: Could not process informat'\
                                         'ion from SBtab %s.' % table_type)

        # 5. check for fbc plugin content
        if self.fbc:
            try:
                self.fbc_objective_sbtab()
            except:
                self.warnings.append('Error: The provided fbc objective information co'\
                                     'uld not be converted. Please check for vali'\
                                     'd fbc objective information.')

        # 6. check for layout plugin content
        if self.layout:
            #try:
            self.layout_sbtab()
            #except:
            #    self.warnings.append('Error: The provided layout information co'\
            #                         'uld not be converted. Please check for vali'\
            #                         'd layout information.')
                    
                    
        # write generated information to SBML model
        new_sbml_model = libsbml.writeSBMLToString(self.new_document)
        
        return (new_sbml_model, self.warnings)

    def return_warnings(self):
        '''
        return warnings from the SBML conversion.
        '''
        return self.warnings
    
    def check_compartments(self):
        '''
        compartment build up is neccessary and tricky:
        either we have a compartment SBtab, or if not, we have to check a
        possible reaction and/or compound SBtab for compartments; if all of
        these do not work, we need one default compartment
        '''
        def_comp_set = False
        #1. check for compartment SBtab
        if 'Compartment' in self.sbtab_doc.type_to_sbtab.keys():
            try:
                self.compartment_sbtab()
                return True
            except:
                self.warnings.append('There was a compartment SBtab but it '\
                                     'could not be used for SBML compartment '\
                                     'initialisation.')

        # 2. if there was no compartment SBtab given, check whether it is given
        # in the other SBtabs; if we find a compartment, we return True since
        # the compartment will be built upon SBtab Compound procession
        if 'Compound' in self.sbtab_doc.type_to_sbtab.keys():
            sbtab_compounds = self.sbtab_doc.type_to_sbtab['Compound']
            for sbtab_compound in sbtab_compounds:
                if '!Location' in sbtab_compound.columns:
                    for row in sbtab_compound.value_rows:
                        if row[sbtab_compound.columns_dict['!Location']] != '':
                            return True

        #3. if there was no compartment SBtab given and no Location found in
        # compound SBtab, check whether it is given
        # in the other SBtabs; if we find a compartment, we return True since
        # the compartment will be built upon SBtab Reaction procession
        if 'Reaction' in self.sbtab_doc.type_to_sbtab.keys():
            sbtab_reactions = self.sbtab_doc.type_to_sbtab['Reaction']
            for sbtab_reaction in sbtab_reactions:
                if '!Location' in sbtab_reaction.columns:
                    for row in sbtab_reaction.value_rows:
                        if row[sbtab_reaction.columns_dict['!Location']] != '':
                            return True

        #4. Nothing yet? Then create a default compartment
        self.def_comp_set = True
        default_compartment = self.new_model.createCompartment()
        default_compartment.setId('Default_Compartment')
        default_compartment.setName('Default_Compartment')
        default_compartment.setSize(True)
        default_compartment.setConstant(True)
        self.compartment_list.append('Default_Compartment')
        self.model_ids.append(default_compartment.getId())

        return True

    def set_annotation(self, element, annotation, urn, elementtype):
        '''
        Set an annotation for a given SBML element.

        Parameters
        ----------
        element : libsbml object
           Element that needs to be annotated.
        annotation : str
           The identifier part of the annotation string.
        urn : str
           URN that links to the external web resource.
        elementtype : str
           What kind of element needs to be annotated? Model or Biological?
        '''
        element.setMetaId(element.getId() + "_meta")
        cv_term = libsbml.CVTerm()

        if elementtype == 'Model':
            cv_term.setQualifierType(1)
            cv_term.setModelQualifierType(libsbml.BQB_IS)
        else:
            cv_term.setQualifierType(1)
            cv_term.setBiologicalQualifierType(libsbml.BQB_IS)

        resource_term = "http://identifiers.org/" + urn + '/' + annotation
        cv_term.addResource(resource_term)

        return cv_term

    def check_id(self, sbtab):
        '''
        IDs have to be handled with care in SBML;
        this function preprocesses the ID field of SBtab to circumvent problems
        in SBML
        '''
        #invalid = [' ','-','_',',','.','+']
        invalid = [' ','-',',','.','+']
        sbml_column = False
        
        for i, column in enumerate(sbtab.columns):
            if column.startswith('!SBML:') and column.endswith('id'):
                sbml_column = i
       
        for row in sbtab.value_rows:
            for iv in invalid:
                if iv in row[sbtab.columns_dict['!ID']]:
                    raise ConversionError('There is an invalid character (%s) in the ID of row %s.'\
                                          'Please remove in order to proceed.' % (iv,row))
                if sbml_column != False:
                    if iv in row[i]:
                        raise ConversionError('There is an invalid character (%s) in the ID of row %s.'\
                                              'Please remove in order to proceed.' % (iv,row))

    def compartment_sbtab(self):
        '''
        extract information from the Compartment SBtab
        '''
        sbtab_compartments = self.sbtab_doc.type_to_sbtab['Compartment']

        # build compartments
        for sbtab_compartment in sbtab_compartments:
            self.check_id(sbtab_compartment)
            for row in sbtab_compartment.value_rows:
                # name and id of compartment (optional SBML id)
                if row[sbtab_compartment.columns_dict['!ID']] not in self.compartment_list:
                    compartment = self.new_model.createCompartment()
                    if '!SBML:compartment:id' in sbtab_compartment.columns and \
                       row[sbtab_compartment.columns_dict['!SBML:compartment:id']] != '':
                        compartment.setId(str(row[sbtab_compartment.columns_dict['!SBML:compartment:id']]))
                    else:
                        compartment.setId(str(row[sbtab_compartment.columns_dict['!ID']]))
                    if '!Name' in sbtab_compartment.columns and \
                       row[sbtab_compartment.columns_dict['!Name']] != '':
                        compartment.setName(str(row[sbtab_compartment.columns_dict['!Name']]))
                    else:
                        compartment.setName(str(row[sbtab_compartment.columns_dict['!ID']]))
                self.compartment_list.append(row[sbtab_compartment.columns_dict['!ID']])
                self.model_ids.append(compartment.getId())
                
                # set the compartment size and SBOterm if given
                if '!Size' in sbtab_compartment.columns and \
                   row[sbtab_compartment.columns_dict['!Size']] != '':
                    try: compartment.setSize(float(row[sbtab_compartment.columns_dict['!Size']]))
                    except: pass

                if '!SBOTerm' in sbtab_compartment.columns and \
                   row[sbtab_compartment.columns_dict['!SBOTerm']] != '':
                    try: compartment.setSBOTerm(int(row[sbtab_compartment.columns_dict['!SBOTerm']][4:]))
                    except: pass

                if '!IsConstant' in sbtab_compartment.columns and \
                       row[sbtab_compartment.columns_dict['!IsConstant']] != '':
                        if row[sbtab_compartment.columns_dict['!IsConstant']].lower() == 'false':
                            try:
                                compartment.setConstant(False)
                            except: pass
                        else:
                            try:
                                compartment.setConstant(True)
                            except: pass
                else:
                    compartment.setConstant(True)

                # search for identifiers and annotations
                for column in sbtab_compartment.columns_dict.keys():
                    if "Identifiers" in column:
                        annot = row[sbtab_compartment.columns_dict[column]]
                        if annot == '': continue
                        for pattern in urns:
                            if pattern in column:
                                urn = pattern
                        try:
                            cv_term = self.set_annotation(compartment, annot,
                                                          urn, 'Model')
                            compartment.addCVTerm(cv_term)
                        except:
                            self.warnings.append('The annotation %s could not be a'\
                                                 'ssigned properly to %s.' % (annot, compartment.getId()))

    def fbc_objective_sbtab(self):
        '''
        extract information from the FBC Objective SBtab and writes it to the model
        '''
        sbtab_fbc_objectives = self.sbtab_doc.type_to_sbtab['FbcObjective']

        # build compounds
        for sbtab_fbc_objective in sbtab_fbc_objectives:
            self.check_id(sbtab_fbc_objective)
            mplugin = self.new_model.getPlugin('fbc')
            for row in sbtab_fbc_objective.value_rows:
                if row[sbtab_fbc_objective.columns_dict['!ID']] not in self.fbc_objectives_list:
                    objective = mplugin.createObjective()
                    objective.setId(row[sbtab_fbc_objective.columns_dict['!ID']])
                    try: objective.setName(row[sbtab_fbc_objective.columns_dict['!Name']])
                    except: pass
                    try: objective.setType(row[sbtab_fbc_objective.columns_dict['!SBML:fbc:type']])
                    except: pass
                    try:
                        if row[sbtab_fbc_objective.columns_dict['!SBML:fbc:active']].capitalize() == 'True':
                            mplugin.setActiveObjectiveId(row[sbtab_fbc_objective.columns_dict['!ID']])
                    except: pass
                    try:
                        if '+' in row[sbtab_fbc_objective.columns_dict['!SBML:fbc:objective']]:
                            pairs = row[sbtab_fbc_objective.columns_dict['!SBML:fbc:objective']].split('+')
                            for pair in pairs:
                                singles = pair.split('*')
                                flux_objective = objective.createFluxObjective()
                                flux_objective.setCoefficient(float(singles[0].strip()))
                                flux_objective.setReaction(singles[1].strip())
                        else:
                            singles = row[sbtab_fbc_objective.columns_dict['!SBML:fbc:objective']].split('*')
                            flux_objective = objective.createFluxObjective()
                            flux_objective.setCoefficient(float(singles[0].strip()))
                            flux_objective.setReaction(singles[1].strip())

                    except: pass
                    self.fbc_objectives_list.append(row[sbtab_fbc_objective.columns_dict['!ID']])

    def layout_sbtab(self):
        '''
        extract information from the Layout SBtab and writes it to the model
        '''
        
        reaction_rows = {}
        sbtab_layouts = self.sbtab_doc.type_to_sbtab['Layout']
        layoutns = libsbml.LayoutPkgNamespaces(3, 1, 1)

        mplugin = self.new_model.getPlugin('layout')
        layout = mplugin.createLayout()
        
        # build layout
        for sbtab_layout in sbtab_layouts:
            for i, row in enumerate(sbtab_layout.value_rows):
                row_id = 'identifier_%s' % str(i)
                                
                # Create Layout Canvas
                if row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'LayoutCanvas':
                    try:
                        layout.setId(row[sbtab_layout.columns_dict['!ID']])
                        layout.setDimensions(libsbml.Dimensions(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:width']]), float(row[sbtab_layout.columns_dict['!SBML:layout:height']])))
                    except:
                        self.warnings.append('Warning: Could not create the Layout Canvas.')

                # Create Compartment Glyphs
                if row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'Compartment':
                    try:
                        compartment_glyph = layout.createCompartmentGlyph()
                        compartment_glyph.setId(row[sbtab_layout.columns_dict['!ID']])
                        compartment_glyph.setCompartmentId(row[sbtab_layout.columns_dict['!SBML:layout:compartment:id']])

                        compartment_glyph.setBoundingBox(libsbml.BoundingBox(layoutns, row_id,
                                                                             float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                                             float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]),
                                                                             float(row[sbtab_layout.columns_dict['!SBML:layout:width']]),
                                                                             float(row[sbtab_layout.columns_dict['!SBML:layout:height']])))
                    except:
                        self.warnings.append('Warning: Could not create the Compartment Layout.')
                        
                # Create Species Glyphs
                if row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'Species':
                    try:
                        species_glyph = layout.createSpeciesGlyph()
                        species_glyph.setId(row[sbtab_layout.columns_dict['!ID']])
                        species_glyph.setSpeciesId(row[sbtab_layout.columns_dict['!SBML:layout:species:id']])
                        species_glyph.setBoundingBox(libsbml.BoundingBox(layoutns, row_id,
                                                                         float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                                         float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]),
                                                                         float(row[sbtab_layout.columns_dict['!SBML:layout:width']]),
                                                                         float(row[sbtab_layout.columns_dict['!SBML:layout:height']])))
                    except:
                        self.warnings.append('Warning: Could not create the Species Layout.')
                        
                # Create Text Glyphs
                if row[sbtab_layout.columns_dict['!SBML:modelEntity']] == 'SpeciesText':
                    try:
                        text_glyph = layout.createTextGlyph()
                        text_glyph.setId(row[sbtab_layout.columns_dict['!ID']])
                        text_glyph.setBoundingBox(libsbml.BoundingBox(layoutns, row_id,
                                                                      float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                                      float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]),
                                                                      float(row[sbtab_layout.columns_dict['!SBML:layout:width']]),
                                                                      float(row[sbtab_layout.columns_dict['!SBML:layout:height']])))
                        text_glyph.setOriginOfTextId(row[sbtab_layout.columns_dict['!SBML:layout:text']])
                        text_glyph.setGraphicalObjectId(row[sbtab_layout.columns_dict['!SBML:layout:species:id']])
                    except:
                        self.warnings.append('Warning: Could not create the Species Text Layout.')


                # Collect rows for Reaction Curves
                if row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'ReactionCurve' or row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'SpeciesReferenceCurve':
                    reaction_id = row[sbtab_layout.columns_dict['!SBML:layout:reaction:id']]
                    if reaction_id in reaction_rows.keys():
                        rows = reaction_rows[reaction_id]
                        rows.append(row)
                        reaction_rows[reaction_id] = rows
                    else: reaction_rows[reaction_id] = [row]

                    
        # Now all layout is written except for the reactions; these have to be assembled over several rows
        # Every dict entry is for one reaction

        for entry in reaction_rows:
            rows = reaction_rows[entry]
            # information for the single reaction:
            try:
                reaction_glyph = layout.createReactionGlyph()
                reaction_glyph.setId(rows[0][sbtab_layout.columns_dict['!ID']])
                reaction_glyph.setReactionId(rows[0][sbtab_layout.columns_dict['!SBML:layout:reaction:id']])
                reaction_curve = reaction_glyph.getCurve()
                ls = reaction_curve.createLineSegment()
            except:
                self.warnings.append('Reaction Layout for %s could not be initialised' % rows[0][sbtab_layout.columns_dict['!ID']])
                continue
            
            sr_glyph2curve = {}
            for row in rows:
                try:
                    if row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'ReactionCurve':
                        if row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'Start':
                            ls.setStart(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                      float(row[sbtab_layout.columns_dict['!SBML:layout:Y']])))
                        elif row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'End':
                            ls.setEnd(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                    float(row[sbtab_layout.columns_dict['!SBML:layout:Y']])))
                    elif row[sbtab_layout.columns_dict['!SBML:layout:modelEntity']] == 'SpeciesReferenceCurve':
                        if row[sbtab_layout.columns_dict['!ID']] not in sr_glyph2curve.keys():
                            species_reference_glyph = reaction_glyph.createSpeciesReferenceGlyph()
                            species_reference_glyph.setId(row[sbtab_layout.columns_dict['!ID']])
                            species_reference_glyph.setSpeciesGlyphId(row[sbtab_layout.columns_dict['!SBML:layout:species:id']])
                            species_reference_curve = species_reference_glyph.getCurve()
                            cb = species_reference_curve.createCubicBezier()
                            sr_glyph2curve[species_reference_glyph.getId()] = cb
                        else:
                            cb = sr_glyph2curve[row[sbtab_layout.columns_dict['!ID']]]
                        if row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'Start':
                            cb.setStart(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                              float(float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]))))
                        elif row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'End':
                            cb.setEnd(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                            float(float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]))))
                        elif row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'BasePoint1':
                            cb.setBasePoint1(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                   float(float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]))))
                        elif row[sbtab_layout.columns_dict['!SBML:layout:curveSegment']] == 'BasePoint2':
                            cb.setBasePoint2(libsbml.Point(layoutns, float(row[sbtab_layout.columns_dict['!SBML:layout:X']]),
                                                   float(float(row[sbtab_layout.columns_dict['!SBML:layout:Y']]))))
                except:
                    self.warnings.append('Warning: Could not create the Species Reference Curve Layout.')

                            
    def compound_sbtab(self):
        '''
        extract information from the Compound SBtab and writes it to the model
        '''
        sbtab_compounds = self.sbtab_doc.type_to_sbtab['Compound']
        
        # build compounds
        for sbtab_compound in sbtab_compounds:
            self.check_id(sbtab_compound)
            for i, row in enumerate(sbtab_compound.value_rows):
                if row[sbtab_compound.columns_dict['!ID']] not in self.species_list:
                    species = self.new_model.createSpecies()
                    # name and id of compartment (optional SBML id)
                    if '!SBML:species:id' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!SBML:species:id']] != '':
                        species.setId(str(row[sbtab_compound.columns_dict['!Compound:SBML:species:id']]))
                        self.id2sbmlid[row[sbtab_compound.columns_dict['!ID']]] = row[sbtab_compound.columns_dict['!Compound:SBML:species:id']]
                    else:
                        species.setId(str(row[sbtab_compound.columns_dict['!ID']]))
                        self.id2sbmlid[row[sbtab_compound.columns_dict['!ID']]] = None
                        
                    if '!Name' in sbtab_compound.columns and \
                       not row[sbtab_compound.columns_dict['!Name']] == '':
                        if '|' in row[sbtab_compound.columns_dict['!Name']]:
                            species.setName(str(row[sbtab_compound.columns_dict['!Name']].split('|')[0]))
                        else:
                            species.setName(str(row[sbtab_compound.columns_dict['!Name']]))
                    else:
                        species.setName(str(row[sbtab_compound.columns_dict['!ID']]))
                    self.species_list.append(species.getId())
                    self.model_ids.append(species.getId())

                    # speciestype (if given)
                    if '!SBML:speciestype:id' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!SBML:speciestype:id']] != '':
                        species_type = self.new_model.createSpeciesType()
                        species_type.setId(str(row[sbtab_compound.columns_dict['!SBML:speciestype:id']]))
                        species.setSpeciesType(row[sbtab_compound.columns_dict['!SBML:speciestype:id']])

                    # if compartments are given, add them
                    if '!Location' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!Location']] != '':
                        if not row[sbtab_compound.columns_dict['!Location']] in self.compartment_list:
                            new_comp = self.new_model.createCompartment()
                            new_comp.setId(str(row[sbtab_compound.columns_dict['!Location']]))
                            new_comp.setName(str(row[sbtab_compound.columns_dict['!Location']]))
                            new_comp.setSize(True)
                            new_comp.setConstant(True)
                            self.compartment_list.append(row[sbtab_compound.columns_dict['!Location']])
                        species.setCompartment(row[sbtab_compound.columns_dict['!Location']])
                    elif self.def_comp_set:
                        species.setCompartment('Default_Compartment')
                    else:
                        self.warnings.append('Could not set compartment for species %s.' % species.getId())

                    # some more options
                    if '!InitialConcentration' in sbtab_compound.columns \
                       and row[sbtab_compound.columns_dict['!InitialConcentration']] != '':
                        species.setInitialConcentration(float(row[sbtab_compound.columns_dict['!InitialConcentration']]))
                    elif '!InitialValue' in sbtab_compound.columns and \
                         row[sbtab_compound.columns_dict['!InitialValue']] != '':
                        species.setInitialConcentration(float(row[sbtab_compound.columns_dict['!InitialValue']]))

                    if '!IsConstant' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!IsConstant']] != '':
                        if row[sbtab_compound.columns_dict['!IsConstant']].lower() == 'false':
                            try:
                                species.setConstant(False)
                                species.setBoundaryCondition(False)
                            except: pass
                        else:
                            try:
                                species.setConstant(True)
                                species.setBoundaryCondition(True)
                            except: pass
                    else:
                        species.setConstant(False)
                        species.setBoundaryCondition(False)

                    if '!hasOnlySubstanceUnits' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!hasOnlySubstanceUnits']] != '':
                        if row[sbtab_compound.columns_dict['!hasOnlySubstanceUnits']].lower() == 'false':
                            try:
                                species.setHasOnlySubstanceUnits(False)
                            except: pass
                        else:
                            try:
                                species.setHasOnlySubstanceUnits(True)
                            except: pass
                    else:
                        species.setHasOnlySubstanceUnits(False)

                    if '!Comment' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!Comment']] != '':
                        try:
                            note = '<body xmlns="http://www.w3.org/1999/xhtml"><p>%s</p></body>' % row[sbtab_compound.columns_dict['!Comment']]
                            species.setNotes(note)
                        except: pass

                    if '!ReferenceName' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!ReferenceName']] != '':
                        try:
                            note = '<body xmlns="http://www.w3.org/1999/xhtml"><p>%s</p></body>' % row[sbtab_compound.columns_dict['!ReferenceName']]
                            species.setNotes(note)
                        except: pass

                    if '!SBOTerm' in sbtab_compound.columns and \
                       row[sbtab_compound.columns_dict['!SBOTerm']] != '':
                        try: species.setSBOTerm(int(row[sbtab_compound.columns_dict['!SBOTerm']][4:]))
                        except: pass

                    if '!Unit' in sbtab_compound.columns and self.unit_mM == False:
                        if row[sbtab_compound.columns_dict['!Unit']] == 'mM':
                            self.unit_def_mm()
                            self.unit_mM = True
                        elif row[sbtab_compound.columns_dict['!Unit']].lower().startswith('molecules'):
                            self.unit_def_mpdw()
                            self.unit_mpdw = True

                    # FBC content
                    if self.fbc:
                        if '!SBML:fbc:charge' in sbtab_compound.columns and \
                           row[sbtab_compound.columns_dict['!SBML:fbc:charge']] != '':
                            splugin = species.getPlugin('fbc')
                            if splugin is not None:
                                try: splugin.setCharge(int(row[sbtab_compound.columns_dict['!SBML:fbc:charge']]))
                                except: pass

                        if '!SBML:fbc:chemicalFormula' in sbtab_compound.columns and \
                           row[sbtab_compound.columns_dict['!SBML:fbc:chemicalFormula']] != '':
                            splugin = species.getPlugin('fbc')
                            if splugin is not None:
                                try: splugin.setChemicalFormula(row[sbtab_compound.columns_dict['!SBML:fbc:chemicalFormula']])
                                except: pass
                            
                    # search for identifiers and annotations
                    for column in sbtab_compound.columns_dict.keys():
                        if 'Identifiers' in column:
                            annot = row[sbtab_compound.columns_dict[column]]
                            if annot == '': continue
                            for pattern in urns:
                                if pattern in column:
                                    urn = pattern
                            try:
                                cv_term = self.set_annotation(species, annot,
                                                              urn, 'Biological')
                                species.addCVTerm(cv_term)
                            except:
                                self.warnings.append('The annotation %s could not be a'\
                                                     'ssigned properly to %s.' % (annot, species.getId()))

        #species without compartments yield errors --> set them to the first available compartment
        for species in self.new_model.getListOfSpecies():
            if not species.isSetCompartment():
                species.setCompartment(self.compartment_list[0])

    def is_number(self, s):
        '''
        test if a given string is a number masked as string; this is mainly
        important while setting SBML IDs (which must NOT be numbers)
        '''
        try:
            float(s)
            return True
        except:
            return False
                
    def reaction_sbtab(self):
        '''
        extract information from the Reaction SBtab and write it to the model
        '''
        sbtab_reactions = self.sbtab_doc.type_to_sbtab['Reaction']

        # preprocessing: if there are species in the reaction formulas, which
        #                  we have not yet created for the model, create them
        for sbtab_reaction in sbtab_reactions:
            self.check_id(sbtab_reaction)
            if '!ReactionFormula' in sbtab_reaction.columns:
                self.get_reactants(sbtab_reaction)
                for reaction in self.reaction2reactants:
                    try: compartment = self.reaction2compartment[reaction]
                    except: compartment = False
                    educts = self.reaction2reactants[reaction][0]
                    for educt in educts:
                        if educt == '': continue
                        if educt not in self.id2sbmlid.keys() and \
                           not educt in self.species_list:
                            sp = self.new_model.createSpecies()
                            sp.setId(str(educt))
                            sp.setName(str(educt))
                            sp.setConstant(False)
                            sp.setBoundaryCondition(False)
                            sp.setHasOnlySubstanceUnits(False)                            
                            if compartment: sp.setCompartment(compartment)
                            elif self.def_comp_set:
                                sp.setCompartment('Default_Compartment')
                            self.species_list.append(sp.getId())
                            self.model_ids.append(sp.getId())
                    products = self.reaction2reactants[reaction][1]
                    for product in products:
                        if product == '': continue
                        if not product in self.id2sbmlid.keys() and \
                           not product in self.species_list:
                            sp = self.new_model.createSpecies()
                            sp.setId(str(product))
                            sp.setName(str(product))
                            sp.setConstant(False)
                            sp.setBoundaryCondition(False)
                            sp.setHasOnlySubstanceUnits(False)
                            if compartment: sp.setCompartment(compartment)
                            elif self.def_comp_set:
                                sp.setCompartment('Default_Compartment')
                            self.species_list.append(sp.getId())
                            self.model_ids.append(sp.getId())

            #if compartments are given for the reactions and these compartments are not built yet:
            if '!Location' in sbtab_reaction.columns:
                for row in sbtab_reaction.value_rows:
                    if row[sbtab_reaction.columns_dict['!Location']] == '':
                        continue
                    if row[sbtab_reaction.columns_dict['!Location']] not in self.compartment_list:
                        compartment = self.new_model.createCompartment()
                        compartment.setId(row[sbtab_reaction.columns_dict['!Location']])
                        compartment.setName(row[sbtab_reaction.columns_dict['!Location']])
                        compartment.setSize(1)
                        compartment.setConstant(True)
                        self.compartment_list.append(row[sbtab_reaction.columns_dict['!Location']])
                        self.model_ids.append(compartment.getId())

            try:
                sbtab_reaction.columns_dict['!KineticLaw']
                self.warnings.append('Warning: Please be aware that the SBtab -> SBML conversion does not include a validation of the provided kinetic rate laws. Thus, invalid SBML code may be produced which cannot be simulated. Please check the correctness of your kinetic rate laws manually.')
            except: pass

            #creating the reactions
            for row in sbtab_reaction.value_rows:
                # if the reaction must not be included in the model: continue
                if '!BuildReaction' in sbtab_reaction.columns and \
                   row[sbtab_reaction.columns_dict['!BuildReaction']] == 'False':
                    continue
                react = self.new_model.createReaction()

                # set id and name
                if '!SBML:reaction:id' in sbtab_reaction.columns and \
                   row[sbtab_reaction.columns_dict['!SBML:reaction:id']] != '' and \
                                                                            not self.is_number(row[sbtab_reaction.columns_dict['!SBML:reaction:id']]):
                    r_id = str(row[sbtab_reaction.columns_dict['!SBML:reaction:id']])
                    react.setId(r_id)

                else:
                    r_id = str(row[sbtab_reaction.columns_dict['!ID']])
                    react.setId(r_id)

                if '!Name' in sbtab_reaction.columns:
                    if row[sbtab_reaction.columns_dict['!Name']] != '':
                        if '|' in row[sbtab_reaction.columns_dict['!Name']]:
                            react.setName(str(row[sbtab_reaction.columns_dict['!Name']].split('|')[0]))
                        else: react.setName(str(row[sbtab_reaction.columns_dict['!Name']]))
                    else: react.setName(str(row[sbtab_reaction.columns_dict['!ID']]))
                else: react.setName(str(row[sbtab_reaction.columns_dict['!ID']]))

                # some more options
                if '!SBOTerm' in sbtab_reaction.columns:
                    if row[sbtab_reaction.columns_dict['!SBOTerm']] != '':
                        try: react.setSBOTerm(int(row[sbtab_reaction.columns_dict['!SBOTerm']][4:]))
                        except: pass

                if '!IsReversible' in sbtab_reaction.columns and \
                   row[sbtab_reaction.columns_dict['!IsReversible']] != '':
                    if string.capwords(row[sbtab_reaction.columns_dict['!IsReversible']]) == 'False':
                        try: react.setReversible(False)
                        except: pass
                    elif string.capwords(row[sbtab_reaction.columns_dict['!IsReversible']]) == 'True':
                        try: react.setReversible(True)
                        except: pass
                else:
                    react.setReversible(True)

                if '!IsFast' in sbtab_reaction.columns and \
                   row[sbtab_reaction.columns_dict['!IsFast']] != '':
                    if string.capwords(row[sbtab_reaction.columns_dict['!IsFast']]) == 'False':
                        try: react.setFast(False)
                        except: pass
                    elif string.capwords(row[sbtab_reaction.columns_dict['!IsFast']]) == 'True':
                        try: react.setFast(True)
                        except: pass
                else:
                    react.setFast(False)

                #if sumformula is at hand: generate reactants and products
                if '!ReactionFormula' in sbtab_reaction.columns and \
                   row[sbtab_reaction.columns_dict['!ReactionFormula']] != '':
                    for educt in self.reaction2reactants[row[sbtab_reaction.columns_dict['!ID']]][0]:
                        if educt == '': continue
                        reactant = react.createReactant()
                        if educt in self.id2sbmlid:
                            if self.id2sbmlid[educt] != None:
                                reactant.setSpecies(self.id2sbmlid[educt])
                            else: reactant.setSpecies(educt)
                        else: reactant.setSpecies(educt)

                        reactant.setStoichiometry(self.rrps2stoichiometry[row[sbtab_reaction.columns_dict['!ID']],educt])
                        if self.fbc: reactant.setConstant(True)
                        else: reactant.setConstant(False)
                    for product in self.reaction2reactants[row[sbtab_reaction.columns_dict['!ID']]][1]:
                        if product == '': continue
                        reactant = react.createProduct()
                        if self.fbc: reactant.setConstant(True)
                        else: reactant.setConstant(False)
                        if product in self.id2sbmlid.keys():
                            if self.id2sbmlid[product] != None: reactant.setSpecies(self.id2sbmlid[product])
                            else: reactant.setSpecies(product)
                        else: reactant.setSpecies(product)
                        reactant.setStoichiometry(self.rrps2stoichiometry[row[sbtab_reaction.columns_dict['!ID']],product])
                '''
                #Uncomment, if we start using SBML Level 3, Version 1, or higher
                #if location is at hand: link reaction to the compartment
                if sbtab_reaction.columns_dict['!Location'] and row[sbtab_reaction.columns_dict['!Location']] != '':
                    if not row[sbtab_reaction.columns_dict['!Location']] in self.compartment_list:
                        new_comp = self.new_model.createCompartment()
                        new_comp.setId(row[sbtab_reaction.columns_dict['!Location']])
                        react.setCompartment(new_comp)
                        self.compartment_list.append(row[sbtab_reaction.columns_dict['!Location']])
                    else:
                        react.setCompartment(row[loc_column])
                '''
                #if an enzyme is given, mark it as modifier to the reaction
                try:
                    sbtab_reaction.columns_dict['!Regulator']
                    if row[sbtab_reaction.columns_dict['!Regulator']] != '':
                        if "|" in row[sbtab_reaction.columns_dict['!Regulator']]:
                            splits = row[sbtab_reaction.columns_dict['!Regulator']].split('|')
                            for element in splits:
                                #element = element.strip()
                                if element.startswith('+') and element[1:] in self.species_list:
                                    try:
                                        mod = react.createModifier()
                                        mod.setSpecies(element[1:])
                                        mod.setSBOTerm(459)
                                        self.modifier_list.append(element)
                                    except: pass
                                elif element.startswith('-') and element[1:] in self.species_list:
                                    try:
                                        mod = react.createModifier()
                                        mod.setSpecies(element[1:])
                                        mod.setSBOTerm(20)
                                        self.modifier_list.append(element)
                                    except: pass
                                elif element[1:] in self.species_list:
                                    try:
                                        mod = react.createModifier()
                                        mod.setSpecies(element[1:])
                                        self.modifier_list.append(element)
                                        letring = str('Warning: The reaction modifier '+element+' could not be identified as either stimulator or inhibitor. Please add an SBO Term.')
                                        self.warnings.append(letring)
                                    except: pass
                        else:
                            if (row[sbtab_reaction.columns_dict['!Regulator']]).startswith('+') and row[sbtab_reaction.columns_dict['!Regulator']] in self.species_list:
                                try:
                                    mod = react.createModifier()
                                    mod.setSpecies(row[sbtab_reaction.columns_dict['!Regulator']][1:])
                                    mod.setSBOTerm(459)
                                    self.modifier_list.append(row[sbtab_reaction.columns_dict['!Regulator']])
                                except: pass
                            elif (row[sbtab_reaction.columns_dict['!Regulator']]).startswith('-') and row[sbtab_reaction.columns_dict['!Regulator']] in self.species_list:
                                try:
                                    mod = react.createModifier()
                                    mod.setSpecies(row[sbtab_reaction.columns_dict['!Regulator']][1:])
                                    mod.setSBOTerm(20)
                                    self.modifier_list.append(row[sbtab_reaction.columns_dict['!Regulator']])
                                except: pass
                            elif row[sbtab_reaction.columns_dict['!Regulator']] in self.species_list:
                                try:
                                    mod = react.createModifier()
                                    mod.setSpecies(row[sbtab_reaction.columns_dict['!Regulator']])
                                    self.modifier_list.append(row[sbtab_reaction.columns_dict['!Regulator']])
                                    letring = str('Warning: The reaction modifier '+row[sbtab_reaction.columns_dict['!Regulator']]+' could not be identified as either stimulator or inhibitor. Please add an SBO Term.')
                                    self.warnings.append(letring)
                                except: pass
                            self.modifier_list.append(row[sbtab_reaction.columns_dict['!Regulator']])

                except: pass
                '''
                #if metabolic regulators are given: extract them and create them
                try:
                    sbtab_reaction.columns_dict['!MetabolicRegulators']
                    if row[sbtab_reaction.columns_dict['!MetabolicRegulators']] != '':
                        acts,inhs = self.extractRegulators(row[sbtab_reaction.columns_dict['!MetabolicRegulators']])
                        for activator in acts:
                            if activator in self.species_list and activator not in self.modifier_list:
                                acti = react.createModifier()
                                acti.setSpecies(activator)
                                acti.setSBOTerm(459)
                                #react.addModifier(acti)
                                self.modifier_list.append(acti)
                        for inhibitor in inhs:
                            if inhibitor in self.species_list and inhibitor not in self.modifier_list:
                                inhi = react.createModifier()
                                inhi.setSpecies(inhibitor)
                                inhi.setSBOTerm(20)
                                #react.addModifier(inhi)
                                self.modifier_list.append(inhi)
                except: pass
                '''
                #since local parameters need to be entered *after* reaction creation, but *before* setting
                try:
                    sbtab_reaction.columns_dict['!KineticLaw']
                    if row[sbtab_reaction.columns_dict['!KineticLaw']] != '':
                        kl = react.createKineticLaw()
                        formula = row[sbtab_reaction.columns_dict['!KineticLaw']]
                        kl.setFormula(formula)
                        react.setKineticLaw(kl)

                        # extract parameters from the Math object to see if they
                        # need to be initialised manually
                        parameter_names = self.extract_parameters_from_formula(react.getKineticLaw().getMath())
                        for p in parameter_names:
                            if p not in self.parameters_global and p not in self.parameters_local and p not in self.species_list:
                                self.create_parameter(p)

                        #for erraneous laws: remove them
                        if react.getKineticLaw().getFormula() == '':
                            react.unsetKineticLaw()
                except: pass

                # Attributes for FBC package
                if self.fbc:
                    if '!SBML:fbc:LowerBound' in sbtab_reaction.columns and \
                       row[sbtab_reaction.columns_dict['!SBML:fbc:LowerBound']] != '':
                        rplugin = react.getPlugin('fbc')
                        try:
                            parameter = row[sbtab_reaction.columns_dict['!SBML:fbc:LowerBound']].strip()
                            # special case for Frank TB: if only a number is given, create parameter
                            if re.match("\d*", parameter).group(0) != '':
                                parameter_name = '%s_fbc_lb' % r_id
                                rplugin.setLowerFluxBound(parameter_name)
                                self.create_parameter(parameter_name, value=float(parameter))
                            else:
                                rplugin.setLowerFluxBound(parameter)
                                if parameter not in self.parameters_global:
                                    self.create_parameter(parameter)                        
                        except:
                            self.warnings.append('Could not set FBC LowerFluxBound of Reaction %s' % (react.getId()))

                    if '!SBML:fbc:UpperBound' in sbtab_reaction.columns and \
                       row[sbtab_reaction.columns_dict['!SBML:fbc:UpperBound']] != '':
                        rplugin = react.getPlugin('fbc')
                        try:
                            parameter = row[sbtab_reaction.columns_dict['!SBML:fbc:UpperBound']].strip()
                            # special case for Frank TB: if only a number is given, create parameter
                            if re.match("\d*", parameter).group(0) != '':
                                parameter_name = '%s_fbc_ub' % r_id
                                rplugin.setUpperFluxBound(parameter_name)
                                self.create_parameter(parameter_name, value=float(parameter))
                            else:
                                rplugin.setUpperFluxBound(parameter)
                                if parameter not in self.parameters_global:
                                    self.create_parameter(parameter)
                        except:
                            self.warnings.append('Could not set FBC UpperFluxBound of Reaction %s' % (react.getId()))                


                    if '!SBML:fbc:GeneAssociation' in sbtab_reaction.columns and \
                       row[sbtab_reaction.columns_dict['!SBML:fbc:GeneAssociation']] != '':
                        try:
                            rplugin = react.getPlugin('fbc')
                            ga = rplugin.createGeneProductAssociation()
                            ga.setAssociation(row[sbtab_reaction.columns_dict['!SBML:fbc:GeneAssociation']])
                        except: pass
                        
                #set annotations if given:
                for column in sbtab_reaction.columns_dict.keys():
                    if "Identifiers" in column:
                        annot = row[sbtab_reaction.columns_dict[column]]
                        if annot == '': continue
                        for pattern in urns:
                            if pattern in column:
                                urn = pattern
                        try:
                            cv_term = self.set_annotation(react,annot,urn,'Biological')
                            react.addCVTerm(cv_term)
                        except:
                            self.warnings.append('The annotation %s could not be a'\
                                                 'ssigned properly to %s.' % (annot, react.getId()))                        
                
    def create_gene_product(self, gene_product):
        '''
        creates an FBC gene product.
        was formerly employed for creating genes that occur in GeneAssociation
        column without being declared elsewhere (deprecated?)
        '''
        self.gene_products.append(gene_product)

    def create_parameter(self, parameter, value=1):
        '''
        creates a default global parameter (if it is used by a reaction but not provided
        by an accompanying Quantity SBtab)
        '''
        new_parameter = self.new_model.createParameter()
        new_parameter.setId(parameter)
        new_parameter.setConstant(True)
        new_parameter.setValue(value)
        self.parameters_global.append(new_parameter.getId())

        self.unit_def_mm()
        self.unit_def_mpdw()
                                    
    def extract_parameters_from_formula(self, formula):
        '''
        extracts the parameters from the formula in order to create proper SBML
        parameters. Parameters that only appear in a formula but not in a parameter
        list yield errors in SBML3
        '''
        parameter_names = []
        for i in range(formula.getNumChildren()):
            name = formula.getChild(i).getName()
            if name != None: parameter_names.append(name)
            else:
                parameters_rec = self.extract_parameters_from_formula(formula.getChild(i))
                for p in parameters_rec:
                    parameter_names.append(p)

        return parameter_names
                
    def unit_def_mm(self):
        '''
        build unit definition
        '''
        if not 'mM' in self.unit_definitions:
            ud = self.new_model.createUnitDefinition()
            ud.setId('mM')
            ud.setName('mM')
            self.unit_definitions.append(ud.getId())

            mole = ud.createUnit()
            mole.setScale(-3)
            mole.setExponent(1)
            mole.setMultiplier(1)
            mole.setKind(libsbml.UNIT_KIND_MOLE)

            litre = ud.createUnit()
            litre.setExponent(-1)
            litre.setScale(1)
            litre.setMultiplier(1)
            litre.setKind(libsbml.UNIT_KIND_LITRE)

    def unit_def_mpdw(self):
        '''
        build unit definition
        '''
        if not 'mmol_per_gDW_per_hr' in self.unit_definitions:
            ud = self.new_model.createUnitDefinition()
            ud.setId('mmol_per_gDW_per_hr')
            ud.setName('mmol_per_gDW_per_hr')
            self.unit_definitions.append(ud.getId())

            mole = ud.createUnit()
            mole.setScale(-3)
            mole.setExponent(1)
            mole.setMultiplier(1)
            mole.setKind(libsbml.UNIT_KIND_MOLE)

            litre = ud.createUnit()
            litre.setScale(0)
            litre.setExponent(-1)
            litre.setMultiplier(1)
            litre.setKind(libsbml.UNIT_KIND_GRAM)
       
            second = ud.createUnit()
            second.setScale(0)
            second.setExponent(-1)
            second.setMultiplier(3600)
            second.setKind(libsbml.UNIT_KIND_SECOND)

    def extractRegulators(self,mods):
        '''
        Extracts the regulators from the column "Regulator".

        Parameters
        ----------
        mods : str
           The modifiers of a reaction.
        '''
        activators = []
        inhibitors = []

        splits = mods.split(' ')

        for i,element in enumerate(splits):
            if element == '+': activators.append(splits[i+1])
            elif element == '-': inhibitors.append(splits[i+1])

        return activators,inhibitors

        
    def get_reactants(self, sbtab):
        '''
        Extracts the reactants from the a reaction formula.

        Parameters
        ----------
        sbtab : SBtab object
           SBtab file as SBtab object.
        '''
        self.reaction2reactants = {}
        self.rrps2stoichiometry = {}
        self.reaction2compartment = {}
        self.specrect2compartment = {}
        educts = []
        products = []
        
        for reaction in sbtab.value_rows:
            r_id = reaction[sbtab.columns_dict['!ID']]
            if '!Location' in sbtab.columns:
                self.reaction2compartment[r_id] = reaction[sbtab.columns_dict['!Location']]
            sum_formula  = reaction[sbtab.columns_dict['!ReactionFormula']]

            #is a compartment given for the reaction? (nice, but we cannot set it (only in SBML version 3))
            if sum_formula.startswith('['):
                self.reaction2compartment[r_id] = re.search('[([^"]*)]',sum_formula).group(1)

            #check the educts
            try:
                educt_list = re.search('([^"]*)<=>',sum_formula).group(1)
                educts = []
                for educt in educt_list.split('+'):
                    try:
                        float(educt.lstrip().rstrip().split(' ')[0])
                        self.rrps2stoichiometry[r_id,educt.lstrip().rstrip().split(' ')[1]] = float(educt.lstrip().rstrip().split(' ')[0])
                        educts.append(educt.lstrip().rstrip().split(' ')[1])
                    except:
                        self.rrps2stoichiometry[r_id,educt.lstrip().rstrip()] = 1
                        educts.append(educt.lstrip().rstrip())
            except: pass

            #check the products
            try:
                product_list = re.search('<=>([^"]*)',sum_formula).group(1)
                products = []
                for product in product_list.split('+'):
                    try:
                        float(product.lstrip().rstrip().split(' ')[0])
                        self.rrps2stoichiometry[r_id,product.lstrip().rstrip().split(' ')[1]] = float(product.lstrip().rstrip().split(' ')[0])
                        products.append(product.lstrip().rstrip().split(' ')[1])
                    except:
                        self.rrps2stoichiometry[r_id,product.lstrip().rstrip()] = 1
                        products.append(product.lstrip().rstrip())
            except: pass

            self.reaction2reactants[r_id] = [educts,products]

    def gene_sbtab(self):
        '''
        Extracts the information from the Gene SBtab and writes it to the model.
        Currently, this has an emphasis on the FBC gene products, not general
        gene information
        '''
        sbtabs_gene = self.sbtab_doc.type_to_sbtab['Gene']
        
        for sbtab_gene in sbtabs_gene:
            self.check_id(sbtab_gene)
            if self.fbc:
                mplugin = self.new_model.getPlugin('fbc')
                for row in sbtab_gene.value_rows:
                    if row[sbtab_gene.columns_dict['!SBML:fbc:geneProduct']].capitalize() == 'True':
                        gene_product = mplugin.createGeneProduct()
                        try: gene_product.setId(row[sbtab_gene.columns_dict['!SBML:fbc:ID']])
                        except: gene_product.setId(row[sbtab_gene.columns_dict['!ID']])
                        try: gene_product.setName(row[sbtab_gene.columns_dict['!SBML:fbc:Name']])
                        except: pass
                        try: gene_product.setLabel(row[sbtab_gene.columns_dict['!SBML:fbc:label']])
                        except: pass
                        self.gene_products.append(gene_product.getId())
                    elif row[sbtab_gene.columns_dict['!SBML:fbc:GeneAssociation']].capitalize() == 'True':
                        gene_association = mplugin.createGeneAssociation()
                        try: gene_association.setId(row[sbtab_gene.columns_dict['!SBML:fbc:ID']])
                        except: gene_association.setId(row[sbtab_gene.columns_dict['!ID']])
                        try: gene_association.setName(row[sbtab_gene.columns_dict['!SBML:fbc:Name']])
                        except: pass
                        
                    for column in sbtab_gene.columns_dict.keys():
                        if "Identifiers" in column:
                            annot = row[sbtab_gene.columns_dict[column]]
                            if annot == '': continue
                            for pattern in urns:
                                if pattern in column:
                                    urn = pattern
                            try:
                                try:
                                    cv_term = self.set_annotation(gene_association,annot,urn,'Biological')
                                    gene_association.addCVTerm(cv_term)
                                except:
                                    cv_term = self.set_annotation(gene_product,annot,urn,'Biological')
                                    gene_product.addCVTerm(cv_term)
                            except:
                                self.warnings.append('The annotation %s could not be a'\
                                                     'ssigned properly.' % annot)

            
    def quantity_sbtab(self):
        '''
        Extracts the information from the Quantity SBtab and writes it to the model.
        '''
        sbtabs_quantity = self.sbtab_doc.type_to_sbtab['Quantity']

        for sbtab_quantity in sbtabs_quantity:
            self.check_id(sbtab_quantity)
            for row in sbtab_quantity.value_rows:
                try:
                    if row[sbtab_quantity.columns_dict['!Type']] == 'local parameter':
                        for reaction in self.new_model.getListOfReactions():
                            kl = reaction.getKineticLaw()
                            formula = kl.getFormula()
                            if row[sbtab_quantity.columns_dict['!SBML:reaction:parameter:id']] in formula:
                                lp = kl.createParameter()
                                lp.setId(row[sbtab_quantity.columns_dict['!SBML:reaction:parameter:id']])
                                self.model_ids.append(lp.getId())
                                try: lp.setValue(float(row[sbtab_quantity.columns_dict['!Value']]))
                                except: lp.setValue(1.0)
                                try: lp.setUnits(row[sbtab_quantity.columns_dict['!Unit']])
                                except: pass
                                if '!Unit' in sbtab_quantity.columns and self.unit_mM == False:
                                    if row[sbtab_quantity.columns_dict['!Unit']] == 'mM':
                                        self.unit_def_mm()
                                        self.unit_mM = True
                                    elif row[sbtab_quantity.columns_dict['!Unit']].lower().startswith('molecules'):
                                        self.unit_def_mpdw()
                                        self.unit_mpdw = True
                                if '!SBOTerm' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!SBOTerm']] != '':
                                    try: lp.setSBOTerm(int(row[sbtab_quantity.columns_dict['!SBOTerm']][4:]))
                                    except: pass
                                if '!IsConstant' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!IsConstant']] != '':
                                    if row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'true': lp.setConstant(True)
                                    elif row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'false': lp.setConstant(False)
                                    else: lp.setConstant(True)
                                else: lp.setConstant(True)
                                self.parameters_local.append(lp.getId())
                    else:
                        parameter = self.new_model.createParameter()
                        try: parameter.setId(row[sbtab_quantity.columns_dict['!Parameter:SBML:parameter:id']])
                        except: parameter.setId(row[sbtab_quantity.columns_dict['!ID']])
                        self.model_ids.append(parameter.getId())
                        try: parameter.setValue(float(row[sbtab_quantity.columns_dict['!Value']]))
                        except: parameter.setValue(1.0)
                        try: parameter.setUnits(row[sbtab_quantity.columns_dict['!Unit']])
                        except: pass
                        if '!SBOTerm' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!SBOTerm']] != '':
                            try: parameter.setSBOTerm(int(row[sbtab_quantity.columns_dict['!SBOTerm']][4:]))
                            except: pass
                        if '!IsConstant' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!IsConstant']] != '':
                            if row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'true': parameter.setConstant(True)
                            elif row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'false': parameter.setConstant(False)
                            else: parameter.setConstant(True)
                        else: parameter.setConstant(True)
                        self.parameters_global.append(parameter.getId())
                except:
                    parameter = self.new_model.createParameter()
                    try: parameter.setId(row[sbtab_quantity.columns_dict['!Parameter:SBML:parameter:id']])
                    except: parameter.setId(row[sbtab_quantity.columns_dict['!ID']])
                    self.model_ids.append(parameter.getId())
                    try: parameter.setValue(float(row[sbtab_quantity.columns_dict['!Value']]))
                    except: parameter.setValue(1.0)
                    try: parameter.setUnits(row[sbtab_quantity.columns_dict['!Unit']])
                    except: pass                    
                    if '!SBOTerm' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!SBOTerm']] != '':
                        try: parameter.setSBOTerm(int(row[sbtab_quantity.columns_dict['!SBOTerm']][4:]))
                        except: pass
                    if '!IsConstant' in sbtab_quantity.columns and row[sbtab_quantity.columns_dict['!IsConstant']] != '':
                        if row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'true': parameter.setConstant(True)
                        elif row[sbtab_quantity.columns_dict['!IsConstant']].lower() == 'false': parameter.setConstant(False)
                        else: parameter.setConstant(True)
                    else: parameter.setConstant(True)
                    self.parameters_global.append(parameter.getId())

                # set unit definitions 
                self.unit_def_mm()
                self.unit_def_mpdw()

    def eventSBtab(self):
        '''
        Extracts the information from the Event SBtab and writes it to the model.
        '''
        sbtab = self.type2sbtab['Event']

        for row in sbtab.value_rows:
            event = self.new_model.createEvent()
            event.setId(row[sbtab.columns_dict['!Event']])
            self.model_ids.append(event.getId())
            try: event.setName(row[sbtab.columns_dict['!Name']])
            except: pass
            try:
                if row[sbtab.columns_dict['!Assignments']] != '':
                    asses = row[sbtab.columns_dict['!Assignments']].split('|')
                    if len(asses) > 1:
                        for ass in asses:
                            ea  = event.createEventAssignment()
                            var = ass.split('=')[0].strip()
                            val = ass.split('=')[1].strip()
                            ea.setMath(libsbml.parseL3Formula(val))
                            ea.setVariable(var)
                    else:
                        ea  = event.createEventAssignment()
                        var = asses[0].split('=')[0].strip()
                        val = asses[0].split('=')[1].strip()
                        ea.setMath(libsbml.parseL3Formula(val))
                        ea.setVariable(var)
            except: pass            
            try:
                if row[sbtab.columns_dict['!Trigger']] != '' and row[sbtab.columns_dict['!Trigger']] != 'None':
                    trig = event.createTrigger()
                    trig.setMetaId(row[sbtab.columns_dict['!Event']]+'_meta')
                    trig.setMath(libsbml.parseL3Formula(row[sbtab.columns_dict['!Trigger']]))
            except: pass
            if '!SBOTerm' in sbtab.columns and row[sbtab.columns_dict['!SBOTerm']] != '':
                try: event.setSBOTerm(int(row[sbtab.columns_dict['!SBOTerm']][4:]))
                except: pass
            try:
                if row[sbtab.columns_dict['!Delay']] != '' and row[sbtab.columns_dict['!Delay']] != 'None':
                    dl = event.createDelay()
                    dl.setMath(libsbml.parseL3Formula(row[sbtab.columns_dict['!Delay']]))
            except: pass
            try:
                if row[sbtab.columns_dict['!UseValuesFromTriggerTime']] == 'False':
                    event.setUseValuesFromTriggerTime(False)
                else:
                    event.setUseValuesFromTriggerTime(True)
            except: pass

            for column in sbtab.columns_dict.keys():
                if "Identifiers" in column:
                    annot = row[sbtab.columns_dict[column]]
                    if annot == '': continue
                    for pattern in urns:
                        if pattern in column:
                            urn = pattern
                    try:
                        cv_term = self.set_annotation(event,annot,urn,'Biological')
                        event.addCVTerm(cv_term)
                    except:
                        self.warnings.append('The annotation %s could not be a'\
                                             'ssigned properly to %s.' % (annot, event.getId()))

    def ruleSBtab(self):
        '''
        Extracts the information from the Rule SBtab and writes it to the model.
        '''
        sbtab = self.type2sbtab['Rule']

        for row in sbtab.value_rows:
            if row[sbtab.columns_dict['!Name']] == 'assignmentRule':
                rule = self.new_model.createAssignmentRule()
            elif row[sbtab.columns_dict['!Name']] == 'algebraicRule':
                rule = self.new_model.createAlgebraicRule()
            elif row[sbtab.columns_dict['!Name']] == 'rateRule':
                rule = self.new_model.createRateRule()
            else: continue
            rule.setMetaId(row[sbtab.columns_dict['!Rule']]+'_meta')
            try: rule.setName(row[sbtab.columns_dict['!Name']])
            except: pass
            try: rule.setUnits(row[sbtab.columns_dict['!Unit']])
            except: pass
            try:
                if row[sbtab.columns_dict['!Formula']] != '':
                    asses = row[sbtab.columns_dict['!Formula']]
                    var = asses.split('=')[0].strip()
                    val = asses.split('=')[1].strip()
                    rule.setMath(libsbml.parseL3Formula(val))
                    rule.setVariable(var)
            except:
                pass
            for column in sbtab.columns_dict.keys():
                if "Identifiers" in column:
                    annot = row[sbtab.columns_dict[column]]
                    if annot == '': continue
                    for pattern in urns:
                        if pattern in column:
                            urn = pattern
                    try:
                        cv_term = self.set_annotation(event,annot,urn,'Biological')
                        rule.addCVTerm(cv_term)
                    except:
                        self.warnings.append('The annotation %s could not be a'\
                                             'ssigned properly to %s.' % (annot, rule.getId()))

