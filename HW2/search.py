#!/usr/bin/python3
import getopt
import re
import string
import sys

import boolean
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer

from utils import Entry, Leaf, Node, Posting, Skiplist, BooleanTree

try:
    import cPickle as pickle
except ImportError:
    import pickle

OPERATORS = {'~': 3, '&': 2, '|': 1,
             '(': 0, ')': 0}  # operators and precedences


def normalize(word, stem=True, stopword=False, lemma=False):
    word = str(word)
    token = ""
    if "invalidpunct" in word:
        word = word.replace("invalidpunct", "")
    if word == "":
        return "IGNORE"
    ''' do stemming, ( stopword removal, lemmatization)'''
    ps = PorterStemmer()
    stemmed_tokens = set()  # multiple term entries in a single document are merged
    if not stopword:
        stop_words = set()
    else:  # stopword removal
        stop_words = set(stopwords.words("english"))

    if word not in stop_words:
        # stemming
        if not lemma:
            token = ps.stem(word)
        else:
            # lemmatization
            lem = WordNetLemmatizer()
            token = ps.stem(lem.lemmatize(word, "v"))
    else:
        token = "IGNORE"

    return token


def preprocess_query(q):

    # avoid case like "AND and"
    replacements = {'AND': ' & ', 'NOT': ' ~ ', 'OR': ' | ', ':': '', ',': '',
                    '!': 'INVALIDPUNCT', '"': 'INVALIDPUNCT', "#": "INVALIDPUNCT", "$": "INVALIDPUNCT", "%": "INVALIDPUNCT", "{": "INVALIDPUNCT", "'": "INVALIDPUNCT",
                    "*": "INVALIDPUNCT", "+": "INVALIDPUNCT", "^": "INVALIDPUNCT", "/": "INVALIDPUNCT", ".": "INVALIDPUNCT", ",": "INVALIDPUNCT", ":": "INVALIDPUNCT",
                    "<": "INVALIDPUNCT", "=": "INVALIDPUNCT", ">": "INVALIDPUNCT", "?": "INVALIDPUNCT", "@": "INVALIDPUNCT", "[": "INVALIDPUNCT", "}": "INVALIDPUNCT",
                    "`": "INVALIDPUNCT", "]": "INVALIDPUNCT", "-": "INVALIDPUNCT", '\\': 'INVALIDPUNCT', ";": "INVALIDPUNCT"}
    q_math = re.sub('({})'.format('|'.join(map(re.escape, replacements.keys()))),
                    lambda m: replacements[m.group()], q)

    return q_math


def process_token(token):
    if token not in OPERATORS:
        return normalize(token)
    else:
        return token


def get_input(query):
    repeat_case = {"(": " ( ", ")": " ) ", "&": " & ", "~": " ~ ", "|": " | "}
    q = re.sub('({})'.format('|'.join(map(re.escape, repeat_case.keys()))),
               lambda m: repeat_case[m.group()], query)
    return list(q.split())


def add_node(output, operator):
    ''' add a Node into output queue, and add previous Node as operands '''
    if operator != '~':
        right, left = output.pop(), output.pop()
        output.append(Node(left, right, operator))
    else:
        output.append(Node(output.pop(), None, operator))


def shunting(tokens):
    ''' based on Shunting-yard_algorithm, produce a tree of operators with the query terms at the leaf '''

    # empty query
    if len(tokens) == 0:
        return Leaf('__Empty__')

    # read tokens
    # - case1: if not operands, add it to output queue
    # - case2: if (, put it on stack
    # - case3: if ), empty the stack in the queue until find a ( to match, otherwise error
    # - case4: if other operands, o1 take o2 from op stack when op1 <= op2 and put o2 in queue,
    #          then put o1 in stack

    outq = []  # output queue
    stack = []
    for token in tokens:
        if token not in OPERATORS:
            outq.append(Leaf(token))  # add term to outq
        elif token == '(':
            stack.append(token)
        elif token == ')':
            pop = ''
            while len(stack) != 0 and pop != '(':
                pop = stack.pop()
                if pop != '(':
                    add_node(outq, pop)
            if pop != '(':
                raise Exception("Mismatching parenthesis", pop, stack)
        else:
            while len(stack) != 0:
                pop = stack.pop()
                if OPERATORS[token] <= OPERATORS[pop]:
                    add_node(outq, pop)
                else:
                    stack.append(pop)
                    break
            stack.append(token)

    # if left some tokens, add to queue
    # unless unexpected parenthesis
    while len(stack) > 0:
        if stack[-1] in "()":
            raise Exception("Unexpected parenthesis!")
        else:
            add_node(outq, stack.pop())

    return outq.pop()


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

        ''' load dictionary and postings '''
        # dict(k,v) -> token, Entry(frequency, offset, size)
        # postings -> the dict containing the entries and metadata of the postings file
        # skiplist -> list of all doc IDs
        dictionary = pickle.load(dictionary_file)
        postings = Posting(dictionary, posting_file)
        file_list = postings['__all__']

        ''' process query, and write the query result to result file '''
        for query in q_in:
            query = preprocess_query(query)
            algebra = boolean.BooleanAlgebra()
            # Simplify query, e.g. tautology
            expression = algebra.parse(query, simplify=True)
            # special cases after simplification
            if str(expression) == "0":
                print("", end='\n', file=q_out)
                continue
            elif str(expression) == "1":
                print(" ".join(map(str, file_list)), end='\n', file=q_out)
                continue

            print(" ".join(map(str, shunting(get_input(str(expression))).eval(
                postings, file_list).list)), end='\n', file=q_out)

            # add posting skiplist and list of all docIDs to corresponding symbol
            # for sym in expression.symbols:
            #     if normalize(sym) == "IGNORE":
            #         norm_sym = str(normalize(sym))
            #         setattr(sym, "obj", norm_sym)
            #         setattr(sym, "skiplist", postings[norm_sym])
            #         setattr(sym, "list", postings[norm_sym].list)
            #         setattr(sym, "file_list", file_list.list)

            # evaluate the query
            # args[]: list of sub-terms
            # For symbols and base elements this tuple is empty,
            # for boolean functions it contains one or more symbols, elements or sub-expressions.
            # print(" ".join(map(str, expression.evaluate_query(expression.args).list)),
            #       end='\n', file=q_out)


def usage():
    # test on my PC: $python3 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt
    print("usage: " +
          sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
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
