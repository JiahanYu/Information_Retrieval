## Index:
The indexation is based on my HW #2, which has implemented the in-memory indexing using Pickle for on disk persistence. In indexation, I compute tf and also the weighted tf for each term in each document, so as to speed up the querying (search) part.

## Search:
The query is not boolean expression but refers to full text search. I split the query into stemmed tokens, compute the tf-idf (ltc) for the query term and then apply cosine similarity, storing the intermediate results in Counter in order to retrieve easily the most 10 relevant document IDs.

For preprocessing the query and document words, I did not remove digits, punctuations. They are treated as a term in the dictionary. No lemmatization. What I do only is case-folding, and removing fullstops by using "sent_tokenize" and "word_tokenize" in the tokenising step.

## Experiment:
1. Preprocess: only remove fullstops.
2. Implementation of phrasal search.
