#!/usr/bin/python3
import getopt
import math
import re
import string
import sys
from collections import defaultdict

import nltk
from nltk.corpus import PlaintextCorpusReader, stopwords
from nltk.stem import PorterStemmer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer, sent_tokenize, word_tokenize

from utils import Entry

try:
    import cPickle as pickle
except ImportError:
    import pickle


def preprocess(text):
    ''' split conjunctions; remove punctuations, digits; case-folding all words '''

    # lowercase letter
    lowercase = text.lower()

    # remove digits
    digit_removed = lowercase.translate(
        str.maketrans("", "", string.digits))

    # split combined words
    # conj_split = re.sub("[-']", " ", digit_removed)

    # remove punctuations
    # punc_removed = conj_split.translate(
    #     str.maketrans("", "", string.punctuation))

    return digit_removed


def tokenize(paragraph):
    ''' tokenization'''
    text = preprocess(paragraph)
    tokenizer = nltk.RegexpTokenizer(r"\w+")
    words = tokenizer.tokenize(text)
    # words = word_tokenize(text)

    return words


def stemming(words, stem=True, stopword=False, lemma=False):
    ''' do stemming, ( stopword removal, lemmatization)'''
    ps = PorterStemmer()
    stemmed_tokens = set()  # multiple term entries in a single document are merged
    for w in words:

        if not stopword:
            stop_words = set()
        else:  # stopword removal
            stop_words = set(stopwords.words("english"))

        if w not in stop_words:
            # stemming
            if not lemma:
                token = ps.stem(w)
            else:
                # lemmatization
                lem = WordNetLemmatizer()
                token = ps.stem(lem.lemmatize(w, "v"))
            stemmed_tokens.add(token)

    return stemmed_tokens


def apply_skippointer(postings):
    ''' insert evenly placed skip pointers in long postings '''

    postings_with_pointer = list(postings)
    postings_with_pointer.sort()
    postings_length = len(postings_with_pointer)

    # for postings with relatively short length(<9), do nothing
    if postings_length > 9:
        cursor = 0
        skip_distance = int(math.floor(math.sqrt(postings_length)))
        while cursor < postings_length:
            if (cursor+skip_distance) >= postings_length:  # add next position the pointer points to
                postings_with_pointer[cursor] = str(
                    postings_with_pointer[cursor]) + ":" + str(postings_with_pointer[-1])
            else:
                postings_with_pointer[cursor] = str(
                    postings_with_pointer[cursor]) + ":" + str(postings_with_pointer[cursor+skip_distance])
            cursor += skip_distance

    return postings_with_pointer


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    ''' head into reuters training data directory '''
    corpus = PlaintextCorpusReader(in_dir, '.*')
    file_names_str = corpus.fileids()  # get list of documents
    file_names = sorted(map(int, file_names_str))

    ''' load corpus '''
    postings = defaultdict(set)
    postings['__all__'] = set(file_names)
    tokens = list()
    for fn in file_names:
        content = corpus.raw(str(fn))  # read file content
        words = tokenize(content)  # tokenization: content -> words
        tokens = stemming(words)  # stemming, singularize
        ''' generate dictionary of (key -> token), (value -> set of document IDs) '''
        for token in tokens:
            postings[token].add(fn)  # add tokens to postings dict

    ''' Output dictionary and postings files '''
    # Dictionary file stores all tokens, with their frequency, offset in the postings file, and size(in bytes)
    # Postings file stores the list of document IDs.

    # write postings file
    dictionary = dict()
    with open(out_postings, mode="wb") as postings_file:
        for key, value in postings.items():
            '''
            len(value) := the frequency of the token(i.e. key)
                        = how many times the token appears in all documents
            offset := current writing position of the postings file
            size := the number of characters written in postings file, in terms of this token
            '''
            offset = postings_file.tell()
            # implement evenly placed skip-pointers in the postings lists
            if key == "__all__": 
                size = postings_file.write(pickle.dumps(value))
            else:
                value_updated = apply_skippointer(value)
                size = postings_file.write(pickle.dumps(value_updated))
            dictionary[key] = Entry(len(value), offset, size)

    # write dictionary file
    with open(out_dict, mode="wb") as dictionary_file:
        pickle.dump(dictionary, dictionary_file)


def usage():
    # command tested on PC:
    # $ python3 index.py -i /Users/yu/nltk_data/corpora/reuters/training/ -d dictionary.txt -p postings.txt
    print("usage: " +
          sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input directory
        input_directory = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
