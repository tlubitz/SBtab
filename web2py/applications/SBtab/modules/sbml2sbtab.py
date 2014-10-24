#!/usr/bin/env python
import re, libsbml, numpy

allowed_sbtabs = ['Reaction','Compound','Compartment']

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

        #print sbml_model
        #sbml_modelx = reader.readSBML(sbml_model)
        
        #print 'tra',sbml_modelx.getModel()

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
        sbtabs = []

        for sbtab_type in allowed_sbtabs:
            function_name = 'self.'+sbtab_type.lower()+'SBtab()'
            sbtabs.append(eval(function_name))

        sbtabs = self.getRidOfNone(sbtabs)

        return sbtabs
        
    def getRidOfNone(self,sbtabs):
        '''
        remove empty SBtabs (if no values for an SBtab were provided by the SBML)
        '''
        new_tabs = []
        for element in sbtabs:
            if element != None:
                new_tabs.append(element)
        return new_tabs

    def enzymeSBtab(self):
        '''
        build an Enzyme SBtab
        '''
        enzyme_SBtab = '!!SBtab Version "0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Enzyme" TableName="Enzyme"\n!Enzyme\t!Name\t!CatalysedReaction\t!KineticLaw\t!SBOTerm\n'
        modifiers = []

        for reaction in self.model.getListOfReactions():
            counter = 0
            try:
                modifiers = reaction.getListOfModifiers()
                for modifier in modifiers:
                    value_row = ''
                    value_row += modifier.getSpecies()+'\t'
                    value_row += modifier.getElementName()+'\t'
                    value_row += reaction.getId()+'\t'
                    try: value_row += reaction.getKineticLaw().getName()+'\t'
                    except: value_row += '\t'
                    if str(modifier.getSBOTerm()) == '-1': value_row += 'No SBO term set in SBML.\n'
                    else: str(modifier.getSBOTerm())+'\n'
                    #try: value_row += str(modifier.getSBOTerm())+'\n'
                    #except: value_row += '\t\n'
                    enzyme_SBtab += value_row
                    counter += 1
            except:
                continue

        if counter>0: return [enzyme_SBtab,'enzyme']
        else: pass
        

    def compartmentSBtab(self):
        '''
        build a Compartment SBtab
        '''
        compartment_SBtab = '!!SBtab Version "0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Compartment" TableName="Compartment"\n!Compartment\t!Name\t!Size\t!Unit\t!SBOTerm\n'

        for compartment in self.model.getListOfCompartments():
            value_row = compartment.getId()+'\t'
            name = compartment.getName()
            if name == '': name = 'No name given in SBML'
            value_row += name+'\t'  
            try: value_row += str(compartment.getSize())+'\t'
            except: value_row += '\t'
            try: value_row += str(compartment.getUnits())+'\t'
            except: value_row += '\t'            
            if str(compartment.getSBOTerm()) == '-1': value_row += 'No SBO Term set in SBML.\n'
            else: str(compartment.getSBOTerm())+'\n'            
            #try: value_row += str(compartment.getSBOTerm())+'\n'
            #except: value_row += '\t\n'
            compartment_SBtab += value_row

        return [compartment_SBtab,'compartment']
        
    def compoundSBtab(self):
        '''
        builds a Compound SBtab
        '''
        compound_SBtab = '!!SBtab Version "0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Compound" TableName="Compound"\n!Compound\t!Name\t!Location\t!Charge\t!IsConstant\t!SBOTerm\t!InitialConcentration\n' #\t!MiriamID\n'

        for species in self.model.getListOfSpecies():
            value_row = species.getId()+'\t'
            value_row += species.getName()+'\t'
            try: value_row += species.getCompartment()+'\t'
            except: value_row += '\t'
            try: value_row += str(species.getCharge())+'\t'
            except: value_row += '\t'
            try: value_row += str(species.getConstant())+'\t'
            except: value_row += '\t'
            if str(species.getSBOTerm()) == '-1': value_row += 'No SBO term set in SBML.\t'
            else: str(species.getSBOTerm())+'\t'
            #try: value_row += str(species.getSBOTerm())+'\t'
            #except: value_row += '\t'
            try: value_row += str(species.getInitialConcentration())+'\n'
            except: value_row += '\t\n'
            #try: value_row += species.getAnnotation()+'\n'
            #except: value_row += '\t\n'
            
            compound_SBtab += value_row
            
        return [compound_SBtab,'compound']


    def reactionSBtab(self):
        '''
        builds a Reaction SBtab
        '''
        reaction_SBtab = '!!SBtab Version "0.8" Document="'+self.filename.rstrip('.xml')+'" TableType="Reaction" TableName="Reaction"\n!Reaction\t!Name\t!SumFormula\t!Location\t!Modifier\t!KineticLaw\t!SBOTerm\t!IsReversible\n'

        for reaction in self.model.getListOfReactions():
            value_row  = reaction.getId()+'\t'
            value_row += reaction.getName()+'\t'
            value_row += self.makeSumFormula(reaction)
            try: compartment = reaction.getCompartment()
            except: compartment = ''
            if compartment == '': compartment = 'No compartment given in SBML'
            value_row += compartment+'\t'
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
            try: kinlaw = reaction.getKineticLaw().getName()
            except: kinlaw = ''
            if kinlaw == '': kinlaw = 'No kinetic law given in SBML'
            value_row += kinlaw+'\t'          
            #try: value_row += reaction.getKineticLaw().getName()+'\t'
            #except: value_row += '\t'
            if str(reaction.getSBOTerm()) == '-1': value_row += 'No SBOterm set in SBML.\t'
            else: str(reaction.getSBOTerm())+'\t'
            #try: value_row += str(reaction.getSBOTerm())+'\t'
            #except: value_row += '\t'
            try: value_row += str(reaction.getReversible())+'\n'
            except: value_row += '\t\n'
            reaction_SBtab += value_row

        return [reaction_SBtab,'reaction']

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
