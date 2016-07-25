from multiprocessing import Process
from NGSutils import runIgblastn, runIgblastp
from collections import Counter
from pandas.core.frame import DataFrame
import sys
import numpy as np

'''
Author: Monther Alhamdoosh
Email: monther.alhamdoosh@csl.com.au / m.hamdoosh@gmail.com 

'''

def extractIGVStats(blastOutput, bitScore, alignLen, subjStart):
    # Extract the top hits  
    print('\tExtracting top hit tables ... ' + blastOutput.split("/")[-1])
    # process igblast output and extract top hit 
    igvDist = Counter()
    stats = []
    filteredIDs = []
    line = ""
    with open(blastOutput) as blast:                   
        while(True):                        
            if (not line.startswith('# Query')):
                line = blast.readline()                       
            if (not line):
                break
            if (line.startswith('# Query')):
                queryId = line.split()[2]                
                line = blast.readline()                
                while(line and 
                      not line.startswith('# Query') and
                       not line.startswith('# Hit')):
                    line = blast.readline()
                    
                if (not line.startswith('# Query')):
                    line = blast.readline()
                    if (line.startswith('# Fields')):
                        line = blast.readline()
                        noHits = int(line.split()[1])    
                        if (noHits != 0): 
                            # retrieve the top hit
                            line = blast.readline()
                            if (not line.startswith("V")): 
                                continue
                            hit = line.split()
                            score = float(hit[-1]) 
                            align = int(hit[4])   
                            sStart = int(hit[10])
                            if (score >= bitScore[0] and score <= bitScore[1] and # check bit-Score
                                align >= alignLen[0] and align <= alignLen[1] and # check alignment length
                                sStart >= subjStart[0] and sStart <= subjStart[1]):  # check subject start
#                                 if (hit[1].split("|")[0] != "reversed"):
#                                     print(hit[1])                    
#                                 if (int(hit[7]) > 0):
#                                     print(line)                              
                                igvDist[hit[2]] = igvDist.get(hit[2], 0) + 1
                                # %identity, Alignment Length, bit-Score,q.start, s.start,
                                stats.append([float(hit[3]), 
                                              align, score,
                                              int(hit[8]), sStart, int(hit[5]), int(hit[7])])
                            else:
                                filteredIDs.append(queryId)
    if stats != []:
        stats = DataFrame(stats, columns = ['identity', 'alignlen', 'bitscore', 'qstart', 
                         'sstart', 'mismatches', 'gaps'])
    else:
        stats = DataFrame()                                                                                 
    return (igvDist, stats, filteredIDs)


def extractIGVAlignInfo(blastOutput, bitScore, alignLen, subjStart):
    # Extract the top hits  
    print('\tExtracting top hit tables ... ' + blastOutput.split("/")[-1])
    # process igblast output and extract top hit 
    alignInfo = []
    line = ""
    with open(blastOutput) as blast:                   
        while(True):                        
            if (not line.startswith('# Query')):
                line = blast.readline()                       
            if (not line):
                break
            if (line.startswith('# Query')):                
                line = blast.readline()
                while(line and 
                      not line.startswith('# Query') and
                       not line.startswith('# Hit')):
                    line = blast.readline()
                    
                if (not line.startswith('# Query')):
                    line = blast.readline()
                    if (line.startswith('# Fields')):
                        line = blast.readline()
                        noHits = int(line.split()[1])    
                        if (noHits != 0): 
                            # retrieve the top hit
                            line = blast.readline()
                            if (not line.startswith("V")): 
                                continue
                            hit = line.split()
                            score = float(hit[-1]) 
                            align = int(hit[4])   
                            sStart = int(hit[10])
                            if (score >= bitScore[0] and score <= bitScore[1] and # check bit-Score
                                align >= alignLen[0] and align <= alignLen[1] and # check alignment length
                                sStart >= subjStart[0] and sStart <= subjStart[1]):  # check subject start
#                                 if (hit[1].split("|")[0] != "reversed"):
#                                     print(hit[1])                    
#                                 if (int(hit[5]) > 30):
#                                     print(line)                              
                                # QueryID, SubjID, queryStart, SubjStart, +/-, 
                                if (hit[1].split("|")[0] == "reversed"):
                                    alignInfo.append([hit[1].split("|")[1].strip(), hit[2],
                                                    int(hit[8]), sStart, 'reversed'])
                                else:
                                    alignInfo.append([hit[1].strip(), hit[2],
                                                    int(hit[8]), sStart, 'forward']) 
    
    alignInfo = DataFrame(alignInfo, 
                          columns = ['queryid', 'subjid', 'qstart', 'sstart', 'strand'])
    alignInfo.index = alignInfo.queryid
    del alignInfo['queryid']
                                                                               
    return alignInfo


