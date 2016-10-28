'''
Created on 15/08/2016

@author: monther
'''
import sys
from IgRepertoire.igRepUtils import writeClonoTypesToFile
from IgRepReporting.igRepPlots import plotSeqLenDist, \
    generateCumulativeLogo
import os
from IgRepAuxiliary.SeqUtils import createAlphabet, generateMotif

def generateDiversityReport(spectraTypes, clonoTypes, name, outDir, topClonotypes):    
    generateSpectraTypePlots(spectraTypes,  name, outDir)
    
    writeClonoTypesToFiles(clonoTypes, name, outDir, topClonotypes)
    
    generateClonoTypePlots(clonoTypes, name, outDir)
#     generateCDRandFRLogos()
    sys.stdout.flush()

def writeClonoTypesToFiles(clonoTypes, name, outDir, topClonotypes = 100):
    print("Clonotype files are being written out ... ")
    for k in clonoTypes.keys():
        writeClonoTypesToFile(clonoTypes[k], 
          outDir + name + ("_%s_clonotypes_%d.csv" % (k, topClonotypes)), 
          topClonotypes)

def generateSpectraTypePlots(spectraTypes,  name, outDir):
    for k in spectraTypes.keys():
        filename = outDir + name + ('_%s_spectratype.png' % (k))
        plotSeqLenDist(spectraTypes[k], name, filename, dna=False,
              seqName=k.upper(), normed=True, maxbins=20)
        if k == 'cdr3':
            filename = outDir + name + ('_%s_spectratype_no_outliers.png' % (k))
            plotSeqLenDist(spectraTypes[k], name, filename, dna=False,
              seqName=k.upper(), normed=True, maxbins=20, 
              removeOutliers= True)

def generateClonoTypePlots(clonoTypes, name, outDir):
    generateSeqLogosMotifs(clonoTypes, name, outDir, "protein")
    generateDiversityPlots(clonoTypes, name, outDir, "protein")

def generateDiversityPlots(clonoTypes, name, outDir, seqType = "protein"):
    pass
  
def generateSeqLogosMotifs(clonoTypes, name, outDir, seqType = "protein"):
    logosFolder = outDir + 'logos/'    
    if (not os.path.isdir(logosFolder)):
        os.system('mkdir ' + logosFolder)
    motifsFolder =  outDir + 'motifs/'   
    if (not os.path.isdir(motifsFolder)):
        os.system('mkdir ' + motifsFolder)
    regions = clonoTypes.keys()
    regions.sort()        
    print(seqType + " sequence logos are being generated .... ")  
    for region in regions: 
        print("\t" + region.upper())
        clonoType = clonoTypes[region]
        seqs = clonoType.keys()        
        weights = map(lambda x: clonoType[x], seqs)
        # Generate cumulative sequence logos using Toby's approach
        filename = logosFolder + name + ("_%s_cumulative_logo.png" % (region))        
        generateCumulativeLogo(seqs, weights, region, filename)
        # Generate sequence motif logos using weblogo                
        #generate logos without alignment
        ### SEQUENCES ARE WEIGHTED ??? HOW TO USE WEIGHTS
        ### SIMPLY REPEAT SEQUENCES OR FIND A WAY
        filename = motifsFolder + name + ("_%s_motif_logo.png" % (region))
        alphabet = createAlphabet(align=False, protein=True)
        m = generateMotif(seqs, region, alphabet, filename,  align = False,
                          protein = True, weights= weights)
        # generate  logos after alignment
        filename = motifsFolder + name + ("_%s_motif_aligned_logo.png" % (region))
        alphabet = createAlphabet(align=True, protein=True)
        m = generateMotif(seqs, region, alphabet, filename,  align = True,
                          protein = True, weights= weights)
    
    
