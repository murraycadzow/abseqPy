
import numpy as np
from os.path import exists
import os
import sys
from Bio import SeqIO, AlignIO
from pandas.core.frame import DataFrame
from numpy import isnan
from Bio.SeqRecord import SeqRecord
from config import CLUSTALOMEGA, MEM_GB
from Bio.Align.Applications._Clustalw import ClustalwCommandline
from Bio.Seq import Seq
from collections import Counter
from Bio.pairwise2 import align, format_alignment
from Bio.SubsMat import MatrixInfo as matlist
import re
from IgRepReporting.igRepPlots import plotDist

def fastq2fasta(fastqFile, outputDir):
    # FASTQ to FASTA
# awk 'NR % 4 == 1 {print ">" $0 } NR % 4 == 2 {print $0}' my.fastq > my.fasta
    filename = fastqFile.split('/')[-1]    
    seqOut = outputDir + "seq/"
    if (not os.path.isdir(seqOut)):
        os.system("mkdir " + seqOut)
    filename = seqOut + filename.replace(filename.split('.')[-1], 'fasta')
    if exists(filename):
        print ("\tThe FASTA file was found!")
        return filename
    print("\t" + fastqFile.split('/')[-1]  + " is being converted into FASTA ...")
    command = ("awk 'NR % 4 == 1 {sub(\"@\", \"\", $0) ; print \">\" $0} NR % 4 == 2 "
               "{print $0}' " + fastqFile + " > " + filename
               )
    
    os.system(command)
    return filename 

def runIgblastn(blastInput, chain, threads = 8, db='$IGBLASTDB'):
    # Run igblast on a fasta file  
      
    blastOutput = blastInput.replace('.' + blastInput.split('.')[-1], '.out')
    if (exists(blastOutput)):
        print("\tBlast results were found ... " + blastOutput.split("/")[-1])
        return blastOutput 
    print('\tRunning igblast ... ' + blastInput.split("/")[-1])
    if (chain == 'hv'):
        command = ("igblastn -germline_db_V " + db+"/imgt_human_ighv -germline_db_J " 
                   "" + db+"/imgt_human_ighj -germline_db_D " + db+"/imgt_human_ighd -domain_system imgt "
                   "-query %s -organism human -auxiliary_data optional_file/human_gl.aux "  
                   "-show_translation -extend_align5end -outfmt 7 -num_threads %d -out %s"
                   )
    elif (chain == 'kv'):
        command = ("igblastn -germline_db_V " + db+"/imgt_human_igkv -germline_db_J " 
                   "" + db+"/imgt_human_igkj -germline_db_D " + db+"/imgt_human_ighd -domain_system imgt "
                   "-query %s -organism human -auxiliary_data optional_file/human_gl.aux "  
                   "-show_translation -extend_align5end -outfmt 7 -num_threads %d -out %s"
                   )
    elif (chain == 'lv'):
        command = ("igblastn -germline_db_V " + db+"/imgt_human_iglv -germline_db_J " 
                   "" + db+"/imgt_human_iglj -germline_db_D " + db+"/imgt_human_ighd -domain_system imgt "
                   "-query %s -organism human -auxiliary_data optional_file/human_gl.aux "  
                   "-show_translation -extend_align5end -outfmt 7 -num_threads %d -out %s"
                   )
    else:
        print('ERROR: unsupported chain type.')     
        sys.exit()   
        
    os.system(command % (blastInput, threads, blastOutput))
    return blastOutput

