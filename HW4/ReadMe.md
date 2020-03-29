Legal Case Retrieval Mini Project
The problem of legal case retrieval with real-world documents and queries. Legal retrieval is a case where structured documents are prevalent, so serve as a good testbed for a variety of different retrieval approaches.

More detail on the inputs: Queries and Cases
The legal cases and the information needs have a particular structure in this task. Let's start with the information needs.

Queries:

In Intelllex's own system, searchers (lawyers or paralegals) use the familiar search bar to issue free text or Boolean queries, such as in the training query q1.txt: quite phone call. and q2.txt: "fertility treatment" AND damages. The keywords enclosed in double quotes are meant to be searched as a phrase. The phrases in the queries are 2 or 3 words long, max; so you if you are able to deal with phrasal queries, you can support them using n-word indices or with positional indices. There are no ORs, NOTs or parentheses in the queries issued by us so you can simplify your query parsing code if you choose.

Query Relevance Assessments:

The query is the first line of the query file. The file also comes with (very few) relevance judgments, as subsequent lines. Each line marks a positive (relevant) legal case identified within the corpus. You should ideally have your system rank documents from the positive list before any other documents. As relevance judgments are expensive (lawyers assigned the judgments made available to you), the bulk of the Intelllex corpus was not assessed for their relevance. That is, there may be additional documents that are relevant in the corpus that are not listed. However, your system will be evaluated only on those documents that have been assessed as relevant. We show the example for the above q1.txt.

quiet phone call
6807771
3992148
4001247
The above indicates that there are 3 documents, with document_ids 6807771, 4001247 and 3992148, that are relevant to the query.

Cases:

The legal cases are given in a csv file. Each case consists of 4 fields in the following format: "document_id","title","content","date_posted","court".

Below are snippets of a document, ID 6807771, a case relevant to the above example query:

"6807771","Burstow R v. Ireland, R v. [1997] UKHL 34","JISCBAILII_CASES_CRIME

JISCBAILII_CASES_ENGLISH_LEGAL_SYSTEM


Burstow R v. Ireland, R v. [1997] UKHL 34 (24th July, 1997) 


HOUSE OF LORDS




��Lord Goff of Chieveley ��Lord Slynn of Hadley 
��Lord Steyn
��Lord Hope of Craighead ��Lord 
Hutton

...

I would therefore answer the certified question in 
the affirmative and dismiss this appeal also.","1997-07-24 00:00:00","UK House of Lords"
You may choose to index or omit title, court, date_posted depending on whether you think they are useful to assessing a case's relevance to the query. More importantly, the content has much structure itself. You may decide to try to treat such work using preprocessing in your indexing if you think you can capitalize on it. Note that different jurisdictions may have differences in formatting, or even a different court's format compared to others.

Zones and Fields
As introduced in Week 8, Zones are free text areas usually within a document that holds some special significance. Fields are more akin to database columns (in a database, we would actually make them columns), in that they take on a specific value from some (possibly infinite) enumerated set of values.

Along with the standard notion of a document as a ordered set of words, handling either / both zones and fields is important for certain aspects of case retrieval.