CDR_FIELDS = ['queryid', 'vgene', 'vqstart', 'vstart', 'vmismatches', 'vgaps',
                    'dgene', 'dqstart', 'dstart', 'dmismatches', 'dgaps', 
                    'jgene', 'jqstart', 'jqend', 'jstart', 'jmismatches', 'jgaps',  
                    'strand', 'stopcodon', 'v-jframe',
                    'fr1.start', 'fr1.end', 'fr1.mismatches', 'fr1.gaps',
                    'cdr1.start', 'cdr1.end', 'cdr1.mismatches', 'cdr1.gaps',
                    'fr2.start', 'fr2.end', 'fr2.mismatches', 'fr2.gaps',
                    'cdr2.start', 'cdr2.end', 'cdr2.mismatches', 'cdr2.gaps',
                    'fr3.start', 'fr3.end', 'fr3.mismatches', 'fr3.gaps',
                    'cdr3.start', 'cdr3.end', 'cdr3.mismatches', 'cdr3.gaps',
                    'fr4.start', 'fr4.end', 'fr4.mismatches', 'fr4.gaps'
                    ]

def createCdrRecord():
    cdrRecord = {}    
    for field in CDR_FIELDS:
        cdrRecord[field] =  np.nan
    return cdrRecord


def convertCdrRecordToOrderedList(cdrRecord):    
    orderedList = []
    for field in CDR_FIELDS:
        orderedList.append(cdrRecord[field])
    
    return orderedList

def to_int(x):
    try:
        return int(x.strip())
    except:
        return None

def extractCDRInfo(blastOutput, bitScore, alignLen, subjStart):
    # Extract the top hits  
    print('\tExtracting top hit tables ... ' + blastOutput.split("/")[-1])
    # process igblast output and extract top hit 
    cdrinfo = []
    line = ""
    
    warning = False
    with open(blastOutput) as blast:                   
        while(True):
            try:
                if (not line.startswith('# Query')): 
                    line = blast.readline()                       
                    if (not line):
                        break 
                    continue            
                cdrRecord = createCdrRecord()
                cdrRecord['queryid'] = line.split()[2].strip()
                # parse  V-(D)-J rearrangement   
                line = blast.readline()
                while(line and 
                      not line.startswith('# Query') and
                       not line.startswith('# V-(D)-J rearrangement')):
                    line = blast.readline()
                if (not line):
                    break
                if (line.startswith('# Query')):
                    continue
                line = blast.readline().strip().split('\t')
                cdrRecord['strand'] = 'forward' if line[-1] == '+' else 'reversed'
#                 print line, cdrRecord['strand']
#                 sys.exit()
                cdrRecord['stopcodon'] = line[4]
                cdrRecord['v-jframe'] = line[5]
                cdrRecord['vgene'] = line[0].split(',')[0]
                cdrRecord['dgene'] = line[1].split(',')[0]
                cdrRecord['jgene'] = line[2].split(',')[0]
                # parse Alignment Summary between query and top germline V gene
                line = ' '.join(line)
                while (line and 
                       not line.startswith('# Query') and
                       not line.startswith("# Alignment")):
                    line = blast.readline()
                if (not line):
                    break
                if (line.startswith('# Query')):
                    continue
                line = blast.readline()
                for i in range(1,4):                
                    if (line.lower().startswith('fr' + `i`)):
                        line = line.split()
                        cdrRecord['fr%d.start' % i] = to_int(line[1])
                        cdrRecord['fr%d.end' % i] = to_int(line[2]) 
                        cdrRecord['fr%d.mismatches' % i] = to_int(line[5])
                        cdrRecord['fr%d.gaps' % i] = to_int(line[6])
                        line = blast.readline()
                    if (line.lower().startswith('cdr' + `i`)):
                        line = line.replace('(germline)', '').split()
                        cdrRecord['cdr%d.start' % i] = to_int(line[1])
                        cdrRecord['cdr%d.end' % i] = to_int(line[2]) 
                        cdrRecord['cdr%d.mismatches' % i] = to_int(line[5])
                        cdrRecord['cdr%d.gaps' % i] = to_int(line[6])
                        line = blast.readline()
                # parse alignment information between query and V, D and J genes
                while (line and 
                       not line.startswith('# Query') and
                       not line.startswith("# Fields")):
                    line = blast.readline()
                if (not line):
                    break
                if (line.startswith('# Query')):
                    continue            
                line = blast.readline()
                noHits = to_int(line.split()[1])    
                if (noHits == 0):
                    continue 
                # retrieve the top hit
                # parse the top V gene info
                line = blast.readline()
                if (not line.startswith("V")): 
                    continue
                hit = line.split()
                score = float(hit[-1]) 
                align = to_int(hit[4])   
                sStart = to_int(hit[10])
                if (score >= bitScore[0] and score <= bitScore[1] and # check bit-Score
                    align >= alignLen[0] and align <= alignLen[1] and # check alignment length
                    sStart >= subjStart[0] and sStart <= subjStart[1]):  # check subject start
                    cdrRecord['vqstart'] = to_int(hit[8])
                    cdrRecord['vstart'] = sStart
                    cdrRecord['vmismatches'] = to_int(hit[5])
                    cdrRecord['vgaps'] = to_int(hit[7])
                    # parse the top D gene info
                    line = blast.readline()
                    while (line and
                           not line.startswith("# Query") and
                           not line.startswith("D") and 
                           not line.startswith("J")):
                        line = blast.readline()
                    if (not line):
                        cdrinfo.append(convertCdrRecordToOrderedList(cdrRecord))
                        break
                    if (line.startswith('# Query')):
                        cdrinfo.append(convertCdrRecordToOrderedList(cdrRecord))
                        continue         
                    if (line.startswith("D")):
                        hit = line.split()
                        cdrRecord['dqstart'] = to_int(hit[8])
                        cdrRecord['dstart'] = to_int(hit[10])
                        cdrRecord['dmismatches'] = to_int(hit[5])
                        cdrRecord['dgaps'] = to_int(hit[7])
                        while (line and
                           not line.startswith("# Query") and
                           not line.startswith("J")):
                            line = blast.readline()
                        if (not line):
                            cdrinfo.append(convertCdrRecordToOrderedList(cdrRecord))
                            break
                        if (line.startswith('# Query')):
                            cdrinfo.append(convertCdrRecordToOrderedList(cdrRecord))
                            continue 
                    if (line.startswith("J")):
                        hit = line.split()
                        cdrRecord['jqstart'] = to_int(hit[8])
                        cdrRecord['jqend'] = to_int(hit[9])
                        cdrRecord['jstart'] = to_int(hit[10])
                        cdrRecord['jmismatches'] = to_int(hit[5])
                        cdrRecord['jgaps'] = to_int(hit[7])
                    cdrinfo.append(convertCdrRecordToOrderedList(cdrRecord))
            except:
