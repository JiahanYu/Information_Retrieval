## Web Crawler 
website crawled: https://en.wikipedia.org/wiki/Category:Indexes_of_computer_topics

Structure of crawled website: (altogether 2447 websites)

(1) Main: https://en.wikipedia.org/wiki/Category:Indexes_of_computer_topics

(2) Sub-Main linked to Main:

https://en.wikipedia.org/wiki/Index_of_Android_OS_articles

https://en.wikipedia.org/wiki/Index_of_articles_related_to_BlackBerry_OS

https://en.wikipedia.org/wiki/Index_of_Internet-related_articles

https://en.wikipedia.org/wiki/Index_of_JavaScript-related_articles

https://en.wikipedia.org/wiki/Index_of_robotics_articles

(3) Articles linked to Sub-main, such as:

https://en.wikipedia.org/wiki/Mascot

https://en.wikipedia.org/wiki/Android_(operating_system)

https://en.wikipedia.org/wiki/Android_Debug_Bridge

command to run crawler:

$ python3 crawler.py -a 2447 -i 5 -o cs_articles https://en.wikipedia.org/wiki/Category:Indexes_of_computer_topics

It will generate a linking graph, recording of visited websites, and crawled data (text only).

The crawled data contains: title, anchor text, and content (text). 

## Compute Pagerank
command to compute page rank: (input file is set as linking_graph.txt, output file is pagerank.txt)

$ python3 compute_pagerank.py

It then give the ranked page list, following the format of:

(docID calculation) #inlink #outlink. For instance,

('0', 0.2812376557281807) 5 0 

('5', 0.186652196087094) 1380 1 

('3', 0.05813405077960963) 429 1 

('4', 0.0388090299815346) 286 1 

('1', 0.026646429479249494) 196 1 

('2', 0.020429989222525896) 150 1 

('6', 0.00015898838538377897) 0 1 

('7', 0.00015898838538377897) 0 1 

...

So we know that website No.1,6,4,5,2,3 has higher page rank. (Note that output indexing starts from 0, yet the website txt file name starts from 1)


## INDEXING 

command to run indexing:  (-x means supporing query phrasal)

$ python3 index.py -i cs_articles -d dictionary.txt -p postings.txt -x  

1. Read crawled data: using PlaintextCorpusReader

2. Store title, anchor text as document info, writing into dictionary.txt.

3. UK to US transformation.

4. Tokenize the words using sentence and word tokenizer.

5. Stem the words, without removing stopwords and lemmatization (but they are supported if want to do so).

6. Store the term positions in each contents, which allow us to perform phasal query in searching part.

7. Calculate weighted term frequency for each term and write in posting file, which will be used for calculating tf-idf in the searching part.


A. The structure of dictionary file is:

total number of distinct document ids

docsInfo --- a dictionary recording the title and anchor text

dictionary --- a dictionary recording all the terms and its information, key is term, value is document frequency, offset, size in postings file

B. The structure of postings file is:

postings --- many dictionaries recording the the information of terms, 

key is the document ID that the term occurs, value is term positions in that document and the weighted term frequency


## SEARCHING 

command to run search:  (-x means supporing query phrasal)

$ python3 search.py -d dictionary.txt -p postings.txt -q q1_1.txt -o output_q1_1.txt -x

In the main implementation of the Search Algorithm, we will be ranking the documents by lnc.ltc ranking scheme (similar to that of HW3). 

## Ranking by lnc.ltc ranking scheme
The documents will be ranked according to the lnc.ltc ranking scheme.

That is to say that the weights of each term in the document will be calculated as: (1 + log10(term_frequency_in_documents))
whereas the weights of each term in the query will be calculated as: tf-idf = (1 + log(term_frequency_in_query)) * log(number_of_documents / document_frequency)

After that, cosine normalization will be applied to the weights of each term in both the query and the document, and the dot product of the weights of the terms in the query and the weights of the terms in the documents will give us a score.

## VSM Model with Freetext Queries
All types of queries are now considered as FreeText, except for double quoted phrases which are meant to be searched as a phrase.

## Process used Lesk; implement query expansion 

1. Read query and preprocess query. Get the frequency of terms in the query. Special treatment with phrases in the query.

2. If a query only consists of phrases, then we do not perform Lesk algo and query expansion.

3. Otherwise, we try Lesk algo -- trying it on every word of the query, finding the best context sense for each word taking into consideration the other words in the query, and taking the first synonym for that sense to replace the initial word. I implemented query expansion yet not used, as the articles are mainly technical words. Query expansion is more suitable to use on daily words. (In this case, it will expand query into very generalized ones.)

4. Use the new query after applying Lesk algo. 
	
  (1) if it contains phrases, then we find all document candidates who have the terms of the phrases and verify by checking their	positions. So we can get possible document to be ranked later.
	
  (2) Otherwise, the document candidate should be the whole set.

5. Compute cosine similarity between the query and each document with the weights follow the tf×idf calculation, and then do normalization.

6. Compute the score for each document containing one of those terms in the query. Rank doc ids by score. 

7. Shuffle the result according to the page rank we obtained.

8. Output file that contains ranked relevant doc ids with urls.

Notes: 

1. No boolean queries

2. Zones and fields: I considered and implemented usage of title, anchor text as zones and fields, yet I did not use them in the searching. What I want to do is: if the term in the query is in the title or anchor text of the document, then this document is supposed to have higher rank.

However, this one would require to generate docs_to_term dictionary in indexing (which can makes faster in searching). But if do so, the dictionary is very large. Also, as what I crawled are many special terms, which this implementation may not make much difference. 

## Python Version

Python 3.7.6
