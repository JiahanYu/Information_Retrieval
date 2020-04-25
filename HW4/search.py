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
from nltk.corpus import wordnet
from uk2us import uk2us

from utils import Entry, Posting, Token, get_tf, normalize, preprocess

try:
    import cPickle as pickle
except ImportError:
    import pickle


phrasal_query = False

lesk_on = False #set for using lesk algorithm
expand = False #set for using query expansion


K_MOST_RELEVANT = 5

def get_term_freq(query):
    ''' 
    Tokenize a given query, do stemming and uk2us translation.
    Count the term frequency in the query

    @param query The query string: str
    @return tokens A list contains all the tokens appeared in the query string: list[str]
            term_count A dictionary where records the counts of the terms in the query: DefaultDict[str: int]
    '''

    global phrasal_query
    # tokenize the query string
    if '"' in query:
        phrasal_query = True
        query= query.strip().lstrip('"').rstrip('"')
    tokens = [word for sent in sent_tokenize(query) for word in word_tokenize(sent)]
    # stem the tokens and do uk2us translation
    ps = PorterStemmer()
    tokens = [ps.stem(uk2us(token.lower())) for token in tokens]
    # tokens = [ps.stem(token.lower()) for token in query.split()]
    # get the term count
    term_count = defaultdict(int)
    for token in tokens:
        term_count[token] += 1

    # get the set of tokens
    terms = list(set(tokens))

    return tokens, terms, term_count

def is_boolean(query):
    '''
    Checks if the given query is boolean or free text
    '''
    return "AND" in query

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

def intersection(terms, postings_dict):
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



def pseudo_rel_feedback(postings,dictionary, most_rel_doc_id, query_weighted, docs_to_terms):
    '''
    implementation of pseudo relevance feedback algorithm,
    takes a list of the most relevant k documents with normal retrieval and uses the terms in them to expand the query
    '''
    feedback ={}
    alpha = 1 # the weight of the original query terms remains the same
    beta = 0.2 # the weight of the added terms from the most relevant documents

    for doc_id in most_rel_doc_id:
        for term in docs_to_terms[doc_id]:
            if term not in feedback:
                feedback[term] = 0
            feedback[term] += postings[term][doc_id].weight #feedback holds the weight for each term in the new query

    prf_query = {}
    for term in query_weighted:
        f = 0
        if term in feedback:
            f = feedback[term]
        prf_query[term] = alpha * query_weighted[term] + beta * f / K_MOST_RELEVANT #adding the modified weights to the existing query terms

    for term in feedback:
        if term not in query_weighted:
            prf_query[term] = beta * feedback[term] / K_MOST_RELEVANT #adding the new query terms

    return prf_query

def execute_search(query, dictionary, postings, num_of_doc, docs_to_terms):
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
        doc_candidate = intersection(terms, postings)
        doc_to_rank = verify(doc_candidate, tokens, postings)

    if lesk_on:
        query = lesk( query)
        print(query)
    if expand:
        query = expand_query(query)
        print(query)
    # Compute cosine similarity between the query and each document,
    # with the weights follow the tf×idf calculation, and then do
    # normalization
    query_weight = normalize([get_tf(freq) * get_idf(num_of_doc, dictionary[term].frequency)
                            for (term, freq) in term_freq.items()])

    # Compute the score for each document containing one of those
    # terms in the query.
    score = Counter()
    query_vector = {}
    for ((term, _), q_weight) in zip(term_freq.items(), query_weight):
        query_vector[term ] = q_weight
        if q_weight > 0:
            ''' get the postings lists of the term, update the score '''
            for doc_id, value in postings[term].items():
                if phrasal_query and (doc_id not in doc_to_rank):
                    continue
                score[doc_id] += q_weight * value.weight
   # return [doc_id for (doc_id, _) in score.most_common(NB_MOST_RELEVENT)]
    ''' rank and get result'''
    most_rel_docs= [doc_id for (doc_id, _) in score.most_common(K_MOST_RELEVANT)]
    new_query = pseudo_rel_feedback(postings,dictionary, most_rel_docs, query_vector,docs_to_terms)
    #print(new_query)
    score = Counter()
    for term in new_query:
        try:
            items = postings[term].items()
        except:
            continue
        for doc_id, freq in items:
            if phrasal_query and (doc_id not in doc_to_rank):
                continue
            score[doc_id] += new_query[term] * value.weight
    return score

