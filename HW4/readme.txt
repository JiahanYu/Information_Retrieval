In the indexing part, we perform the following operation:

1. UK to US transformation: we set up a dictionary to match
the word in UK English and in US English, then we can use
the function uk2us() defined in uk2us.py to perform the 
transformation.

2. Removing stop words, performing lemmatization, stemming:
after using sent_tokenize() and word_tokenize() to get all tokens, 
we remove all the stop words and perform lemmatization and 
stemming on all of the tokens.

3. Storing term position: we store the term positions in each 
contents, which allow us to perform phasal query in searching
part.

4. Calculating weighted term frequency: we calculate the term
frequency for each term and write them down in posting file, 
so that we can implement vector space model.

5. Storing court name and date: we store the court name and date
of each doc, which allows us to range the searching results by court 
hierarchy and date

The structure of dictionary file is:
len(rows) --- number of rows in dataset
consecutive_ids --- a list of doc ID of each row
docsInfo --- a dictionary recording the court name and date of each doc
dictionary --- a dictionary recording all the terms and its information, key
	is term, value is document frequency and offset in postings file

The structure of postings file is:
 postings --- many dictionaries recording the the information of terms, 
	key is the document ID that the term occurs, value is term positions
	in that document and the weighted term frequency