def runIgblastp(blastInput, chain, threads = 8, db='$IGBLASTDB'):
    # Run igblast on a fasta file        
    blastOutput = blastInput.replace('.' + blastInput.split('.')[-1], '.out')
    if (exists(blastOutput)):
        print("\tBlast results were found ... " + blastOutput.split("/")[-1])
        return blastOutput 
    print('\tRunning igblast ... ' + blastInput.split("/")[-1])
    if (chain == 'hv'):
        command = ("igblastp -germline_db_V " + db+"/imgt_human_ighv_p " 
                   "-domain_system imgt "
                   "-query %s -organism human "  
                   "-outfmt 7 -extend_align5end -num_threads %d -out %s"
                   )
    elif (chain == 'kv'):
        command = ("igblastp -germline_db_V " + db+"/imgt_human_igkv_p " 
                   "-domain_system imgt "
                   "-query %s -organism human "  
                   "-outfmt 7 -extend_align5end -num_threads %d -out %s"
                   )
    elif (chain == 'lv'):
        command = ("igblastp -germline_db_V " + db+"/imgt_human_iglv_p " 
                   "-domain_system imgt "
                   "-query %s -organism human "  
                   "-outfmt 7 -extend_align5end -num_threads %d -out %s"
                   )
    else:
        print('ERROR: unsupported chain type.')     
        sys.exit() 
        
    
    os.system(command % (blastInput, threads, blastOutput))
    return blastOutput


def writeCountsToFile(dist, filename):
    # This function prints the distribution counts into a text file
    with open(filename, 'w') as out:
        out.write('IGHV Class, Count, Proportion \n')
        total = sum(dist.values()) * 1.0
        for k in sorted(dist, key=dist.get, reverse=True):
            out.write(str(k) + ',' + `dist[k]` + ',' + ("%.2f" % (dist[k] / total * 100)) + '\n')
        out.write('TOTAL, ' + `total` + ', 100 ')
    print("A text file has been created ... " + filename.split("/")[-1])


def findBestAlignment(seq, query, dna=False, offset=0, show=False):
    if not dna:
        alignments = align.localds(seq.replace('*', 'X'), query, matlist.blosum62,-100, -100)
    else:
        alignments = align.localms(seq, query, 1,-2, -2, -2)
    
#     print(seq, query, alignments)
    scores = [a[2] for a in alignments]
    if (len(scores) == 0):
#         print(seq, query, alignments)
#         raise
        return -1, -1, True
    best = scores.index(max(scores))
    if show:
        print(format_alignment(*alignments[best]))
        print(alignments[best])
    # return alignment start and end
    start = int(offset + alignments[best][-2] + 1)
    end = int(offset + alignments[best][-1])
    gapped = False  
    if '-' in alignments[best][0]:
        start -= alignments[best][0][:(alignments[best][-2]+1)].count('-')
        end -= alignments[best][0][:(alignments[best][-1]+1)].count('-')
        gapped = True
    return start, end, gapped # 1-based

'''
    Extract a protein fragment from a protein sequence based on DNA positions
    start and end are 1-based
'''
def extractProteinFrag(protein, start, end, offset=0, trimAtStop=False):
    if (np.isnan(start) or np.isnan(end)):
        return ''
    if (start != -1 and end != -1 and end - start < 1):
        return ''
    # start and end are 1-based positions
    start = (start - offset) if start != -1 else start
    end = (end - offset) if end != -1 else end
    try:        
        if (start != -1):
            s = int((start  - 1 ) / 3)# 0-based
        else:
            s = 0
        if end != -1:
            e = int(end  / 3) # 1-based
        else:
            e = len(protein)
        if (s+1) < e:        
            frag = protein[s:e]
        elif (s + 1) == e:
            frag = protein[s]
        else:            
            return ''       
        if trimAtStop and ('*' in frag):
            frag = frag[:frag.index('*')]
        return frag
    except:
        print("ERROR at Extract Protein Fragment",protein, start, end)
        return None