#                 print(line, cdrRecord)
                warning = True
                continue
            
    if (len(cdrinfo) > 0):
        # productive = no stop and in-frame
        # v-jframe: in-frame, out-of-frame, N/A (no J gene) 
        # stopcodon: yes, no
        cdrinfo = DataFrame(cdrinfo, columns =  CDR_FIELDS) 
        cdrinfo.index = cdrinfo.queryid
        del cdrinfo['queryid']
    else:
        cdrinfo = DataFrame()
    if (warning):
        print("Warning: something went wrong while parsing %s" % (blastOutput))                                                            
    return cdrinfo


def analyzeSmallFile(fastaFile, chain, igBlastDB, bitScore, alignLen, subjStart, 
                     operation, seqType='dna', threads=8): # , bitScore = 0
    # Run igblast
    if seqType.lower() == 'dna':
        blastOutput = runIgblastn(fastaFile, chain, threads, igBlastDB)   
    else:
        blastOutput = runIgblastp(fastaFile, chain, threads, igBlastDB)
    if (operation == 'abundance'):
        return extractIGVStats(blastOutput, bitScore, alignLen, subjStart)
    elif (operation == 'aligninfo'):
        return extractIGVAlignInfo(blastOutput, bitScore, alignLen, subjStart)
    elif (operation == 'cdrinfo'):
        return extractCDRInfo(blastOutput, bitScore, alignLen, subjStart)
    else:
        return None             
    

class IgBlastWorker(Process):
    def __init__(self, chain, igBlastDB, bitScore, alignLen, subjStart, operation,
                 seqType, threads):
        super(IgBlastWorker, self).__init__() 
        self.chain = chain     
        self.igBlastDB = igBlastDB  
        self.bitScore = bitScore
        self.alignLen = alignLen
        self.subjStart = subjStart
        self.operation = operation
        self.seqType = seqType
        self.threads = threads
        self.tasksQueue = None
        self.resultsQueue = None
        self.exitQueue = None
#         self.args = None
    
#     def __init__(self, name, tasksQueue, resultsQueue):
#         self.name = name
#         self.tasksQueue = tasksQueue
#         self.resultsQueue = resultsQueue
    
    def run(self):
        while True:            
            nextTask = self.tasksQueue.get()
#             print("process has started a run... " + self.name)
            # poison pill check            
            if (nextTask is None):
                print("process has stopped ... " + self.name)
                self.exitQueue.put("exit")
#                 self.terminate()
                break
            try:
                result = analyzeSmallFile(nextTask, self.chain, self.igBlastDB, 
                                                     self.bitScore, self.alignLen,
                                                     self.subjStart,
                                                     self.operation,
                                                     self.seqType, self.threads)                        
#                 print("process has completed analysis... " + self.name) 
                self.resultsQueue.put(result)            
            except Exception as e:
                print("An error occurred while processing " + nextTask.split('/')[-1])
                print(e)
                self.resultsQueue.put(None)
#                 raise
#                 sys.exit()
                continue                       
#             print("process has completed a run... " + self.name) 
        return
         