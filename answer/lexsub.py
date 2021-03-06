import os, sys, optparse
import tqdm
import pymagnitude
import numpy as np
from pymagnitude import converter
from gensim import scripts
from gensim.scripts.glove2word2vec import glove2word2vec


def read_word_vector(filename):

    wordVec={}
    for line in open(filename, 'r'):
        wordC = line.strip().lower().split()
        temp = [w for w in wordC[1:]]
        if wordC[0] not in wordVec:
            wordVec[wordC[0]] = temp
        else:
            wordVec[wordC[0]] += temp
    return wordVec

def retrofit(wordVecs, lexicon, T=20, alpha=2, beta=1):
    newWordVecs = {}
    wvVocab = set()
    for word, it in wordVecs:
        wvVocab.add(word)
        newWordVecs[word] = it
    for i in range(T):
        for j, word in enumerate(wvVocab):
            temp = np.zeros(newWordVecs[word].shape)
            if word in lexicon:
                count = 0
                LoopVocab = lexicon[word]
                for w in LoopVocab:
                    if w in newWordVecs:
                        temp += beta * newWordVecs[w]
                        count += 1
                newWordVecs[word] = ((temp + (alpha * wordVecs.query(word)))) / (count + alpha)
    return newWordVecs

def convert_to_magnitude_and_retrofit(mag_path):
    path = os.getcwd()
    if os.getcwd().split('/')[-1] == 'answer':
        path = os.path.dirname(os.getcwd())
    LL_path = os.path.join(path,'data/lexicons','ppdb-xl.txt')
    lexicon = read_word_vector(LL_path)
    wv = pymagnitude.Magnitude(mag_path)
    lexicon_retrofitted = retrofit(wv, lexicon)
    retrofitpath = os.path.join(path,'data','glove.6B.100d.retrofit.txt')
    # if os.path.exists(os.path.join(path,'data','glove.6B.100d.retrofit.magnitude')) == True:
    #     wvecs=pymagnitude.Magnitude(os.path.join(path,'data','glove.6B.100d.retrofit.magnitude'))
    # else:
    with open(retrofitpath, 'w') as f:
        for word, embedding in lexicon_retrofitted.items():
            s = word
            for num in embedding:
                s += " " + str(num)
            s += '\n'
            f.write(s)
        target_file=os.path.join(path,'data','glove.6B.100d.retrofit.magnitude')
        converter.convert(retrofitpath, target_file)
    wvecs = pymagnitude.Magnitude(os.path.join(path,'data','glove.6B.100d.retrofit.magnitude'))
    return wvecs

class LexSub:
    def __init__(self, wvec_file, topn=10):
#         self.wvecs = pymagnitude.Magnitude(wvec_file)
        self.topn = topn
        self.wvecs = convert_to_magnitude_and_retrofit(wvec_file)

    def substitutes(self, index, sentence):
        "Return ten guesses that are appropriate lexical substitutions for the word at sentence[index]."
        return(list(map(lambda k: k[0], self.wvecs.most_similar(sentence[index], topn=self.topn))))

if __name__ == '__main__':
    optparser = optparse.OptionParser()
    optparser.add_option("-i", "--inputfile", dest="input", default=os.path.join('data', 'input', 'dev.txt'), help="input file with target word in context")
    optparser.add_option("-w", "--wordvecfile", dest="wordvecfile", default=os.path.join('data', 'glove.6B.100d.magnitude'), help="word vectors file")
    optparser.add_option("-n", "--topn", dest="topn", default=10, help="produce these many guesses")
    optparser.add_option("-l", "--logfile", dest="logfile", default=None, help="log file for debugging")
    (opts, _) = optparser.parse_args()

    if opts.logfile is not None:
        logging.basicConfig(filename=opts.logfile, filemode='w', level=logging.DEBUG)

    lexsub = LexSub(opts.wordvecfile, int(opts.topn))
    num_lines = sum(1 for line in open(opts.input,'r'))
    with open(opts.input) as f:
        for line in tqdm.tqdm(f, total=num_lines):
            fields = line.strip().split('\t')
            print(" ".join(lexsub.substitutes(int(fields[0].strip()), fields[1].strip().split())))
