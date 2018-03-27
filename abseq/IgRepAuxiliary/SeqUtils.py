'''
    Short description: Quality Control Analysis of Immunoglobulin Repertoire NGS (Paired-End MiSeq)    
    Author: Monther Alhamdoosh    
    Python Version: 2.7
    Changes log: check git commits. 
'''
from __future__ import print_function
import matplotlib
matplotlib.use('agg')
import gc
import sys
import pickle
import random
import bisect
import matplotlib.pyplot as plt
import os

from os.path import exists
from collections import Sequence, defaultdict
from Bio.Seq import Seq
from Bio.Alphabet.IUPAC import IUPACProtein
from Bio import SeqIO, motifs, Phylo
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import Alphabet

from abseq.config import WEBLOGO
import abseq.IgRepertoire
from abseq.logger import printto, LEVEL

# the following are conditionally imported in functions that require them to reduce abseq's dependency list
# It's here for a simple glance of required dependencies
# from TAMO.Clustering.UPGMA import UPGMA
# from TAMO.Clustering.UPGMA import DFUNC
# from TAMO.Clustering.UPGMA import print_tree
# from TAMO.Clustering.UPGMA import create_tree_phylip
# from TAMO.Clustering.UPGMA import print_tree_id
# from TAMO import MotifTools
# from TAMO.MotifTools import Motif

def readSeqFileIntoDict(seqFile, format = "fastq", outDict = None):
    if (outDict is None):
        outDict = {}
    try:
        if format == "fastq":
            with open(seqFile) as h:
                while True:
                    line = h.readline()
                    if not line:
                        break
                    id = line.strip("\n")[1:].split()[0]
                    seq = h.readline().strip("\n") 
                    outDict[id] = seq
                    h.readline()
                    h.readline()
#                     print(id)
        elif format == "fasta":
            with open(seqFile) as h:
                while True:            
                    line = h.readline()
                    if not line:
                        break
                    line = line.strip("\n")
                    if line.startswith(">"):
                        id = line[1:].split()[0]
                        outDict[id] = ""
                    else:
                        outDict[id] += line                            
        else:
            raise Exception("Unknown sequence file format")
    except Exception as e: 
        print("Something went wrong while reading a sequence file")
        raise e
    return outDict


def generateMotif(sequences, name, alphabet, filename, 
                  align=False, transSeq=False, protein=False, weights=None, outDir=None, stream=None):
    """

    :param sequences: list of strings
                    list of sequences used to find motifs

    :param name: string
                    sample name
    :param alphabet:
    :param filename:
    :param align:
    :param transSeq:
    :param protein:
    :param weights:
    :param outDir:
    :param stream:
    :return:
    """
    if exists(filename):
        printto(stream, "\t" + name + " motif logo was found", LEVEL.WARN)
        return
    # check whether sequences should be translated                 
    if transSeq:
        seqs = []               
        for rec in sequences:
            seq = Seq(rec).translate(to_stop=False)                   
            seqs.append(str(seq))
    else:
        seqs = sequences
    # sample sequences if they are too many  
    if (len(seqs) > 1*10**5 or 
        (weights is not None and sum(weights) > 1*10**5)):
        random.seed(1986)
#         print(sum(weights))
        seqs = weightedSample(seqs, weights, int(1*10**5)) 
        if align:
            seqs = random.sample(seqs, 10000) 
    # perform multiple sequence alignment on a sample of 10000 sequences 
    if align and len(seqs) > 1:
        alignedSeq = abseq.IgRepertoire.igRepUtils.alignListOfSeqs(seqs, outDir, stream=stream)
#                 print(alignedSeq[:10])
    else:                
        # if alignment is not required, add "-" to short sequences
        L = map(len, seqs)
        if min(L) != max(L):
            # print('\t\t- is being added to short sequences ...[%d, %d[' % (min(L), max(L)))
            if '-' not in alphabet.letters:
                alphabet.letters += '-'
            alignedSeq = []
            m = max(L)
            for s in seqs:
                if len(s) < m:
                    alignedSeq.append(s + '-'*(m-len(s)))
        else:
            alignedSeq = seqs
    # create the sequence motif and encode it into PFM
    printto(stream, "\tMotif logo is being created for %s ..." % (name))
    m = motifs.create(alignedSeq, alphabet)  # print(m.counts)
    # create sequence logo
    generateMotifLogo(m, filename, outDir, not transSeq and not protein)
    return m
    
    