def extractCDRsandFRsProtein(protein, qsRec, offset):
    try:
        seqs = []
        newProtein = ""
        # Extract protein sequence of FR1             
        seqs.append(extractProteinFrag(protein, qsRec['fr1.start'], qsRec['fr1.end'], offset))
        # Extract protein sequence of CDR1
        seqs.append(extractProteinFrag(protein, qsRec['cdr1.start'], qsRec['cdr1.end'], offset))
        # Extract protein sequence of FR2
        seqs.append(extractProteinFrag(protein, qsRec['fr2.start'], qsRec['fr2.end'], offset))
        # Extract protein sequence of CDR2
        seqs.append(extractProteinFrag(protein, qsRec['cdr2.start'], qsRec['cdr2.end'], offset))
        # Extract protein sequence of FR3
        seqs.append(extractProteinFrag(protein, qsRec['fr3.start'], qsRec['fr3.end'], offset))
        # Extract protein sequence of CDR3 and FR4
        seqs.append(extractProteinFrag(protein, qsRec['cdr3.start'], qsRec['cdr3.end'], offset))
        seqs.append(extractProteinFrag(protein, qsRec['fr4.start'], qsRec['fr4.end'], offset))
        # check whether FR and CDR sequences were extracted correctly
        newProtein = ''.join(seqs)
        assert newProtein in protein
    except Exception as e:            
#         print("ERROR at partitioning the protein sequence: ")
#         print (protein, newProtein, seqs, offset)  
#         raise e
        raise Exception("ERROR at partitioning the protein sequence: ")
    return (newProtein, seqs)

def extractCDRsandFRsDNA(dna, qsRec):
    try:
        seqs = []
        newDna = ""
        seqs.append(dna[int(qsRec['fr1.start']-1):int(qsRec['fr1.end'])])
        seqs.append(dna[int(qsRec['cdr1.start']-1):int(qsRec['cdr1.end'])])
        seqs.append(dna[int(qsRec['fr2.start']-1):int(qsRec['fr2.end'])])
        seqs.append(dna[int(qsRec['cdr2.start']-1):int(qsRec['cdr2.end'])])
        seqs.append(dna[int(qsRec['fr3.start']-1):int(qsRec['fr3.end'])])
        if (isnan(qsRec['cdr3.start']) or isnan(qsRec['cdr3.end']) or 
            qsRec['cdr3.end'] - qsRec['cdr3.start'] < 0):
            seqs.append('')
        else:
            seqs.append(dna[int(qsRec['cdr3.start']-1):int(qsRec['cdr3.end'])])
        if isnan(qsRec['fr4.start']) or isnan(qsRec['fr4.end']):
            seqs.append('')
        else:
            seqs.append(dna[int(qsRec['fr4.start']-1):int(qsRec['fr4.end'])])
        newDna = ''.join(seqs)
        assert newDna in dna
    except Exception as e:            
#         print("ERROR at partitioning the nucleotide sequence: ")
#         print (dna, newDna, seqs)  
#         raise e
        raise Exception("ERROR at partitioning the nucleotide sequence: ")
    return seqs
        
    
def mergeReads(readFile1, readFile2, threads=3, merger='leehom', outDir="./"):    
    seqOut = outDir + "seq/"
    if (not os.path.isdir(seqOut)):
        os.system("mkdir " + seqOut)
    readFile = readFile1.split("/")[-1]
    outputPrefix = seqOut + readFile.replace("_" + readFile.split('_')[-1], '')    
    mergedFastq = "" 
    if (merger == 'pear'):        ### MERGE using PEAR            
        mergedFastq = outputPrefix + '.assembled.fastq'
        if (not exists(mergedFastq)):
            print("%s and %s are being merged ..." % (readFile1.split('/')[-1]
                                              , readFile2.split('/')[-1])) 
            command = "pear -f %s -r %s -o %s -j %d -v 15 -n 350"
            os.system(command % (readFile1, readFile2, outputPrefix, threads))
            #os.system("mv %s.* %s" % (outputPrefix, seqOut))            
        else:
            print(".../" + mergedFastq.split("/")[-1] + ' was found!')
    elif (merger == 'leehom'):        
        mergedFastq = outputPrefix + '.fq'
        if (not exists(mergedFastq)):
            print("%s and %s are being merged ..." % (readFile1.split('/')[-1]
                                              , readFile2.split('/')[-1])) 
            command = "leeHom -fq1 %s -fq2 %s -fqo %s --ancientdna --verbose"
            os.system(command % (readFile1, readFile2, outputPrefix))
            os.system('gunzip ' + mergedFastq + '.gz')
            #os.system("mv %s.* %s" % (outputPrefix, seqOut))
            #os.system("mv %s_r* %s" % (outputPrefix, seqOut))
        else:
            print(".../" + mergedFastq.split("/")[-1] + ' was found!')
    elif (merger == 'flash'):        
        mergedFastq = outputPrefix + '.extendedFrags.fastq'
        outputPrefix = outputPrefix.split("/")[-1]
        if (not exists(mergedFastq)):
            print("%s and %s are being merged ..." % (readFile1.split('/')[-1]
                                              , readFile2.split('/')[-1])) 
            # the merger params souldn't be hardcoded
            command = "flash %s %s -t %d -o %s -r 300 -f 450 -s 50"            
            os.system(command % (readFile1, readFile2, threads, outputPrefix))
            os.system("mv %s.* %s" % (outputPrefix, seqOut))            
        else:
            print(".../" + mergedFastq.split("/")[-1] + ' was found!')