#     
# def generateCDRandFRLogos(self):
# #         sampleName = self.readFile1.split('/')[-1].split("_")[0] + '_'  
# #         sampleName += self.readFile1.split('/')[-1].split("_")[-1].split('.')[0]
#     seqs = {}
#     for k in self.cloneSeqs.columns:
#         if k.startswith('cdr') :
#             seqs[k] = self.cloneSeqs[k].tolist()
#         if k.startswith('fr'):
#             seqs[k] = self.cloneSeqs[k].tolist()
#     # generate Toby's logos ?!?!
#     generateProteinLogos(seqs, self.outputDir + self.name + '_cdr_fr_Toby')
#     
#     # generate CDR/FR logos without alignment
#     generateMotifs(seqs, False, self.outputDir + self.name + '_cdr_fr',
#                    protein=True) 
#     # generate CDR/FR logos after alignment
#     generateMotifs(seqs, True,
#                 self.outputDir + self.name + '_cdr_fr_aligned',
#                 protein=True)
#     # generate CDR3 logos per  germline 
#     seqs = {}
#     vgenes = self.cloneSeqs["germline"].tolist()
#     vgenes = map(lambda x: x.split('*')[0], vgenes)
#     for vgene in set(vgenes):
#         seqs["cdr3_"+vgene.replace("/", "-")] = self.cloneSeqs.loc[map(lambda x: x == vgene, vgenes), "cdr3"].tolist()            
#     # generate Toby's logos ?!?!
#     generateProteinLogos(seqs, self.outputDir + self.name + '_cdr_Toby_gene')
#     # generate CDR/FR logos after alignment
#     generateMotifs(seqs, True,
#                 self.outputDir + self.name + '_cdr_gene_aligned',
#                 protein=True)
#     # generate CDR3 logos per family        
#     seqs = {}
#     vfams = map(lambda x: x.split('-')[0].split('/')[0], vgenes)
#     for vfam in set(vfams):
#         seqs["cdr3_"+vfam] = self.cloneSeqs.loc[map(lambda x: x == vgene, vgenes), "cdr3"].tolist()
#     # generate Toby's logos ?!?!
#     generateProteinLogos(seqs, self.outputDir + self.name + '_cdr_fr_Toby')
#     # generate CDR/FR logos after alignment
#     generateMotifs(seqs, True,
#                 self.outputDir + self.name + '_cdr_fr_aligned',
#                 protein=True)
#        
      
  
# quantify CDR sequence diversity      
          
