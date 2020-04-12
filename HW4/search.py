#!/usr/bin/python3
import getopt
import re
import string
import sys
from collections import Counter, defaultdict
from math import log10 as log
import array

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize


from utils import Entry, Posting, Token, get_tf, normalize, preprocess

try:
    import cPickle as pickle
except ImportError:
    import pickle


phrasal_query = False


def get_term_freq(query):
    ''' 
    Tokenize a given query, and do stemming.
    Count the term frequency in the query

    @param query The query string: str
    @return tokens A list contains all the tokens appeared in the query string: list[str]
            term_count A dictionary where records the counts of the terms in the query: DefaultDict[str: int]
    '''


    # tokenize the query string
    tokens = [word for sent in sent_tokenize(query)  for word in word_tokenize(sent)]
    if '"' in query:
        phrasal_query = True
        tokens = [token.replace('"', "").strip() for token in tokens]
    # stem the tokens
    ps = PorterStemmer()
    tokens = [ps.stem(token.lower()) for token in tokens]
    # tokens = [ps.stem(token.lower()) for token in query.split()]
    # get the term count
    term_count = defaultdict(int)
    for token in tokens:
        term_count[token] += 1

    # get the set of tokens
    terms = list(set(tokens))

    return tokens, terms, term_count


def get_idf(N, doc_freq):
    '''
    Calculates the inversed document frequency weight idf = log(N/df)

    @params N - The number of document: int
    @params doc_freq - The document frequency for a term: int
    @return weight: float
    '''
    if doc_freq == 0:
        return 0
    else:
        return log(float(N/doc_freq))

def interection(terms, postings_dict):
    ''' perform posting list intersection to retrieve a list of candidate doc IDs '''
    if len(terms) == 0:
        return []
            
    # optimize the order of the merge
    costs = list()
    for term in terms:
        try:
            doc_ids = list(postings_dict[term].keys())
        except: # some might be empty Token, which can go wrong
            doc_ids = []
        costs.append((term, len(doc_ids)))
    costs.sort(key = lambda key: key[1])

    # initial result, assigned as the posting list of the first term
    try:
        result = sorted(list(postings_dict[costs[0][0]].keys()))
    except:
        result = []

    ''' perform pairwise merge '''
    for i in range(1, len(costs)):
        term = costs[i][0]

        try:
            postings = sorted(list(postings_dict[term].keys()))
        except:  # some might be empty Token, which can go wrong
            postings = []

        p1 = p2 = 0
        len1, len2 = len(result), len(postings)
        temp = array.array('i')
        while p1 < len1 and p2 < len2:
            doc1 = result[p1]
            doc2 = postings[p2]
            if doc1 == doc2:
                temp.append(doc1)
                p1, p2 = p1 + 1, p2 + 1
            elif doc1 < doc2:
                p1 += 1
            else:
                p2 += 1
        result = temp

    return list(result)

def verify(candidate, tokens, postings_dict):
    ''' 
    see if the query is in the candidate file, as the terms 
    should appear one by one, side by side 

    @param candidate The candidate doc IDs
    @param tokens The stemmed words list in the query
    @param postings_dict The dictionary containing the pos info
    '''
    if len(tokens) <= 1:
        return candidate

    positions = defaultdict(dict)
    candidate = set(candidate)

    # get postions for docs
    for i, token in enumerate(tokens):
        try:
            for doc_id, val in postings_dict[token].items():
                if doc_id in candidate:
                    positions[doc_id][i] = val.pos
        except:
            continue

    # judging every doc
    ans = []
    flag = False
    for doc in positions.keys():
        term1_positions = positions[doc][0]
        length = len(positions[doc].keys())
        for pos in term1_positions:
            for i in range(1,length):
                if (pos+i) in positions[doc][i]:
                    flag = True
                else:
                    flag = False
                    break
        if flag == True:
            ans.append(doc)

    return ans


def execute_search(query, dictionary, postings, num_of_doc):
    '''
    Compute cosine similarity between the query and each document, i.e.,
    the lnc tf-idf for the tuples (term, frequency).
    Compute the score for each document containing one of those terms in 
    the query.
    Return (at most) 10 most relavant document id (sorted) by score.

    @param query - The query string: str
    @param dictonary - The dictionary containing the doc frequency of a
                        token: DefaultDict[int, Entry]
    @param postings - The postings dictionary containing a mapping of 
                        doc ID to the weight for a given token: Posting
    @param num_of_doc - The number of the documents indexed
    '''

    '''
    Get tokens (stemmed words in the query), terms (set of tokens), 
    and the dictionary of term frequency in the query: DefaultDict[str, int]
    '''
    tokens, terms, term_freq = get_term_freq(query)
    
    if phrasal_query:
        doc_candidate = interection(terms, postings)
        doc_to_rank = verify(doc_candidate, tokens, postings)


    # Compute cosine similarity between the query and each document,
    # with the weights follow the tf×idf calculation, and then do
    # normalization
    query_weight = normalize([get_tf(freq) * get_idf(num_of_doc, dictionary[term].frequency)
                            for (term, freq) in term_freq.items()])

    # Compute the score for each document containing one of those
    # terms in the query.
    score = Counter()
    for ((term, _), q_weight) in zip(term_freq.items(), query_weight):
        if q_weight > 0:
            ''' get the postings lists of the term, update the score '''
            for doc_id, value in postings[term].items():
                if phrasal_query and (doc_id not in doc_to_rank):
                    continue
                score[doc_id] += q_weight * value.weight

    ''' rank and get result '''
    return [doc_id for (doc_id, _) in score.most_common()]


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    with open(dict_file, mode="rb") as dictionary_file,\
            open(postings_file, mode="rb") as posting_file,\
            open(queries_file, encoding="utf8") as q_in,\
            open(results_file, mode="w", encoding="utf8") as q_out:

        ''' 
        load dictionary and postings 
        - num_of_doc -> The number of the documents indexed
        - dict(k,v) -> token, Enftry(frequency, offset, size)
        - postings  -> list of tuples (doc ID, token frequency)
        '''
        num_of_doc = pickle.load(dictionary_file)
        dictionary = pickle.load(dictionary_file)
        postings = Posting(dictionary, posting_file)

        ''' 
        process query, and write the query result (i.e., the 10 
        most relevant doc IDs) to the result file 
        '''
        for query in q_in:
            print(*execute_search(query, dictionary,
                                  postings, num_of_doc), end='\n', file=q_out)


def usage():
    # test on my PC: $python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt
    # test on my PC: $python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt -x
    print("usage: " +
          sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")
    print("tips:\n"
          "  -d  dictionary file path\n"
          "  -p  postings file path\n"
          "  -q  queries file path\n"
          "  -o  search results file path\n"
          "  -x  enable phrasal query\n")

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:x')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