#     elif (merger == 'seqprep'):
#         ### MERGE using SeqPrep 
#         mergedFastq = readFile1.replace(readFile1.split('_')[-1], 'merged.fastq.gz')
#         unmerged1 = readFile1.replace('.fastq', '_unmerged.fastq.gz')
#         unmerged2 = readFile2.replace('.fastq', '_unmerged.fastq.gz')
#         aligns = readFile1.replace(readFile1.split('_')[-1], 'aligns.txt.gz')
#         command = "SeqPrep -f %s -r %s -s %s -1 %s -2 %s -E %s"   
#         os.system(command % (readFile1, readFile2, mergedFastq, 
#                              unmerged1, unmerged2, aligns))
#         os.system("gunzip " + mergedFastq)
#         mergedFastq = mergedFastq.replace('.gz', '')
#         ### END MERGE using SeqPrep
    else:
        raise Exception("Uknowne short reads merger is selected")
        
    return os.path.abspath(mergedFastq)


def writeTableIntoFile(table, filename):
    df = DataFrame(table)
    df.to_csv(filename, sep='\t', header=True, index=True)    
    print("Text file has been written to " + filename)

def writeListToFile(items, filename):
    out = open(filename, 'w')
    out.write("\n".join(items))
    out.close()

def loadIGVSeqsFromFasta(filename):
    ighvSeqs = {}
    for rec in SeqIO.parse(filename, 'fasta'): 
        ighv = rec.id.split('|')[1].strip()
        if (ighvSeqs.get(ighv, None) is None):
            ighvSeqs[ighv] = []
        ighvSeqs[ighv].append(str(rec.seq))
        
    return ighvSeqs
                
def compressSeqGeneLevel(seqDict):    
    geneLevel = {}
    for ighv in seqDict.keys():
        gene = ighv.split('*')[0]
        if (geneLevel.get(gene, None) is None):
            geneLevel[gene] = []
        geneLevel[gene] += seqDict[ighv]
    return geneLevel

def compressSeqFamilyLevel(seqDict):    
    familyLevel = {}
    for ighv in seqDict.keys():
        fam = ighv.split('-')[0].split('/')[0]
        if (familyLevel.get(fam, None) is None):
            familyLevel[fam] = []
        familyLevel[fam] += seqDict[ighv]
    return familyLevel

def compressCountsGeneLevel(countsDict):
    geneLevel = Counter()
    for k in countsDict.keys():
        ksub = k.split('*')[0]
        geneLevel[ksub] = geneLevel.get(ksub, 0) + countsDict[k]
    return geneLevel

def writeCountsCategoriesToFile(countsVariant, sampleName, filePrefix, title=''):
    writeCountsToFile(countsVariant,
            filePrefix + 'variant.csv')
    # gene level
    countsVariant = compressCountsGeneLevel(countsVariant)
    writeCountsToFile(countsVariant,
        filePrefix + 'gene.csv')
    plotDist(countsVariant, sampleName, 
             filePrefix + 'gene.png', 
             title)
    # family level
    countsVariant = compressCountsFamilyLevel(countsVariant)
    writeCountsToFile(countsVariant,
        filePrefix + 'family.csv')
    plotDist(countsVariant, sampleName, 
             filePrefix + 'family.png',
             title)
            