def lesk(query):
    '''
    implementing the general Lesk Algorithm, with a slight modification - trying it on every word of the query,
    finding the best context sense for each word taking into consideration the other words in the query,
    and taking the first synonym for that sense to replace the initial word
    ex. big person try
    output: large person attempt
    '''
    words = word_tokenize(preprocess(query, removepunc=True))
    for word in words:
        senses = wordnet.synsets(word)  # Take all WordNet senses of the target word
        if not senses: # if there are no synonyms for this word
            continue
        bestsense = senses[0]  # Initialise as the most frequent sense of the word
        maxOverlap = 0
        sentence = word_tokenize(preprocess(query, removepunc=True))  # Tokenize the query
        for sense in senses:
            gloss = set(word_tokenize(sense.definition())) #adding all the words from the definition of that synonym, to get the gloss of that synonym
            for ex in sense.examples():
                gloss.union(word_tokenize(ex))
            overlap = len(gloss.intersection(sentence))

            for h in sense.hyponyms(): #using hyponyms as well
                gloss = set(word_tokenize(h.definition()))
                for ex in h.examples():
                    gloss.union(word_tokenize(ex))
                overlap += len(gloss.intersection(sentence))

            if overlap > maxOverlap: #choosing the best sense - set of synonyms to be used
                maxOverlap = overlap
                bestsense = sense
        try:
            best_syn = bestsense.lemmas()[0].name() #taking the first synonym for that sense if it exists
        except:
            continue
        if best_syn not in query: #if the synonym chosen was not used we replace it in the query
            query = query.replace(word,best_syn)
    return query



def expand_query(query):
    '''
    expanding the query with one synonym for each word in the query
    ex. big person try
    expanded: big person try large individual attempt
    '''
    split_query = preprocess(query, removepunc=True).split(" ")
    synonyms = []
    cnt = 0
    for word in split_query:
        synonyms.append(word)
    for word in split_query:
        for synonym in wordnet.synsets(word):
            for lemma in synonym.lemmas():
                if cnt < 1:
                    if preprocess(lemma.name()) not in synonyms and '_'not in lemma.name(): #checking that the synonym is not the word itself
                                                                                # or that it is not a combination of two words
                        synonyms.append(lemma.name())
                        cnt += 1
        cnt = 0
    new_query = ' '.join(list(synonyms))
    #synonyms = list(map(lambda syn: syn.replace("_", " "), synonyms))
    return new_query

def normalize_score(max_score, min_score, score):
    """
    normalize a score of a list of scores to range 0 - 1
    """
    return (score - min_score) / (max_score - min_score)

def eval_and(scores1, scores2):
    """
    find intersection of scores1 and scores2:
    add together normalized scores for all doc_ids that exist both in scores1 and scores2, discard the rest
    note: length of scores1 should be less than length of scores2
    note: 0 scores are possible because of normalization
    """
    result = Counter()
    scores1_sorted = scores1.most_common()
    max1 = scores1_sorted[0][1]
    min1 = scores1_sorted[len(scores1) - 1][1]
    scores2_sorted = scores2.most_common()
    max2 = scores2_sorted[0][1]
    min2 = scores2_sorted[len(scores2) - 1][1]
    for doc_id, score1 in scores1_sorted:
        score2 = scores2[doc_id]
        if score2 != 0:
            result[doc_id] = normalize_score(max1, min1, score1) + normalize_score(max2, min2, score2)
    return result

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
        docsInfo = pickle.load(dictionary_file)
        docs_to_terms = pickle.load(dictionary_file)
        dictionary = pickle.load(dictionary_file)
        postings = Posting(dictionary, posting_file)

        ''' 
        process query, and write the query result (i.e., the 10 
        most relevant doc IDs) to the result file 
        '''
        for query in q_in:
            # handle boolean query: split into subqueries
            subqueries = query.split(' AND ')
            subresults = [execute_search(subquery, dictionary, postings, num_of_doc, docs_to_terms) for subquery in subqueries]
            # merge results of subqueries
            subresults.sort(key=len)
            result = []
            while len(subresults) > 1 and len(subresults[0]) != 0:
                subresults[1] = eval_and(subresults[0], subresults[1])
                subresults.pop(0)
            # print result to output file
            result = [doc_id for (doc_id, _) in subresults[0].most_common()]
            print(*result, end='\n', file=q_out)

def usage():
    # test on my PC: $python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt
    # test on my PC: $python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt -x
    print("usage: " +
          sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")
    print("tips:\n"
          "  -d  dictionary file path\n"
          "  -p  postings file path\n"
          "  -q  queries file path\n"
          "  -o  search results file path\n")

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