def createAlphabet(align=False, transSeq=False, extendAlphabet=False, protein=False):
    if not transSeq and not protein:
        alphabet = Alphabet()
        alphabet.letters = "ACGT" if not extendAlphabet else "ACGTN"            
    else:
        alphabet = IUPACProtein()
        alphabet.letters += '*' if not extendAlphabet else '*X'         
    if align:
        alphabet.letters += '-'  
    return alphabet


def generateMotifs(seqGroups, align, outputPrefix, transSeq=False,
                        extendAlphabet=False, clusterMotifs=False, protein=False, stream=None):
    from TAMO.MotifTools import Motif
    ighvMotifs = []
    if clusterMotifs and 'gene' in outputPrefix:
        findMotifClusters(ighvMotifs, outputPrefix, stream=stream)
    printto(stream, '\t\tPWMs, consensus and logos are being generated for {} motifs ... '.format(len(seqGroups)))
    pwmFile = open(outputPrefix + '_pwm.txt', 'w')
    consensusFile = open(outputPrefix + '_consensus.txt', 'w')
    logosFolder = outputPrefix + '_logos'

    if not os.path.exists(logosFolder):
        os.makedirs(logosFolder)

    # create the sequence alphabet: DNA or Protein
    alphabet = createAlphabet(align, transSeq, extendAlphabet, protein)
    groups = seqGroups.keys()
    groups.sort()        
    
    for group in groups:    
        filename = os.path.join(logosFolder, group.replace('/', '') + '.png')
        seqs = seqGroups[group]
        m = generateMotif(seqs, group, alphabet, filename, align, transSeq, protein, outDir=logosFolder)
        if m is None:
            # motif file found, no further work required
            return
        motifSeqs = m.instances
        pwm = m.counts.normalize(pseudocounts=None)  # {'A':0.6, 'C': 0.4, 'G': 0.4, 'T': 0.6}
        consensusMax = str(m.consensus)      
               
        pwmFile.write('#{} {} sequences\n'.format(group, len(motifSeqs)))
        pwmFile.write(str(pwm))  
        consensusFile.write('>{} max_count\n'.format(group))
        consensusFile.write(consensusMax + '\n')      
    #             print(str(m.anticonsensus)) # smallest values in the columns
        if not transSeq and not align and not protein:
            consensusIupac = str(m.degenerate_consensus)
    #             print(consensusIupac) # IUPAC ambiguous nucleotides            
            consensusFile.write('>{} degenerate\n'.format(group))
            consensusFile.write(consensusIupac + '\n')
        
        pwmFile.flush()
        consensusFile.flush()
        gc.collect()
        if clusterMotifs and len(motifSeqs) > 10:
            motif = Motif(map(lambda x: str(x), motifSeqs),
                          backgroundD={'A': 0.6, 'C': 0.4, 'G': 0.4, 'T': 0.6}, id=group)
            motif.addpseudocounts(0.1)
            ighvMotifs.append(motif)
            
    pwmFile.close()
    consensusFile.close()      
    gc.collect()
    printto(stream, "\tPosition weight matrices are written to " + os.path.basename(outputPrefix + '_pwm.txt'))
    printto(stream, "\tConsensus sequences are written to " + os.path.basename(outputPrefix + '_consensus.txt'))
    if clusterMotifs:
        findMotifClusters(ighvMotifs, outputPrefix, stream=stream)
        
        
def findMotifClusters(ighvMotifs, outputPrefix, stream=None):
    from TAMO.Clustering.UPGMA import UPGMA
    from TAMO.Clustering.UPGMA import DFUNC
    from TAMO.Clustering.UPGMA import print_tree_id
    # cluster using a variant of the UPGMA algorithm implemented in the TAMO package
    
    motifsFile = os.path.abspath(outputPrefix + '_motifs.tamo')
    if not exists(motifsFile):
        if len(ighvMotifs) > 0:
            pickle.dump(ighvMotifs, open(motifsFile, 'wb'))            
    else:
        ighvMotifs = pickle.load(open(motifsFile, 'rb'))

    prefixName, sampleName = os.path.split(outputPrefix)
    dendogramDirectory = os.path.join(prefixName, 'dendograms')
    if not exists(dendogramDirectory):
        os.makedirs(dendogramDirectory)

    if len(ighvMotifs) > 0:
        groupedMotifs = defaultdict(list)
        for m in ighvMotifs:
            ighv = m.id.split('-')[0].split('/')[0]
            groupedMotifs[ighv].append(m)
        try:
            motifClustersFile = os.path.join(dendogramDirectory, sampleName + '_pwm_clusters.txt')

            _old_stdout = sys.stdout
            sys.stdout = open(motifClustersFile, 'w')

            for ighv in groupedMotifs.keys():
                newickDendogramFile = os.path.join(dendogramDirectory, sampleName + '_{}_newick.dnd'.format(ighv))
                tree = UPGMA(groupedMotifs[ighv], DFUNC)
                print_tree_id(tree)

                saveNewickDendogram(newickDendogramFile, tree, sys.stdout, title=ighv, logger=stream)

            lists = groupedMotifs.values()
            tree = UPGMA([m for lst in lists for m in lst], DFUNC)
            print_tree_id(tree)

            newickDendogramFile = os.path.join(dendogramDirectory, sampleName + '_newick.dnd')
            saveNewickDendogram(newickDendogramFile, tree, sys.stdout, logger=stream)

            sys.stdout.close()
            sys.stdout = _old_stdout

            printto(stream, "\tMotif clusters were written to " + os.path.basename(motifClustersFile))
        except Exception as e:
            print(e)
            printto(stream, "Motifs couldn't be clustered!", LEVEL.ERR)