def compressCountsFamilyLevel(countsDict):
    familyLevel = Counter()
    for k in countsDict.keys():
        ksub = k.split('-')[0].split('/')[0].rstrip('D')
        familyLevel[ksub] = familyLevel.get(ksub, 0) + countsDict[k]
    return familyLevel
            
'''
    perform multiple sequence alignment using CLUSTAL
'''
def alignListOfSeqs(signals):
    L = map(len, signals)
    print("\t\t%d sequences are being aligned using CLUSTAL-OMEGA (L in [%d, %d])... " % (len(L), min(L), max(L)))
    tempSeq = "csl_temp_seq.fasta"
    tempAlign = tempSeq.replace('.fasta', '.aln')
    seqs = []
    for i in range(len(signals)):
        seqs.append(SeqRecord(Seq(signals[i]), id='seq' + `i`))
    SeqIO.write(seqs, tempSeq, 'fasta')
    clustalw = ClustalwCommandline(CLUSTALOMEGA, infile=tempSeq, 
                    outfile=tempAlign)
    stdout, stderr = clustalw() 
    
    alignment = AlignIO.read(tempAlign, 'clustal')
    alignedSeq = []
    for rec in alignment:
        alignedSeq.append(str(rec.seq))
    os.system("rm %s %s " % (tempSeq, tempAlign) )
    return alignedSeq

iupac = {
        'A':'A',
        'C': 'C',
        'G':'G',
        'T':'T',
        'R': '(AG)',
        'Y': '(CT)',
        'S': '(GC)',
        'W': '(AT)',
        'K': '(GT)',
        'M': '(AC)',
        'B': '(CGT)',
        'D': '(AGT)',
        'H': '(ACT)',
        'V': '(ACG)',
        'N':'N'         
        }
def replaceIUPACLetters(iupacSeq):
    tcgaSeq = ''
    iupacLetters = ''.join(iupac.keys())
    for s in iupacSeq.upper():
        if s not in iupacLetters:
            tcgaSeq += s
        else:
            tcgaSeq += iupac[s]
    return tcgaSeq
    
'''
    Used for restriction sites search 
'''
def findHitsRegion(cdrRec, hitStarts):
    vhStart = cdrRec['vqstart'] - cdrRec['vstart']
    regions = {}
    for s in hitStarts:
        if (s >= cdrRec['fr1.start']-cdrRec['vstart']  - vhStart and s <= cdrRec['fr1.end'] - vhStart):
            regions['fr1'] = 1
        elif (s >= cdrRec['cdr1.start'] - vhStart and s <= cdrRec['cdr1.end'] - vhStart):
            regions['cdr1'] = 1
        elif (s >= cdrRec['fr2.start'] - vhStart and s <= cdrRec['fr2.end'] - vhStart):
            regions['fr2'] = 1
        elif (s >= cdrRec['cdr2.start'] - vhStart and s <= cdrRec['cdr2.end'] - vhStart):
            regions['cdr2'] = 1
        elif (s >= cdrRec['fr3.start'] - vhStart and s <= cdrRec['fr3.end'] - vhStart):
            regions['fr3'] = 1
        elif (s >= cdrRec['cdr3.start'] - vhStart and s <= cdrRec['cdr3.end'] - vhStart):
            regions['cdr3'] = 1
        elif (not isnan(cdrRec['fr4.end']) and s >= cdrRec['fr4.start'] - vhStart and s <= cdrRec['fr4.end'] - vhStart):
            regions['fr4'] = 1    
        else:
            print(hitStarts, vhStart, cdrRec)
            raise
    return regions
                
def findHits(seq, site):
    seq = seq.upper()
    site = site.replace('/', '')  
    return [match.start() for match in re.finditer('(?=(%s))' %(site), seq)]
#     return len(re.findall(site, seq))
  

