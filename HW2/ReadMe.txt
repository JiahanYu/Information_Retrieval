# Python Version
3.7.6

# General Notes

1. Build index from a list of document stored in the corpus training data directory
2. Use dictionary and postings files, perform searching based on the given queries and output the search result.

# Indexing

(1) Head into directory, and load corpus.
(2) Create a dictionary for storing tokens and their corresponding postings.
(3) Performs preprocessing, tokenization. Lowercase all tokens. Remove all digits.
(4) Perform stemming.
(5) Having stemmed the words, we add the words into the dictionary.
(6) Write the postings file.
(7) Apply the skip pointer.
(8) Write the dictionary file.

# Search
(1) Load dictionary and postings file.
(2) Process query.
(3) Simplify the query expression.
(4) Check if it is already independent of the tokens -- always true or false.
(5) Get split items of the query expression.
(6) Use Shunting-yeard's algorithm, produce a boolean tree of operators with the query terms at the leaf. The algorithem mainly follows steps: first check if it is a empty query. If not, read the split operands and words: 
    - case1: if not operands, add it to output queue
    - case2: if (, put it on stack
    - case3: if ), empty the stack in the queue until find a ( to match, otherwise error
    - case4: if other operands, operand 1 take operand 2 from operand stack when operand 1 <= operand 2 and put operand 2 in queue, then put operand 1 in stack.
If there left some tokens, add them to the queue, unless they are unexpected parenthesis.
(7) Given the boolean tree, evaluate the result by evaluate sub-trees and merge from bottom (the leaf of the boolean tree) to up. In the merge process, consider De Morgan's rule: ~a&~b => ~(a|b) and ~a|~b => ~(a&b).

# utils.py (data structures used for indexing and searching)

1. Entry := an entry of the dictionary, containing the frequency of the token, the offset of the postings file, the size of the list (of docIDs) corresponding inside the postings file.
    -- Entry = namedtuple("Entry", ['frequency', 'offset', 'size'])
    
2. Skiplist := imitate a list of docIDs with skip pointers.

3. Posting := matches dictionary term and postings (docIDs).

4. BooleanTree := represents a query. Can recursively evaluate the itself to return a list of docs that results from the operations. It has sub-classes Node, and Leaf.

# Experiment

1. Stopword removal can affect the query result if stop word is in the query. The result will be nothing matched.

2. For boolean.py, I want to use its classes hiearchy to evaluate the query. Yet I did not finish this part. boolean.py is buggy.

== References ==

1. Shunting's algo in arithmetic: 
http://rosettacode.org/wiki/Parsing/Shunting-yard_algorithm#Python

2. defaultdict(), and how to construct inverted index: 
https://nlpforhackers.io/building-a-simple-inverted-index-using-nltk/

3. boolean.py referenced from: 
https://github.com/bastikr/boolean.py.
