#!/usr/bin/env python
import libsbml, numpy

allowed_sbtabs = ['Reaction','Compound','Compartment','Quantity']

class ConversionError(Exception):
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
        initalize SBtab document, check it for SBtabs
        '''
        #reader      = libsbml.SBMLReader()
        #sbml_modelx = reader.readSBML(sbml_model)
        #print sbml_modelx.getModel()

        self.model    = sbml_model
        self.filename = filename
        if not self.filename.endswith('.xml'): 
            raise ConversionError('The given file format is not supported: '+self.filename)

        #for testing purposes:
        '''
        sbtabs = self.makeSBtabs()
        for sbtab in sbtabs:
            print sbtab
            print '\n\n\n'
        '''

    def makeSBtabs(self):
        '''
        generates the SBtab files
        '''
        self.warnings = []
        sbtabs        = []

        self.testForInconvertibles()

        for sbtab_type in allowed_sbtabs:
            function_name = 'self.'+sbtab_type.lower()+'SBtab()'
            sbtabs.append(eval(function_name))

        sbtabs = self.getRidOfNone(sbtabs)

        return sbtabs,self.warnings

    def testForInconvertibles(self):
        '''
        some SBML entities cannot be converted to SBML. so we add warnings to tell the user.
        '''
        try:
            rules = self.model.getListOfRules()
            if len(rules)>0:
                self.warnings.append('The SBML model contains rules. These cannot be translated to the SBtab files.')
        except: pass
        try:
            events = self.model.getListOfEvents()
            if len(events)>0:
                self.warnings.append('The SBML model contains events. These cannot be translated to the SBtab files.')
        except: pass
        
        
    def getRidOfNone(self,sbtabs):
        '''
        remove empty SBtabs (if no values for an SBtab were provided by the SBML)
        '''
        new_tabs = []
        for element in sbtabs:
            if element != None:
                new_tabs.append(element)
        return new_tabs

    def compartmentSBtab(self):
        '''
        build a Compartment SBtab
        '''
        compartment_SBtab = '!!SBtab SBtabVersion="0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Compartment" TableName="Compartment"\n!Compartment\t!Name\t!Size\t!Unit\t!SBOTerm'
        identifiers = []
        the_rows    = ''

        for compartment in self.model.getListOfCompartments():
            value_row = compartment.getId()+'\t'
            try: value_row += str(compartment.getName())+'\t'
            except: value_row += '\t'
            try: value_row += str(compartment.getSize())+'\t'
            except: value_row += '\t'
            try: value_row += str(compartment.getUnits())+'\t'
            except: value_row += '\t'           
            if str(compartment.getSBOTerm()) == '-1': value_row += '\t'
            else: value_row += str(compartment.getSBOTerm())+'\t'            
            #try: value_row += str(compartment.getSBOTerm())+'\n'
            #except: value_row += '\t\n'

            try:
                (annotation,urn) = self.getAnnotation(compartment)
                if urn in identifiers: value_row += annotation+'\n'
                else: value_row += '\n'
                if not "!Identifiers:" in compartment_SBtab:
                    compartment_SBtab += '\t'+'!Identifiers:'+urn
                    identifiers.append(urn)
            except:
                value_row += '\n'
            the_rows += value_row

        compartment_SBtab += '\n'
        compartment_SBtab += the_rows
            
        return [compartment_SBtab,'compartment']
        
    def compoundSBtab(self):
        '''
        builds a Compound SBtab
        '''
        compound_SBtab = '!!SBtab SBtabVersion="0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Compound" TableName="Compound"\n!Compound\t!Name\t!Location\t!Charge\t!IsConstant\t!SBOTerm\t!InitialConcentration'
        identifiers = []
        the_rows    = ''

        for species in self.model.getListOfSpecies():
            value_row = species.getId()+'\t'
            value_row += species.getName()+'\t'
            try: value_row += species.getCompartment()+'\t'
            except: value_row += '\t'
            try: value_row += str(species.getCharge())+'\t'
            except: value_row += '\t'
            try: value_row += str(species.getConstant())+'\t'
            except: value_row += '\t'
            if str(species.getSBOTerm()) == '-1': value_row += '\t'
            else: value_row += str(species.getSBOTerm())+'\t'
            try: value_row += str(species.getInitialConcentration())+'\t'
            except: value_row += '\t'

            #this is a little bit more tricky: try and get an annotation from an element:
            try:
                (annotation,urn) = self.getAnnotation(species)
                if urn in identifiers: value_row += annotation+'\n'
                else: value_row += '\n'
                if not "!Identifiers:" in compound_SBtab:
                    compound_SBtab += '\t'+'!Identifiers:'+urn
                    identifiers.append(urn)
            except:
                value_row += '\n'
            the_rows += value_row

        compound_SBtab += '\n'
        compound_SBtab += the_rows
            
        return [compound_SBtab,'compound']


    def getAnnotation(self,element):
        '''
        try and extract an annotation from an SBML element. PS: this is tricky stuff.
        '''
        cvterms    = element.getCVTerms()
        annotation = False
        urn        = False       

        pattern2urn = {"CHEBI:\d+$":"obo.chebi",\
                       "C\d+$":"kegg.compound",\
                       "GO:\d{7}$":"obo.go",\
                       "((S\d+$)|(Y[A-Z]{2}\d{3}[a-zA-Z](\-[A-Z])?))$":"obo.sgd",\
                       "SBO:\d{7}$":"biomodels.sbo",\
                       "\d+\.-\.-\.-|\d+\.\d+\.-\.-|\d+\.\d+\.\d+\.-|\d+\.\d+\.\d+\.(n)?\d+$":"ec-code",\
                       "K\d+$":"kegg.orthology",\
                       "([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9][A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$":"obo.uniprot"}#,\
                       #"\d+$":"taxonomy"}

        #for i in range(element.getNumCVTerms()):
        cvterm   = cvterms.get(0)
        resource = cvterm.getResourceURI(0)
        #now try ALL the annotation identification patterns:
        for pattern in pattern2urn.keys():
            try:
                search_annot = re.search(pattern,resource)
                annotation   = search_annot.group(0)
                urn = pattern2urn[pattern]
                break
            except: pass

        if urn == False:
            try:
                search_annot = re.search('identifiers.org/(.*)/(.*)',resource)
                annotation   = search_annot.group(2)
                urn          = search_annot.group(1)
            except: pass
            
        return (annotation,urn)

    def reactionSBtab(self):
        '''
        builds a Reaction SBtab
        '''
        
        reaction_SBtab = '!!SBtab SBtabVersion="0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Reaction" TableName="Reaction"\n!Reaction\t!Name\t!SumFormula\t!Location\t!Regulator\t!KineticLaw\t!SBOTerm\t!IsReversible'
        identifiers = []
        the_rows    = ''

        for reaction in self.model.getListOfReactions():
            value_row  = reaction.getId()+'\t'
            value_row += reaction.getName()+'\t'
            value_row += self.makeSumFormula(reaction)+'\t'
            try: compartment = reaction.getCompartment()+'\t'
            except: compartment = '\t'
            #try: value_row += reaction.getCompartment()+'\t'
            #except: value_row += '\t'
            modifiers = reaction.getListOfModifiers()
            if len(modifiers)>1:
                modifier_list = ''
                for i,modifier in enumerate(modifiers):
                    if i != len(reaction.getListOfModifiers())-1: modifier_list += modifier.getSpecies() + '|'
                    else: modifier_list += modifier.getSpecies() + '\t'
                value_row += modifier_list
            elif len(modifiers)==1:
                for modifier in modifiers: value_row += modifier.getSpecies()+'\t'
            else: value_row += '\t'
            try: kinlaw = reaction.getKineticLaw().getFormula()
            except: kinlaw = ''
            if kinlaw == '': kinlaw = ''
            value_row += kinlaw+'\t'          
            #try: value_row += reaction.getKineticLaw().getName()+'\t'
            #except: value_row += '\t'
            if str(reaction.getSBOTerm()) == '-1': value_row += '\t'
            else: value_row += str(reaction.getSBOTerm())+'\t'
            #try: value_row += str(reaction.getSBOTerm())+'\t'
            #except: value_row += '\t'
            try: value_row += str(reaction.getReversible())+'\t'
            except: value_row += '\t'
            try:
                (annotation,urn) = self.getAnnotation(reaction)
                if urn in identifiers: value_row += annotation+'\n'
                else: value_row += '\n'
                if not "!Identifiers:" in reaction_SBtab:
                    reaction_SBtab += '\t'+'!Identifiers:'+urn
                    identifiers.append(urn)
            except:
                value_row += '\n'
            the_rows += value_row

        reaction_SBtab += '\n'
        reaction_SBtab += the_rows

        return [reaction_SBtab,'reaction']

    def quantitySBtab(self):
        '''
        builds a Quantity SBtab
        '''
        quantity_SBtab = '!!SBtab SBtabVersion="0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Quantity" TableName="Quantity"\n!Quantity\t!SBML:parameter:id\t!Value\t!Unit\t!Description'
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
        generates the sum formula of a reaction from the list of products and list of reactants
        '''
        sumformula = ''
        id2name    = {}
        
        for species in self.model.getListOfSpecies():
            id2name[species.getId()] = species.getName()

        for i,reactant in enumerate(reaction.getListOfReactants()):
            if i != len(reaction.getListOfReactants())-1:
                if reactant.getStoichiometry() != 1.0:
                    sumformula += str(int(reactant.getStoichiometry())) + ' ' + reactant.getSpecies()+' + '
                else:
                    sumformula += reactant.getSpecies()+' + '
            else:
                if numpy.isnan(reactant.getStoichiometry()):
                    sumformula += '1 ' + reactant.getSpecies() + ' <=> '
                elif reactant.getStoichiometry() != 1.0:
                    sumformula += str(int(reactant.getStoichiometry())) + ' ' + reactant.getSpecies()+' <=> '
                else:
                    sumformula += reactant.getSpecies()+' <=> '
        for i,product in enumerate(reaction.getListOfProducts()):
            if i != len(reaction.getListOfProducts())-1:
                if product.getStoichiometry() != 1.0:
                    sumformula += str(int(product.getStoichiometry())) + ' ' + product.getSpecies()+' + '
                else:
                    sumformula += product.getSpecies()+' + '
            else:
                if numpy.isnan(product.getStoichiometry()):
                    sumformula += '1 ' + product.getSpecies() + ' <=> '
                elif product.getStoichiometry() != 1.0:
                    sumformula += str(int(product.getStoichiometry())) + ' ' + product.getSpecies()+'\t'
                else:
                    sumformula += product.getSpecies()+'\t'
            
        #if there is no product in the reaction (e.g. influxes), don't forget the tab
        if len(reaction.getListOfProducts()) < 1:
            sumformula += '\t'

        return sumformula
        

if __name__ == '__main__':
    #sbml_model = open('teusink.xml','r')
    reader = libsbml.SBMLReader()
    sbml   = reader.readSBML('yeast_7.00.xml')
    model  = sbml.getModel()
    sbml_class = SBMLDocument(model,'yeast_7.00.xml')


    reactions = sbml_class.reactionSBtab()
    bla = open('yeast.tsv','wr')
    for row in reactions:
        bla.write(row)

    bla.close()