# source ftp://ftp.ncbi.nih.gov/blast/matrices/NUC.4.4        
matStr1 = ("   A   T   G   C   S   W   R   Y   K   M   B   V   H   D   N,"
          "A   5  -4  -4  -4  -4   1   1  -4  -4   1  -4  -1  -1  -1  -2,"
          "T  -4   5  -4  -4  -4   1  -4   1   1  -4  -1  -4  -1  -1  -2,"
          "G  -4  -4   5  -4   1  -4   1  -4   1  -4  -1  -1  -4  -1  -2,"
          "C  -4  -4  -4   5   1  -4  -4   1  -4   1  -1  -1  -1  -4  -2,"
          "S  -4  -4   1   1  -1  -4  -2  -2  -2  -2  -1  -1  -3  -3  -1,"
          "W   1   1  -4  -4  -4  -1  -2  -2  -2  -2  -3  -3  -1  -1  -1,"
          "R   1  -4   1  -4  -2  -2  -1  -4  -2  -2  -3  -1  -3  -1  -1,"
          "Y  -4   1  -4   1  -2  -2  -4  -1  -2  -2  -1  -3  -1  -3  -1,"
          "K  -4   1   1  -4  -2  -2  -2  -2  -1  -4  -1  -3  -3  -1  -1,"
          "M   1  -4  -4   1  -2  -2  -2  -2  -4  -1  -3  -1  -1  -3  -1,"
          "B  -4  -1  -1  -1  -1  -3  -3  -1  -1  -3  -1  -2  -2  -2  -1,"
          "V  -1  -4  -1  -1  -1  -3  -1  -3  -3  -1  -2  -1  -2  -2  -1,"
          "H  -1  -1  -4  -1  -3  -1  -3  -1  -3  -1  -2  -2  -1  -2  -1," 
          "D  -1  -1  -1  -4  -3  -1  -1  -3  -1  -3  -2  -2  -2  -1  -1,"
          "N  -2  -2  -2  -2  -1  -1  -1  -1  -1  -1  -1  -1  -1  -1  -1"
)
# custom: ambitious code matching == max score
matStr2 = ("   A   T   G   C,"
          "A   5  -4  -4  -4,"
          "T  -4   5  -4  -4,"
          "G  -4  -4   5  -4,"
          "C  -4  -4  -4   5,"
          "S  -4  -4   5   5,"
          "W   5   5  -4  -4,"
          "R   5  -4   5  -4,"
          "Y  -4   5  -4   5,"
          "K  -4   5   5  -4,"
          "M   5  -4  -4   5,"
          "B  -4  5  5  5,"
          "V  5  -4  5  5,"
          "H  5  5  -4  5," 
          "D  5  5  5  -4,"
          "N  5  5  5  5"
)

def getIUPACSubMatrix():
    lines = matStr2.split(',')
    colHeads = lines[0].split()
    iupacSubMat = {}
    for line in lines[1:]:
        row = line.split()
        for i in range(len(row) - 1):
            iupacSubMat[(colHeads[i], row[0])] = float(row[i+1])
    return iupacSubMat

subMatIUPAC = getIUPACSubMatrix()

def calMaxIUPACAlignScores(seqs):
    scores = []
    for seq in seqs:
        scores.append(0)        
        for s in seq:
            rowscores = []
            for (r, c) in subMatIUPAC.keys():
                if (c == s):
                    rowscores.append(subMatIUPAC[(r, c)])
            scores[-1] += max(rowscores)
    return scores
        
'''
    A function to find the best matched pattern in a list of patterns
    and classify the type of the alignment (intact, indelled, mismatched, unknown)
'''            
def findBestMatchedPattern(seq, patterns):
    scores = []
    # align the sequence against all possible patterns
    for (id, pattern, maxScore) in patterns:
