#!/usr/bin/python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from nltk.util import pad_sequence
from nltk.util import ngrams
import sys
import getopt
import string
import math

def preprocess(text):
    # remove punctuations
    remove_punctuations = text.translate(
        str.maketrans("", "", string.punctuation))
    # remove digits
    remove_digits = remove_punctuations.translate(
        str.maketrans("", "", string.digits))
    # lowercase letter
    result = remove_digits.lower()
    return result

def build_LM(in_file):
    """
    build language models for each label
    each line in in_file contains a label and a string separated by a space
    """
    print('building language models...')
    # This is an empty method
    # Pls implement your code in below

    '''
    Labeling the training data
    split sentence to 4-gram
    padding at the beginning and the end
    '''
    malay_corpus = list()
    indon_corpus = list()
    tamil_corpus = list()
    vocabulary = dict() # total vocabulary
    
    fp = open(in_file, "r")
    while True:
        line = fp.readline()
        if not line: 
            break

        line_clean = preprocess(line)

        # Exclude label, split sentence
        label = line_clean.split(" ", 1)[0]
        sentence = line_clean.split(" ", 1)[1]

        # remove excess space due to deletion of punctuations and digits
        integrated = ' '.join(sentence.split())

        # Split sentence into single characters
        text = list(integrated)
        
        # 4-gram LM with beginning and end padding
        padded_sent = list(pad_sequence(text,
                        pad_left=True, left_pad_symbol="<s>",
                        pad_right=True, right_pad_symbol="</s>",
                        n=4))
        padded_list = list(ngrams(padded_sent, n=4))
            
        # Add one smoothing
        for item in padded_list:
            if item not in vocabulary:
                vocabulary[item] = [1,1,1]
        
        if (label == "malaysian"):
            malay_corpus.append(padded_list)
        elif (label == "indonesian"):
            indon_corpus.append(padded_list)
        elif (label == "tamil"):
            tamil_corpus.append(padded_list)
    
    fp.close()

    # size of distinct 4-grams in training data
    tot = len(vocabulary)

    '''
    dictionary vocabulary
    key: such as ('S', 'a', 'm', 'e')
    value: [#(malay), #(indon), #tamil, #(random/other)]
    '''
    cnt_m = tot
    cnt_i = tot
    cnt_t = tot
    for sentence in malay_corpus:
        for chars in sentence:
            cnt_m += 1
            vocabulary[chars][0] += 1   
    for sentence in indon_corpus:
        for chars in sentence:
            cnt_i += 1
            vocabulary[chars][1] += 1
    for sentence in tamil_corpus:
        for chars in sentence:
            cnt_t += 1
            vocabulary[chars][2] += 1

    # Normalize with add-one-smoothing
    for key in vocabulary.keys():
        lst = vocabulary[key]
        new_lst = [lst[0]/cnt_m, lst[1]/cnt_i, lst[2]/cnt_t, 1/tot]
        vocabulary[key] = new_lst
    return vocabulary

def test_LM(in_file, out_file, LM):
    """
    test the language models on new strings
    each line of in_file contains a string
    you should print the most probable label for each string into out_file
    """
    print("testing language models...")
    # This is an empty method
    # Pls implement your code in below

    '''
    multiply the probabilities of the 4-grams for this string, 
    and return the label (i.e., malaysian, indonesian, and tamil) 
    that gives the highest product. 
    Ignore the four-gram if it is not found in the LMs.
    '''
    fp = open(in_file, "r")
    fo = open(out_file, "w")
    while True:
        line = fp.readline()
        if not line: break

        line_clean = preprocess(line)

        # remove excess space due to deletion of punctuations and digits
        integrated = ' '.join(line_clean.split())

        # Split sentence into single characters
        text = list(integrated)
        # 4-gram LM with beginning and end padding
        padded_sent = list(pad_sequence(text,
                                        pad_left=True, left_pad_symbol="<s>",
                                        pad_right=True, right_pad_symbol="</s>",
                                        n=4))
        padded_list = list(ngrams(padded_sent, n=4))
        
        # the initial prob should be 1, but we take logarithm 
        # as prob can be very small float number
        prob_m = 0  # prob of malaysian
        prob_i = 0  # prob of indonesian
        prob_t = 0  # prob of tamil
        prob_r = 0  # random model probability, used to determine other languages
        num_r = 0   # number of unseen four-grams
        num = 0     # number of total four-grams
        for four_gram in padded_list:
            num += 1
            if four_gram not in LM.keys():
                # Ignore the four-gram if it is not found in the LMs.
                # pass
                num_r += 1
            else:
                # multiply the probabilities of the 4-grams for this string
                # but in practice we calculate logarithm by addition
                prob_m += math.log(LM[four_gram][0])
                prob_i += math.log(LM[four_gram][1])
                prob_t += math.log(LM[four_gram][2])
                prob_r += math.log(LM[four_gram][3])
            
        '''        
        return the label (i.e., malaysian, indonesian, and tamil)
        that gives the highest product.
        Add label at the beginning of the sentence
        '''
        line_w = ""
        if ((num_r/num > 0.7) or prob_r >= max(prob_m, prob_i, prob_t)):
            line_w = "other " + line
        elif (prob_m >= prob_i) and (prob_m >= prob_t):
            line_w = "malaysian " + line
        elif (prob_i >= prob_m) and (prob_i >= prob_t):
            line_w = "indonesian " + line
        elif (prob_t >= prob_m) and (prob_t >= prob_i):
            line_w = "tamil " + line
        # else:
        #     line_w = "other " + line
        
        # write predicted result into output file
        fo.write(line_w)
    fp.close()
    fo.close()



def usage():
    print("usage: " + sys.argv[0] + " -b input-file-for-building-LM -t input-file-for-testing-LM -o output-file")

input_file_b = input_file_t = output_file = None
try:
    opts, args = getopt.getopt(sys.argv[1:], 'b:t:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)
for o, a in opts:
    if o == '-b':
        input_file_b = a
    elif o == '-t':
        input_file_t = a
    elif o == '-o':
        output_file = a
    else:
        assert False, "unhandled option"
if input_file_b == None or input_file_t == None or output_file == None:
    usage()
    sys.exit(2)

LM = build_LM(input_file_b)
test_LM(input_file_t, output_file, LM)
