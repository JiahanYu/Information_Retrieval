== Python Version ==

Using Python Version 3.7.6

== General Notes ==
The project is mainly about how to build index from a list of document stored in the corpus training data directory, as well as using the generated dictionary and postings files to perform searching based on the given queries and output the search result.

For indexing part, it follows the below steps:
(1). Head into data directory and load corpus. Use PlaintextCorpusReader to retrieve all the file names in the directory. Read the file content directly by specifying the file name.
(2). Create a default-dictionary for storing token-postings. Since the default dictionary allows me to specify the "value" type as set(/list), it would be quicker to add distinct file_name in the dictionary. Also, it can perform add operation and does not require assignment when a token is not yet a existed key in the dictionary.
(3). After reading the file content for each file, the program performs preprocessing, tokenization. All terms are in the lowercase, also the digits are removed. Since we would like to have words only, yet word_tokenizer cannot eliminate all punctuations (what it does is actually split but still keep them). So here I used nltk.RegexpTokenizer to get rid of the punctuations. Since all cases are lowered, it is meaningless to have sentence tokenizer since word tokenizer can do at one time. 
(4). After got the tokens, then it will perform stemming as many words are not in the dictionary form. However, in this step, although I implemented the part for stopword removal and lemmatization, but I did not do so since stopword removal would have a great impact on searching. If the query has stopword, then it is very likely that the result postings would be no document IDs. But for lemmatization, actually I did not really know whether it is good to use it or not.
(5). Having stemmed the words, we add the words into the dictionary.
(6). Then we write the postings file using pickle. Here, in order to read convenient for searching stage, I put a key, value tupe as "__all__", all file names (the whole file set/list). As this is quite important information when dealing with NOT query.
(7). For other token and postings, I first apply the skip pointer using appended next position to that document id. For instance, docID#34 points to #78, then I would store the docID#34 as "34:78" rather than 34.
(8). Write the dictionary using pickle, where the key is the token and the value is a Entry which used the namedTuple and consists of three attributes: the frequency of the token, current writing position of the postings file (i.e., later reading position before searching), also how many bytes has been written in the postings file (so that we can read that much before searching).

For searching, it involves four txt file, two files that need to be read from the disk are dictionary file and postings file. The queries file is used to test searching algo, while result file shows the output of the result of given queries. And the searching follows the below steps:
(1). Load dictionary and postings file using pickle. Retrieve the token and the corresponding entry content (frequency, offset, size). According to the info stored in each entry, we seek the corresponding postings in the postings file, store (token, postings) into "Posting" data structure.
(2). Process query, first I substitute AND, OR, NOT to logical symbols, to avoid the situation like "AND and". Also, I repalce the invalid punctuations in the word (I assume it is caused by accident). 
(3). Then I used boolean.py to simplify the query expression so that some repeated patterns, tautologies, or some other complicated forms can be in a much simpler form.
(4). Having got the simplified version of query as a boolean expression, I will first check if it is already independent of the tokens -- it is always true or it is always false, regardless the corresponding postings of the tokens. If the expression is always true, then add all file names as a result. Otherwise, the result should be nothing matched.
(5). For normal query expression, I first split the query into a number of tokens and operands. 
(6). Then use Shunting-yeard's algorithm, produce a boolean tree of operators with the query terms at the leaf. The algorithem mainly follows steps: first check if it is a empty query. If not, read the split operands and words: 
	# - case1: if not operands, add it to output queue
    # - case2: if (, put it on stack
    # - case3: if ), empty the stack in the queue until find a ( to match, otherwise error
    # - case4: if other operands, operand 1 take operand 2 from operand stack when operand 1 <= operand 2 and put operand 2 in queue, then put operand 1 in stack.
If there left some tokens in the end, then add them to the queue, unless they are unexpected parenthesis.
(7). For the produced boolean tree, the program evaluate the result by evaluate sub-trees and merge from bottom (the leaf of the boolean tree) to up. In the merge process, it would consider De Morgan's rule: ~a&~b => ~(a|b) and ~a|~b => ~(a&b).

In the utils.py, there are several data structure used for indexing and searching.
(1). Entry is an entry of the dictionary, containing the frequency of the token, the offset of the postings file, the size of the list (of docIDs) corresponding inside the postings file.
	# Entry = namedtuple("Entry", ['frequency', 'offset', 'size'])
(2). Skiplist is a data structure that imitate a list of docIDs with skip pointers.
(3). Posting is a data structure that matches dictionary term and postings (docIDs).
(4). BooleanTree is a data structure that for each one it represents a query. It can recursively evaluate the itself to return a list of docs that results from the operations. It has sub-classes Node and Leaf where Leaf is the bottom side with no sub-tree at left and right.

Experiment
(1). Stopword removal can affect the query result if stop word is in the query. The result will be nothing matched.
(2). For boolean.py, I want to use its classes hiearchy to evaluate the query. Yet I did not finish this part. boolean.py is buggy.

== References ==

1. Shunting's algo in arithmetic:
http://rosettacode.org/wiki/Parsing/Shunting-yard_algorithm#Python

2. Know about defaultdict() in this web page, and found it quite useful
https://nlpforhackers.io/building-a-simple-inverted-index-using-nltk/

3. boolean.py referenced from https://github.com/bastikr/boolean.py.