#         print(seq, pattern)
        alignments = align.localds(seq.upper(), pattern, subMatIUPAC, -5, -5)
        if (len(alignments) > 1):
            localScores = [a[2] for a in alignments]
            alignment = alignments[localScores.index(max(localScores))]
        elif (len(alignments) > 0):
            alignment = alignments[0]
        else:
            raise Exception("Couldn't align ... ", seq, patterns)            
        if alignment:
            alignLen = alignment[-1] - alignment[-2]
            scores.append((id, alignment))
            ## if the sequence exactly matches one of the patterns ==> intact
            if (alignment[2] == maxScore and 
                alignLen == len(pattern) and 
                '-' not in alignment[0] and
                '-' not in alignment[1]):
                return (scores[-1][0], "Intact", 0)
        else:
            scores.append((id, ('', '', 0)))
    # if no exact matching ==> find the best alignment (pattern)
    if (len(scores) > 1):       
        tmp = map(lambda x : x[1][2], scores)
        bestInd = tmp.index(max(tmp))       
    elif len(scores) == 1:
        bestInd = 0
    else:
        return ("None", "Unknown", 0)
    # classify the allignment type ==> insertion, deletion, mismatches
    best = list(scores[bestInd])    
    best[1] = list(best[1])
    if best[1][2] == 0:
        return ("None", "Unknown", 0)
    # Find the position of Indel/Mismatch
    # remove starting indels
    if best[1][1].startswith('-'):
        i = 0
        while best[1][1][i] == '-':
            i += 1
        best[1][0] = best[1][0][i:]
        best[1][1] = best[1][1][i:]
    # find the location of insertion or deletion 
    delPos = -1
    if '-' in best[1][0]:
        delPos=  best[1][0].index('-') + 1
    # if there is a gap at the beginning ==> happened because of insertion/deletion in the middle
    if '-' in best[1][1] and  best[1][1].index('-') > delPos and best[1][3] > 0 and best[1][4] == len(best[1][0]):
        delPos = best[1][1].index('-')
    # if a gap at the end ==>  deletion in the middle
    elif '-' in best[1][1] and  best[1][1].index('-') + 1 < delPos: # and best[1][4] < len(best[1][0]):
        delPos = best[1][1].index('-') + 1
        
    if delPos != -1:    
        return (best[0], "Indelled", delPos) # 1-based
    else:
        # if it is Mismatched ==> length of alignment == length of pattern
        try:           
            assert len(best[1][0]) == len(patterns[bestInd][1])
            misPos = 0
            while (misPos < len(best[1][0])):
                # 5 is max score in the substitution matrix
                if (subMatIUPAC[(best[1][0][misPos], patterns[bestInd][1][misPos])] != 5):
                    break
                misPos += 1 
        except:
            raise Exception("Unexpected behaviour:" + seq +  " " + scores + " " + best)            
        return (best[0], "Mismatched", misPos+1) # 1-based

def splitFastaFile(fastaFile, totalFiles, seqsPerFile, filesDir, 
                   cutAt = -1, prefix="", ext=".fasta"):    
    if (not exists(filesDir + "/" + prefix + "part" + `int(totalFiles)` + ext) and 
        not exists(filesDir + "/" + prefix + "part"  + `int(totalFiles)` + ".out")):        
        # Split the FASTA file into multiple chunks
        print("\tThe clones are distributed into multiple workers .. ")    
        if (not os.path.isdir(filesDir)):        
            os.system("mkdir " + filesDir)
        i = 1  
        records = []
        out = None
        if (MEM_GB > 20):
            recordsAll = SeqIO.to_dict(SeqIO.parse(fastaFile, 'fasta'))
        else:
            recordsAll = SeqIO.index(fastaFile, 'fasta')
        for id in recordsAll:
            rec = recordsAll[id]
            if (i %  seqsPerFile == 1):
                if (out is not None):
                    SeqIO.write(records, out, 'fasta')
                    records = []   
                out =filesDir + "/" + prefix + "part"  + `int(i / seqsPerFile) + 1` + ext
            rec.description = ''
            if cutAt > 0:
                rec.seq = rec.seq[:cutAt]
            records.append(rec)
            i += 1      
            sys.stdout.flush()
        if (out is not None):
            SeqIO.write(records, out, 'fasta')  

    
