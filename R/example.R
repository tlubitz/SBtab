####
# This file exemplifies how SBtab files can be opened in the R framework
# without employing Python code. The files sbtab_read_tsv and one_or_many
# are pure R code.
####

source("sbtab_read_tsv.R")
source("one_or_many.R")
y1 <- sbtab_read_tsv("../sbtab_examples/LacOperon_Gene.csv")
print(sprintf("header = '%s'", y1$header))

y2 <- one_or_many("../sbtab_examples/ecoli_ccm_aerobic_ModelData.tsv")
concentration_sbtab = y2$sbtabs[[9]]

print(sprintf("compound = '%s', %f <= concentration <= %f",
             concentration_sbtab$Compound[1],
             as.numeric(concentration_sbtab$`Concentration:Min`[1]),
             as.numeric(concentration_sbtab$`Concentration:Max`[1])))