#         if (not exists(self.outputDir + self.name + 
#                  '_Vdomain_diversity.png')):            
#     #         i = 0
#             VH = []
#             for (id, f1, c1, f2, c2, f3, c3, f4) in zip(self.cloneSeqs.index.tolist(),
#                                                         self.cloneSeqs['fr1'].tolist(),
#                                                           self.cloneSeqs['cdr1'].tolist(),
#                                                           self.cloneSeqs['fr2'].tolist(),
#                                                           self.cloneSeqs['cdr2'].tolist(),
#                                                           self.cloneSeqs['fr3'].tolist(),
#                                                           self.cloneSeqs['cdr3'].tolist(),
#                                                           self.cloneSeqs['fr4'].tolist()):           
#                 try:
#                     VH += [''.join([f1, c1, f2, c2, f3, c3, f4])]
#                 except:
#                     if (f4 is None or isnan(f4)):  # or c3 is None or isnan(c3):
#                         VH += [''.join([f1, c1, f2, c2, f3, c3])]
#                     else:
#                         print(id, f1, c1, f2, c2, f3, c3, f4)
# #                 i += 1
# #         print(i)
# #         sys.exit()
#             plotSeqDuplication([self.cloneSeqs['cdr1'].tolist(),
#                               self.cloneSeqs['cdr2'].tolist(),
#                               self.cloneSeqs['cdr3'].tolist(),
#                               VH],
#                              self.outputDir + self.name + 
#                      '_Vdomain__Vdomain_ication.png',
#                              ['CDR1', 'CDR2', 'CDR3', 'V Domain'],
#                              'Duplication of V Domain Sequences')
#             plotSeqDiversity([self.cloneSeqs['cdr1'].tolist(),
#                           self.cloneSeqs['cdr2'].tolist(),
#                           self.cloneSeqs['cdr3'].tolist(),
#                           VH],
#                          self.outputDir + self.name + 
#                  '_Vdomain_diversity.png',
#                          ['CDR1', 'CDR2', 'CDR3', 'V Domain'],
#                          'Diversity of V Domain Sequences')
#         gc.collect()
#         
#         plotSeqDuplication([self.cloneSeqs['cdr1'].tolist(),
#                           self.cloneSeqs['cdr2'].tolist(),
#                           self.cloneSeqs['cdr3'].tolist()
#                           ],
#                          self.outputDir + self.name + 
#                  '_cdr_duplication.png',
#                          ['CDR1', 'CDR2', 'CDR3'],
#                          'Duplication of CDR Sequences')        
#         
#         plotSeqDiversity([self.cloneSeqs['cdr1'].tolist(),
#                           self.cloneSeqs['cdr2'].tolist(),
#                           self.cloneSeqs['cdr3'].tolist()
#                         ],
#                          self.outputDir + self.name + 
#                  '_cdr_diversity.png',
#                          ['CDR1', 'CDR2', 'CDR3'],
#                          'Diversity of CDR Sequences')
#         gc.collect()
  
  
# Quantify FR sequence diversity
#         plotSeqDuplication([self.cloneSeqs['fr1'].tolist(),
#                           self.cloneSeqs['fr2'].tolist(),
#                           self.cloneSeqs['fr3'].tolist(),
#                           self.cloneSeqs['fr4'].tolist()],
#                          self.outputDir + self.name + 
#                  '_fr_duplication.png',
#                          ['FR1', 'FR2', 'FR3', 'FR4'],
#                          'Duplication of FR Sequences')
#         gc.collect()
#         plotSeqDiversity([self.cloneSeqs['fr1'].tolist(),
#                           self.cloneSeqs['fr2'].tolist(),
#                           self.cloneSeqs['fr3'].tolist(),
#                           self.cloneSeqs['fr4'].tolist()],
#                          self.outputDir + self.name + 
#                  '_fr_diversity.png',
#                          ['FR1', 'FR2', 'FR3', 'FR4'],
#                          'Diversity of FR Sequences')


# quantify V domain sequence diversity                
#         if (not exists(self.outputDir + self.name + 
#                  '_Vdomain_duplication_family.png')):
#             print("Grouping V domain sequences per family ...")
#             VH = {}
#     #         i = 0
#             ighvs = map(lambda x : x.split('-')[0].split('/')[0], self.cloneSeqs['germline'].tolist())
#             for ighv in set(ighvs):
#                 VH[ighv] = []
#             for (ighv, f1, c1, f2, c2, f3, c3, f4) in zip(ighvs,
#                                                         self.cloneSeqs['fr1'].tolist(),
#                                                           self.cloneSeqs['cdr1'].tolist(),
#                                                           self.cloneSeqs['fr2'].tolist(),
#                                                           self.cloneSeqs['cdr2'].tolist(),
#                                                           self.cloneSeqs['fr3'].tolist(),
#                                                           self.cloneSeqs['cdr3'].tolist(),
#                                                           self.cloneSeqs['fr4'].tolist()):           
#                 try:
#                     VH[ighv].append(''.join([f1, c1, f2, c2, f3, c3, f4]))
#                 except:
#                     if (f4 is None or isnan(f4)):  # or c3 is None or isnan(c3):
#                         VH += [''.join([f1, c1, f2, c2, f3, c3])]
#                     else:
#                         print(id, f1, c1, f2, c2, f3, c3, f4)
#             ighvs = VH.keys()
#             ighvs.sort()        
#             
#             plotSeqDuplication(map(lambda x:VH[x], ighvs),
#                              self.outputDir + self.name + 
#                      '_Vdomain_duplication_family.png',
#                              ighvs,
#                              'Duplication of V Domain Sequences Per Family', True)
#             gc.collect()