def saveNewickDendogram(newickClusterFile, tree, stream, title="", logger=None):
    """
    :param newickClusterFile:
    :param tree:  UPGMA object
    :param stream:
    :param title:
    :param logger:
    :return:
    """
    from TAMO.Clustering.UPGMA import create_tree_phylip
    desc = '' if not title else " for {} ".format(title)

    # get phylip newick syntax
    phylipTree = create_tree_phylip(tree)
    with open(newickClusterFile, 'w') as newickfp:
        newickfp.write(phylipTree)

    printto(logger, "Newick dendogram{}written to ".format(desc) + os.path.basename(newickClusterFile))

    # show ascii art
    phylipTree = Phylo.read(newickClusterFile, format='newick')

    try:
        print("\n\nASCII phylip tree{}:\n".format(desc), file=stream)
        Phylo.draw_ascii(phylipTree, file=stream)
    except ZeroDivisionError:
        # if the weights are 0
        print("\t Not drawn because of 0 weights", file=stream)
        pass

    # plot dendogram in matplotlib
    phylipTree.ladderize()
    fig, axes = plt.subplots(figsize=(8, 5))
    Phylo.draw(phylipTree, do_show=False, axes=axes, branch_labels=lambda c: c.branch_length)
    axes.set_title(title)
    fig.savefig(newickClusterFile.replace('.dnd', '.png'), dpi=300)
    plt.close()


def generateMotifLogo(m, filename, outdir='', dna=True):
    instances = m.instances
    records = []
    for i in range(len(instances)):
        records.append(SeqRecord(instances[i], id=str(i)))
    tmpFile = os.path.join(outdir, 'temp_seq_logos.fasta')
    SeqIO.write(records, tmpFile, 'fasta')

    command = "%s -f %s  -o %s -A %s -F png -n 200 -D fasta -s medium "
    command += "-c %s --errorbars NO --fineprint CSL --resolution 600 -X NO -Y NO"

    os.system(command % (WEBLOGO, tmpFile, filename, "dna" if dna else "protein", "classic" if dna else "auto"))
    os.remove(tmpFile)
        

def maxlen(x):
    return max(map(len, x))


# XXX: Author: JIAHONG FONG: @depreciated. - removing adefazio/sampler dependency
# TODO: Look for faster and ACCURATE weighted sampling approach
# def weightedSampleFast(population, weights, k):
#    if (weights is not None):
#        from fast_sampler import FastSampler
#        from numpy import array
#        weights = array(weights, dtype='d')
#        h = FastSampler(len(population), max(weights), min(weights))
#        for i in range(len(population)):
#            h.add(i, weights[i])
#        s = map(lambda x : population[h.sample()], range(k))
#        return s
#    else:
#        return random.sample(population, k)


def weightedSample(population, weights, k):
    if weights is not None:
        return random.sample(WeightedPopulation(population, weights), k)
    else:
        return random.sample(population, k)


# from http://stackoverflow.com/questions/13047806/weighted-random-sample-in-python
class WeightedPopulation(Sequence):
    def __init__(self, population, weights):
        assert len(population) == len(weights) > 0
        self.population = population
        self.cumweights = []
        cumsum = 0 # compute cumulative weight
        for w in weights:
            cumsum += w   
            self.cumweights.append(cumsum)

    def __len__(self):
        return self.cumweights[-1]

    def __getitem__(self, i):
        if not 0 <= i < len(self):
            raise IndexError(i)
        return self.population[bisect.bisect(self.cumweights, i)]

