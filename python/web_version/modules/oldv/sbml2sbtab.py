"""
SBML2SBtab Converter
====================

Python script that converts an SBML file to SBtab file/s.

See specification for further information.

Everything should still be functionable, just remember:
- 2 more columns in Compound and Reaction, which could/should be removed
- reaction formulae have -> instead of <=>
- reaction formulae have names instead of ids
- modifiers are names instead of ids
"""
#!/usr/bin/env python
import re, libsbml, numpy
import sys

allowed_sbtabs = ['Reaction','Compound','Compartment','Quantity','Event','Rule']

class ConversionError(Exception):
    '''
    Base class for errors in the SBtab conversion class.
    '''
    def __init__(self,message):
        self.message = message
    def __str__(self):
        return self.message

class SBMLDocument:
    '''
    SBML model to be converted to SBtab file/s
    '''
    def __init__(self,sbml_model,filename):
        '''
        Initalizes SBtab document, checks it for SBtabs

        Parameters
        ----------
        sbml_model : libsbml object
            SBML model as libsbml object.
        filename : str
            Filename with extension.
        '''
        #reader      = libsbml.SBMLReader()
        #sbml_modelx = reader.readSBML(sbml_model)
        #print sbml_modelx.getModel()

        self.model    = sbml_model
        self.filename = filename
        if not self.filename.endswith('.xml') and not filename.endswith('.sbml'): 
            raise ConversionError('The given file format is not supported: '+self.filename)

        #cell designer add on
        self.cd = self.determineCD(self.model)
        if self.cd:
            try: self.cd_preprocessing()
            except: print 'The preprocessing of the cell designer metadata was erroneous.'
        else:
            self.sid2sname = {}
            for sp in self.model.getListOfSpecies():
                self.sid2sname[sp.getId()] = sp.getName()



    def determineCD(self,model):
        '''
        if the provided SBML is exported from cell designer,
        loads of meta information need to be processed.
        '''
        cd = False
        for i in range(model.getNamespaces().getNumNamespaces()):
            if model.getNamespaces().getPrefix(i) == 'celldesigner':
                cd = True

        return cd

    def makeSBtabs(self):
        '''
        Generates the SBtab files.
        '''
        self.warnings = []
        sbtabs        = []

        #self.testForInconvertibles()
        for sbtab_type in allowed_sbtabs:
            try:
                function_name = 'self.'+sbtab_type.lower()+'SBtab()'
                new_sbtab = eval(function_name)
                if new_sbtab != False: sbtabs.append(new_sbtab)
            except:
                pass

        sbtabs = self.getRidOfNone(sbtabs)
        sbtabs = self.getRidOfEmptyColumns(sbtabs)

        return sbtabs,self.warnings

    def testForInconvertibles(self):
        '''
        Some SBML entities cannot be converted to SBML. Thus, we add warnings to tell the user about omitting them.
        NOTE: Not needed anymore, we now support rules (roughly)
        '''
        try:
            rules = self.model.getListOfRules()
            if len(rules)>0:
                self.warnings.append('The SBML model contains rules. These cannot be translated to the SBtab files yet.')
        except: pass
        
    def getRidOfNone(self,sbtabs):
        '''
        Removes empty SBtabs (if no values for an SBtab were provided by the SBML).

        Parameters
        ----------
        sbtabs : list
           List of single SBtab files.
        '''
        new_tabs = []
        for element in sbtabs:
            if element != None:
                new_tabs.append(element)
        return new_tabs

    def getRidOfEmptyColumns(self,sbtabs):
        '''
        Removes empty columns.

        Parameters
        ----------
        sbtabs : list
           List of single SBtab files.        
        '''
        sbtab2empty_columns = {}

        for i,sbtab in enumerate(sbtabs):
            tab   = sbtab[0]
            sptab = tab.split('\n')[1]
            empty_columns = list(range(0,len(sptab.split('\t'))))
            for k,element in enumerate(empty_columns): empty_columns[k] = str(element)
            for row in sbtab[0].split('\n')[2:]:
                for j,element in enumerate(row.split('\t')):
                    if element != '':
                        try: empty_columns.remove(str(j))
                        except: pass
            for k,element in enumerate(empty_columns): empty_columns[k] = int(element)
            sbtab2empty_columns[i] = empty_columns

        new_tabs = []
        
        for i,sbtab in enumerate(sbtabs):
            eliminate_columns = sbtab2empty_columns[i]
            new_tab = [sbtab[0].split('\n')[0]]
            #new_tab.append(sbtab[0].split('\n')[1])
            tab = sbtab[0].split('\n')[1:]
            for row in tab:
                new_row = []
                for j,element in enumerate(row.split('\t')):
                    if not j in eliminate_columns:
                        new_row.append(element)
                new_tab.append('\t'.join(new_row))
            new_tabs.append(('\n'.join(new_tab),sbtab[1]))

        return new_tabs
                

    def compartmentSBtab(self):
        '''
        Builds a Compartment SBtab.
        '''
        compartment  = [['!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Compartment" TableName="Compartment"'],['']]
        header       = ['!ID','!Name','!Size','!Unit','!SBOTerm']
        identifiers  = []
        column2ident = {}

        for comp in self.model.getListOfCompartments():
            value_row = ['']*len(header)
            value_row[0] = comp.getId()
            try: value_row[1] = comp.getName()
            except: pass
            try: value_row[2] = str(comp.getSize())
            except: pass
            try: value_row[3] = str(species.getUnits())
            except: pass
            if str(comp.getSBOTerm()) != '-1': value_row[5] ='SBO:%.7d'%comp.getSBOTerm()
            try:
                annot_tuples = self.getAnnotations(comp)
                for i,annotation in enumerate(annot_tuples):
                    if not ("!Identifiers:"+annotation[1]) in header:
                        identifiers.append(annotation[1])
                        column2ident[annotation[1]] = int(len(header)+1)
                        header.append('!Identifiers:'+annotation[1])
                        value_row.append('')
                    if annotation[1] in identifiers:
                        value_row[column2ident[annotation[1]]-1] = annotation[0]
            except: pass
            compartment.append(value_row)

        compartment[1] = header
        compartment_SB = compartment[0]
        for row in compartment[1:]:
            compartment_SB.append('\t'.join(row))
        compartment_SBtab = '\n'.join(compartment_SB)

        return [compartment_SBtab,'compartment']

    def cd_preprocessing(self):
        '''
        preprocessing to access the multilayered information of Cell Designer SBML files
        '''
        self.sid2sname           = {}
        self.sname2sid           = {}
        self.product2reaction    = {}
        self.reaction2substrates = {}
        self.sid2statename       = {}
        self.nameRes2Res1        = {}
        self.nameRes2Res2        = {}
        self.sid2resnameMod      = {}
        self.sid2notes           = {}
        self.rid2notes           = {}
        self.sid2layernotes      = {}
        self.rid2layernotes      = {}
        self.id2object           = {}
        salias2sid               = {}

        for sp in self.model.getListOfSpecies():
            self.sid2sname[sp.getId()] = sp.getName()
            self.sname2sid[sp.getName()] = sp.getId()
            self.id2object[sp.getId()] = sp
            try:
                notes_string = sp.getNotesString()
                notes_obj    = re.search('<body>(.*)</body>',notes_string.replace('\n',' '))
                self.sid2notes[sp.getId()] = notes_obj.group(1)
            except: self.sid2notes[sp.getId()] = None

        exten = self.model.getAnnotation().getChild(0)
        sp_list = exten.getChild('listOfIncludedSpecies')

        for j in range(sp_list.getNumChildren()):
            self.id2object[sp_list.getChild(j).getAttrValue(0)] = sp_list.getChild(j)

        prot_list = exten.getChild('listOfProteins')
        for i in range(prot_list.getNumChildren()):
            prot_id   = prot_list.getChild(i).getAttrValue(0)
            prot_name = prot_list.getChild(i).getAttrValue(1)
            mods      = prot_list.getChild(i).getChild('listOfModificationResidues')
            for k in range(mods.getNumChildren()):
                try: res_name = mods.getChild(k).getAttrValue(2)
                except: continue
                if res_name == 'none': continue
                res_id  = mods.getChild(k).getAttrValue(1)
                el_tple1 = (prot_id,res_id)
                el_tple2 = (prot_name,res_id)
                self.nameRes2Res1[el_tple1] = mods.getChild(k).getAttrValue(2)   #prID
                self.nameRes2Res2[el_tple2] = mods.getChild(k).getAttrValue(2)   #sName

        alias_list = exten.getChild('listOfSpeciesAliases')
        for i in range(alias_list.getNumChildren()):
            salias2sid[alias_list.getChild(i).getAttrValue(0)] = alias_list.getChild(i).getAttrValue(1)
        layer_list = exten.getChild('listOfLayers').getChild(0)
        text_list  = layer_list.getChild('listOfTexts')
        for i in range(text_list.getNumChildren()):
            ltype  = text_list.getChild(i).getAttrValue(0)
            alias = text_list.getChild(i).getAttrValue(1)
            notes = text_list.getChild(i).getChild(0).getChild(0).getCharacters()
            if ltype == 'reaction': self.rid2layernotes[alias] = notes.replace('\n',' ').replace('\t',' ').replace(';',' ')
            elif ltype == 'species':
                try: self.sid2layernotes[salias2sid[alias]] = notes.replace('\n',' ').replace('\t',' ').replace(';',' ')
                except: self.sid2layernotes[alias] = notes.replace('\n',' ').replace('\t',' ').replace(';',' ')

        for reaction in self.model.getListOfReactions():
            try:
                notes_string = reaction.getNotesString()
                notes_obj    = re.search('<body>(.*)</body>',notes_string.replace('\n',' '))
                self.rid2notes[reaction.getId()] = notes_obj.group(1)
            except: self.rid2notes[reaction.getId()] = None
            substrates = []

            for substrate in reaction.getListOfReactants():
                sname = self.sid2sname[substrate.getSpecies()]
                if ' ' in sname:
                    ss = sname.split(' ')
                    for s in ss:
                        substrates.append(s)
                else:
                    substrates.append(substrate.getSpecies())

            for pr in reaction.getListOfProducts():
                product = pr.getSpecies()

            self.product2reaction[product] = reaction.getId()
            self.reaction2substrates[reaction.getId()] = substrates

        for species in self.model.getListOfSpecies():
            state_name    = species.getName()
            firstchild    = species.getAnnotation().getChild(0)
            sI            = firstchild.getChild('speciesIdentity')
            state_name    = species.getName()
            firstchild    = species.getAnnotation().getChild(0)
            sI            = firstchild.getChild('speciesIdentity')
            state_attr    = sI.getChild('state')
            modifications = state_attr.getChild('listOfModifications')
            res_states    = []
            for k in range(modifications.getNumChildren()):
                res_id   = modifications.getChild(k).getAttrValue('residue')
                el_tple  = (species.getName(),res_id)
                try: res_name = self.nameRes2Res2[el_tple]
                except: res_name = res_id
                state    = modifications.getChild(k).getAttrValue('state')
                state_name += '_[%s]-{%s}'%(res_name,state)
            try:
                multi = int(state_attr.getChild('homodimer').getChild(0).getCharacters())
                state_name = ((state_name+'.')*multi)[:-1]
            except: pass
            
            self.sid2statename[species.getId()] = state_name

        for i in range(sp_list.getNumChildren()):
            sid           = sp_list.getChild(i).getAttrValue(0)
            sname         = sp_list.getChild(i).getAttrValue(1)
            protein       = sp_list.getChild(i).getChild('annotation').getChild('speciesIdentity').getChild('proteinReference').getChild(0).getCharacters()
            modifications = sp_list.getChild(i).getChild('annotation').getChild('speciesIdentity').getChild('state').getChild('listOfModifications')
            tples         = []
            try: multi = int(sp_list.getChild(i).getChild('annotation').getChild('speciesIdentity').getChild('state').getChild('homodimer').getChild(0).getCharacters())
            except: multi = 1
            for m in range(modifications.getNumChildren()):
                res_id     = modifications.getChild(m).getAttrValue(0)
                el_tple    = (protein,res_id)
                try: res_name = self.nameRes2Res1[el_tple]
                except: res_name = '?'
                sname += '_['+res_name+']-{'+modifications.getChild(m).getAttrValue(1)+'}'
            sname = (sname+'.')*multi
            self.sid2statename[sid] = sname[:-1]
        
    def extractNameAndState(self,species,recursion=False,r=False):
        '''
        if we are dealing with a cell designer file, we need to take the modification state
        of the species into consideration; this needs to be extracted here
        '''
        state_name    = ''
        exten         = self.model.getAnnotation().getChild(0)
        sp_list       = exten.getChild('listOfIncludedSpecies')
        
        if recursion:
            sp_obj       = self.id2object[species]
            firstchild   = sp_obj.getChild('annotation')
            sI           = firstchild.getChild('speciesIdentity')
            sclass       = sI.getChild('class')
            species_name = species
        else:
            firstchild   = species.getAnnotation().getChild(0)
            sI           = firstchild.getChild('speciesIdentity')
            sclass       = sI.getChild('class')
            species_name = species.getId()

        if sclass.getChild(0).getCharacters() == 'COMPLEX':
            for i in range(sp_list.getNumChildren()):
                try:
                    sp_id   = sp_list.getChild(i).getAttrValue(0)
                    sp_name = sp_list.getChild(i).getAttrValue(1)
                    compl   = sp_list.getChild(i).getChild('annotation').getChild('complexSpecies').getChild(0).getCharacters()
                    clas    = sp_list.getChild(i).getChild('annotation').getChild('speciesIdentity').getChild('class').getChild(0).getCharacters()
                    if species_name != compl: continue
                    if clas == 'COMPLEX':
                        state_name += self.extractNameAndState(sp_id,recursion=True)+'.'
                    else: state_name += self.sid2statename[sp_id]+'.'
                except: state_name += self.sid2statename[sp_id]+'.'
        else:
            for sp in self.model.getListOfSpecies():
                sp_id = sp.getId()
                if sp_id != species_name: continue
                state_name += self.sid2statename[sp_id]+'.'

        state_name = state_name[:-1]

        return state_name
        
    def compoundSBtab(self):
        '''
        Builds a Compound SBtab.
        '''
        compound = [['!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Compound" TableName="Compound"'],['']]
        if self.cd: header = ['!ID','!Name','!Location','!Charge','!IsConstant','!SBOTerm','!InitialConcentration','!hasOnlySubstanceUnits','!Notes','!LayerNotes']
        else: header = ['!ID','!Name','!Location','!Charge','!IsConstant','!SBOTerm','!InitialConcentration','!hasOnlySubstanceUnits']
        identifiers  = []
        column2ident = {}

        for species in self.model.getListOfSpecies():
            value_row = ['']*len(header)
            value_row[0] = species.getId()
            try: name = self.extractNameAndState(species)
            except: name = species.getName()
            value_row[1] = name
            try: value_row[2] = species.getCompartment()
            except: pass
            try: value_row[3] = str(species.getCharge())
            except: pass
            try: value_row[4] = str(species.getConstant())
            except: pass
            if str(species.getSBOTerm()) != '-1': value_row[5] ='SBO:%.7d'%species.getSBOTerm()
            try: value_row[6] = str(species.getInitialConcentration())
            except: pass
            try: value_row[7] = str(species.getHasOnlySubstanceUnits())
            except: pass
            try: value_row[8] = str(self.sid2notes[species.getId()])
            except: pass
            try: value_row[9] = str(self.sid2layernotes[species.getId()])
            except: pass
            try:
                annot_tuples = self.getAnnotations(species)
                for i,annotation in enumerate(annot_tuples):
                    if not ("!Identifiers:"+annotation[1]) in header:
                        identifiers.append(annotation[1])
                        column2ident[annotation[1]] = int(len(header)+1)
                        header.append('!Identifiers:'+annotation[1])
                        value_row.append('')
                    if annotation[1] in identifiers:
                        value_row[column2ident[annotation[1]]-1] = annotation[0]
            except: pass
            compound.append(value_row)

        compound[1] = header
        compound_SB = compound[0]
        for row in compound[1:]:
            compound_SB.append('\t'.join(row))
        compound_SBtab = '\n'.join(compound_SB)
            
        return [compound_SBtab,'compound']

    def eventSBtab(self):
        '''
        Builds an Event SBtab.
        '''
        if len(self.model.getListOfEvents()) == 0:
            return False
            
        event    = [['!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Event" TableName="Event"'],['']]
        header   = ['!ID','!Name','!Assignments','!Trigger','!SBOterm','!Delay','!UseValuesFromTriggerTime']
        identifiers  = []
        column2ident = {}

        for eve in self.model.getListOfEvents():
            value_row = ['']*len(header)
            value_row[0] = eve.getId()
            value_row[1] = eve.getName()
            if eve.getNumEventAssignments() > 1:
                try:
                    eas = eve.getListOfEventAssignments()
                    ea_entry = ''
                    for ea in eas:
                        var       = ea.getVariable()
                        ea_e      = ea.getMath()
                        ea_entry += var+' = '+libsbml.formulaToL3String(ea_e)+' | '
                    value_row[2] = ea_entry[:-3]
                except: pass
            else:
                try:
                    eas = eve.getListOfEventAssignments()
                    for ea in eas:
                        var          = ea.getVariable()
                        vr           = ea.getMath()
                        value_row[2] = var+' = '+libsbml.formulaToL3String(vr)
                except: pass
            try:
                trigger      = eve.getTrigger().getMath()
                value_row[3] = libsbml.formulaToL3String(trigger)
            except: pass
            if str(eve.getSBOTerm()) != '-1': value_row[4] ='SBO:%.7d'%eve.getSBOTerm()
            try: value_row[5] = str(eve.getDelay())
            except: pass
            try: value_row[6] = str(eve.getUseValuesFromTriggerTime())
            except: pass
            try:
                annot_tuples = self.getAnnotations(eve)
                for i,annotation in enumerate(annot_tuples):
                    if not ("!Identifiers:"+annotation[1]) in header:
                        identifiers.append(annotation[1])
                        column2ident[annotation[1]] = int(len(header)+1)
                        header.append('!Identifiers:'+annotation[1])
                        value_row.append('')
                    if annotation[1] in identifiers:
                        value_row[column2ident[annotation[1]]-1] = annotation[0]
            except: pass
            event.append(value_row)

        event[1] = header
        event_SB = event[0]
        for row in event[1:]:
            event_SB.append('\t'.join(row))
        event_SBtab = '\n'.join(event_SB)
            
        return [event_SBtab,'event']

    def ruleSBtab(self):
        '''
        Builds a Rule SBtab.
        '''
        if len(self.model.getListOfRules()) == 0:
            return False
            
        rule     = [['!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Rule" TableName="Rule"'],['']]
        header   = ['!ID','!Name','!Formula','!Unit']
        identifiers  = []
        column2ident = {}

        for ar in self.model.getListOfRules():
            value_row = ['']*len(header)
            value_row[0] = ar.getId()
            value_row[1] = ar.getElementName()
            try:
                var          = ar.getVariable()
                vr           = ar.getMath()
                value_row[2] = var+' = '+libsbml.formulaToL3String(vr)
            except: pass
            try: value_row[3] = ar.getUnits()
            except: pass            
            try:
                annot_tuples = self.getAnnotations(ar)
                for i,annotation in enumerate(annot_tuples):
                    if not ("!Identifiers:"+annotation[1]) in header:
                        identifiers.append(annotation[1])
                        column2ident[annotation[1]] = int(len(header)+1)
                        header.append('!Identifiers:'+annotation[1])
                        value_row.append('')
                    if annotation[1] in identifiers:
                        value_row[column2ident[annotation[1]]-1] = annotation[0]
            except: pass
            rule.append(value_row)

        rule[1] = header
        rule_SB = rule[0]
        for row in rule[1:]:
            rule_SB.append('\t'.join(row))
        rule_SBtab = '\n'.join(rule_SB)
            
        return [rule_SBtab,'rule']

    def getAnnotations(self,element):
        '''
        extracts annotations from an SBML element.
        '''
        cvterms      = element.getCVTerms()
        annotation   = False
        urn          = False
        annot_tuples = []

        pattern2urn = {"CHEBI:\d+$":"obo.chebi",\
                       "C\d+$":"kegg.compound",\
                       "GO:\d{7}$":"obo.go",\
                       "((S\d+$)|(Y[A-Z]{2}\d{3}[a-zA-Z](\-[A-Z])?))$":"sgd",\
                       "SBO:\d{7}$":"biomodels.sbo",\
                       "\d+\.-\.-\.-|\d+\.\d+\.-\.-|\d+\.\d+\.\d+\.-|\d+\.\d+\.\d+\.(n)?\d+$":"ec-code",\
                       "K\d+$":"kegg.orthology",\
                       "([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9][A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$":"uniprot"}
        for i in range(element.getNumCVTerms()):
            cvterm   = cvterms.get(i)
            for j in range(cvterm.getNumResources()):
                resource = cvterm.getResourceURI(j)
                for pattern in pattern2urn.keys():
                    try:
                        search_annot = re.search(pattern,resource)
                        annotation   = search_annot.group(0)
                        urn          = pattern2urn[pattern]
                        annot_tuples.append([annotation,urn])
                        break
                    except: pass
                    try:
                        search_annot = re.search('identifiers.org/(.*)/(.*)',resource)
                        annotation   = search_annot.group(2)
                        urn          = search_annot.group(1)
                        annot_tuples.append([annotation,urn])
                    except: pass

        return annot_tuples

    def reactionSBtab(self):
        '''
        Builds a Reaction SBtab.
        '''
        reaction     = [['!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Reaction" TableName="Reaction"'],['']]
        if self.cd: header = ['!ID','!Name','!ReactionFormula','!ReactionFormulaStates','!Regulator','!KineticLaw','!SBOTerm','!IsReversible','!Notes','!LayerNotes','!Location']
        else:       header = ['!ID','!Name','!ReactionFormula','!Location','!Regulator','!KineticLaw','!SBOTerm','!IsReversible']
        identifiers  = []
        column2ident = {}
        for react in self.model.getListOfReactions():
            value_row = ['']*len(header)
            value_row[0] = react.getId()
            value_row[1] = react.getName()
            value_row[2] = self.makeSumFormula(react)
            if self.cd: value_row[3] = self.makeSumFormulaCD(react)
            else:
                try: value_row[3] = str(react.getCompartment())
                except: pass
            modifiers = react.getListOfModifiers()
            if len(modifiers)>1:
                modifier_list = ''
                for i,modifier in enumerate(modifiers):
                    try: name = self.extractNameAndState(self.id2object[modifier.getSpecies()])
                    except: name = modifier.getSpecies()
                    if i != len(react.getListOfModifiers())-1: modifier_list += name + '|'
                    else: modifier_list += name
                value_row[4] = modifier_list
            elif len(modifiers)==1:
                for modifier in modifiers:
                    try: name = self.extractNameAndState(self.id2object[modifier.getSpecies()])
                    except: name = modifier.getSpecies()
                    value_row[4] = name
            else: pass
            try: value_row[5] = react.getKineticLaw().getFormula()
            except: pass
            if str(react.getSBOTerm()) != '-1': value_row[6] ='SBO:%.7d'%react.getSBOTerm()
            try: value_row[7] = str(react.getReversible())
            except: pass
            if self.cd: 
                try: value_row[8] = str(self.rid2notes[react.getId()])
                except: pass
                try: value_row[9] = str(self.rid2layernotes[react.getId()])
                except: pass
                try: value_row[10] = str(react.getCompartment())
                except: pass
            try:
                annot_tuples = self.getAnnotations(react)
                for i,annotation in enumerate(annot_tuples):
                    if not ("!Identifiers:"+annotation[1]) in header:
                        identifiers.append(annotation[1])
                        column2ident[annotation[1]] = int(len(header))
                        header.append('!Identifiers:'+annotation[1])
                        value_row.append('')
                    if annotation[1] in identifiers:
                        value_row[column2ident[annotation[1]]] = annotation[0]
            except: pass
            reaction.append(value_row)

        reaction[1] = header
        reaction_SB = reaction[0]
        for row in reaction[1:]:
            reaction_SB.append('\t'.join(row))
        reaction_SBtab = '\n'.join(reaction_SB)
        
        return [reaction_SBtab,'reaction']

    def quantitySBtab(self):
        '''
        Builds a Quantity SBtab.
        '''
        pars = True
        if len(self.model.getListOfParameters()) == 0:
            pars = False
            for reaction in self.model.getListOfReactions():
                kinetic_law = reaction.getKineticLaw()
                if len(kinetic_law.getListOfParameters()) != 0: pars = True

        if not pars: return False
        
        quantity_SBtab = '!!SBtab SBtabVersion="1.0" Document="'+self.filename.rstrip('.xml')+'" TableType="Quantity" TableName="Quantity"\n!ID\t!SBML:parameter:id\t!Value\t!Unit\t!Description'
        identifiers = []
        the_rows    = ''

        for reaction in self.model.getListOfReactions():
            kinetic_law = reaction.getKineticLaw()
            if kinetic_law:
                value_row   = ''
                for parameter in kinetic_law.getListOfParameters():
                    value_row += parameter.getId()+'_'+reaction.getId()+'\t'
                    value_row += parameter.getId()+'\t'
                    value_row += str(parameter.getValue())+'\t'
                    try: value_row += parameter.getUnits()+'\t'
                    except: value_row += '\t'
                    value_row += 'local parameter\t'
                    #quantity_SBtab += value_row
                    try:
                        (annotation,urn) = self.getAnnotation(parameter)
                        if urn in identifiers: value_row += annotation+'\n'
                        else: value_row += '\n'
                        if not "!Identifiers:" in quantity_SBtab:
                            quantity_SBtab += '\t'+'!Identifiers:'+urn
                            identifiers.append(urn)
                    except:
                        value_row += '\n'
                the_rows += value_row

        for parameter in self.model.getListOfParameters():
            value_row = parameter.getId()+'\t'
            value_row += parameter.getId()+'\t'
            value_row += str(parameter.getValue())+'\t'            
            try: value_row += parameter.getUnits()+'\t'
            except: value_row += '\t'            
            value_row += 'global parameter\t'
            try:
                (annotation,urn) = self.getAnnotation(parameter)
                if urn in identifiers: value_row += annotation+'\n'
                else: value_row += '\n'
                if not "!Identifiers:" in quantity_SBtab:
                    quantity_SBtab += '\t'+'!Identifiers:'+urn
                    identifiers.append(urn)
            except:
                value_row += '\n'
            the_rows += value_row

        quantity_SBtab += '\n'
        quantity_SBtab += the_rows
            
        return [quantity_SBtab,'quantity']

    def makeSumFormula(self,reaction):
        '''
        Generates the reaction formula of a reaction from the list of products and list of reactants.

        Parameters
        ----------
        reaction : libsbml object reaction
           Single reaction object from the SBML file.
        '''
        sumformula = ''
        if self.cd: arrow = '-> '
        else: arrow = '<=> '

        for i,reactant in enumerate(reaction.getListOfReactants()):
            if self.cd: name = self.sid2sname[reactant.getSpecies()]
            else: name = reactant.getSpecies()
            if numpy.isnan(reactant.getStoichiometry()):
                sumformula += '1 ' + name
            elif reactant.getStoichiometry() != 1.0:
                sumformula += str(float(reactant.getStoichiometry())) + ' ' + name +' + '
            else:
                sumformula += name+' + '

        sumformula = sumformula[:-3]+' '+arrow
        if sumformula == '': sumformula += arrow
        
        for i,product in enumerate(reaction.getListOfProducts()):
            if self.cd: name = self.sid2sname[product.getSpecies()]
            else: name = reactant.getSpecies()
            if numpy.isnan(product.getStoichiometry()):
                sumformula += '1 ' + name
            elif product.getStoichiometry() != 1.0:
                sumformula += str(float(product.getStoichiometry())) + ' ' + name+' + '
            else:
                sumformula += name+' + '
            
        sumformula = sumformula[:-3]
        return sumformula

    def makeSumFormulaCD(self,reaction):
        '''
        Generates the reaction formula of a reaction from the list of products and list of reactants.

        Parameters
        ----------
        reaction : libsbml object reaction
           Single reaction object from the SBML file.
        '''
        sumformula = ''

        for i,reactant in enumerate(reaction.getListOfReactants()):
            try: name = self.extractNameAndState(self.id2object[reactant.getSpecies()])
            except: name = self.sid2sname[reactant.getSpecies()]
            if numpy.isnan(reactant.getStoichiometry()):
                sumformula += '1 ' + name
            elif reactant.getStoichiometry() != 1.0:
                sumformula += str(float(reactant.getStoichiometry())) + ' ' + name +' + '
            else:
                sumformula += name+' + '

        sumformula = sumformula[:-3]+' -> '
        if sumformula == '': sumformula += '-> '
        
        for i,product in enumerate(reaction.getListOfProducts()):
            try:
                name = self.extractNameAndState(self.id2object[product.getSpecies()])
            except:
                name = self.sid2sname[product.getSpecies()]
            if numpy.isnan(product.getStoichiometry()):
                sumformula += '1 ' + name
            elif product.getStoichiometry() != 1.0:
                sumformula += str(float(product.getStoichiometry())) + ' ' + name+' + '
            else:
                sumformula += name+' + '
            
        sumformula = sumformula[:-3]
        return sumformula
        

if __name__ == '__main__':

    try: sys.argv[1]
    except:
        print 'You have not provided input arguments. Please start the script by also providing an SBML file and an optional SBtab output filename: >python sbml2sbtab.py SBMLfile.xml Output'
        sys.exit()

    file_name  = sys.argv[1]
    try: output_name = sys.argv[2]+'.tsv'
    except: output_name = file_name[:-4]+'.tsv'

    reader     = libsbml.SBMLReader()
    sbml       = reader.readSBML(file_name)
    model      = sbml.getModel()
    Sbml_class = SBMLDocument(model,file_name)

    (sbtabs,warnings) = Sbml_class.makeSBtabs()

    #print warnings

    for sbtab in sbtabs:
        sbtab_name = output_name[:-4]+'_'+sbtab[1]+output_name[-4:]
        sbtab_file = open(sbtab_name,'w')
        sbtab_file.write(sbtab[0])
        sbtab_file.close()

    print 'The SBtab file/s have been successfully written to your working directory or chosen output path.'

