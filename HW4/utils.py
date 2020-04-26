import ast
import math
import re
import string
from collections import namedtuple
from math import log10 as log
from math import sqrt

from nltk.stem.porter import PorterStemmer

try:
    import cPickle as pickle
except ImportError:
    import pickle

maxLength = None
stemmer = PorterStemmer()

highPrioritySet = {
    'SG Court of Appeal',
    'SG Privy Council',
    'UK House of Lords'
    'UK Supreme Court',
    'High Court of Australia',
    'CA Supreme Court]'
}

mediumPriorityList = {
    'SG High Court',
    'Singapore International Commercial Court',
    'HK High Court',
    'HK Court of First Instance',
    'UK Crown Court',
    'UK Court of Appeal',
    'UK High Court',
    'Federal Court of Australia',
    'NSW Court of Appeal',
    'NSW Court of Criminal Appeal',
    'NSW Supreme Court'
}

############################################
###########       Functions      ###########
############################################


def getCourtsPriority(docId, courts_dict):
    try:
        courts = courts_dict[str(docId)][1]
        if courts in highPrioritySet:
            return 2
        elif courts in mediumPriorityList:
            return 1
        else:
            return 0
    except KeyError as e:
        return 0

def preprocess(raw_text, removedigit=False, splitcombined=False, removepunc=True):
    ''' 
    split conjunctions; remove punctuations, digits; case-folding all words 

    Since in this project we did not consider the removal of digits, punctuations, 
    conjunction symbols in the word, this function is not used.
    '''

    # lowercase letter
    text = raw_text.lower()

    # remove digits
    if removedigit:
        text = text.translate(
            str.maketrans("", "", string.digits))

    # split combined words
    if splitcombined:
        test = re.sub("[-']", " ", text)

    # remove punctuations
    if removepunc:
        text = text.translate(
            str.maketrans("", "", string.punctuation))

    return text


def get_tf(term_freq):
    '''
    Given term freq = 1 + log(tf), calculate and return the term freq weight

    @param term_freq - The term frequency: int
    @return weight: float
    '''
    if term_freq == 0:
        return 0
    else:
        return 1 + log(term_freq)


def normalize(list_to_norm):
    '''
    Normalize a given list

    @param list_to_norm - a list to normalize: list
    @return the normalized list: list
    '''
    norm = sqrt(sum([i * i for i in list_to_norm], 0))
    if norm == 0:
        return list_to_norm
    else:
        return [i / norm for i in list_to_norm]


############################################
#####    NamedTupels: Entry & Token    #####
############################################
'''
Entry := an entry of the dictionary, containing the frequency of 
the token, the offset of the postings file, the size of the list
(of docIDs) corresponding inside the postings file
'''
Entry = namedtuple("Entry", ['frequency', 'offset'])
Entry.__new__.__defaults__ = (0, 0, 0)


'''
Token := an entry of the posting, containing the weight inside a given document
'''
Token = namedtuple("Token", ['weight'])
Token.__new__.__defaults__ = (0, 0)
PhrasalToken = namedtuple("PhrasalToken", ["pos", 'weight'])
PhrasalToken.__new__.__defaults__ = (0, [], 0)

############################################
##########     Class: Posting    ###########
############################################
class Posting(object):
    ''' 
    A data structure that based on a dictionary in order 
    to get the value of the dictionary from the disk as 
    you would do it for a normal dictionary.

    It represents the dictionary token and the postings, i.e., 
    list of tuples (docID, token_freq).

    Can access the postings on disk for a given entry
    '''

    def __init__(self, dicionary, posting_file):
        '''
        @param dictionary: DefaultDict[str, Entry]
        @param posting_file: txt file
        '''
        self.dictionary = dicionary
        self.posting_file = posting_file

    def __getitem__(self, term):
        '''
        Implement of evaluation of self[key]

        Return the associated Token to a key, or an empty Token if the
        token is not in the dictionary

        @param term: int
        @return Term(token_freq, weight)
        '''
        if term in self.dictionary:
            val = self.dictionary[term]  # val: Entry
            self.posting_file.seek(val.offset)
            return pickle.load(self.posting_file)
        else:
            return Token(0, 0)
