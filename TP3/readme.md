## Modification of the input

The only modification applied to the input data was the addition of **"italy"** and **"italian"** as synonyms in the synonym dictionary.  

This change was introduced after testing a query containing the term *"italian"* and observing that it did not return the expected results. The issue was caused by the absence of a link between the country name and its adjectival form in the synonym dictionary. So I added the synonyms..

## Document Filtering

Before ranking, documents are filtered in order to reduce the search space.
A document is selected if **at least one query token** appears in one of the
following fields:

- title
- description
- brand
- origin

This filtering strategy is intentionally permissive and aims to improve recall.
For example, if a query refers to a product made in a specific country but no
such product exists in the corpus, the system will still return other products
sharing the same origin. The same reasoning applies to brand-based queries.

---

## Signals Used for Ranking

The final relevance score of each document is computed using a **linear
combination of multiple signals**:

- BM25 score on the title
- BM25 score on the description
- Exact match between the query and the title
- Exact match between the query and the description
- Presence of all query tokens in the document
- Presence of query tokens in the brand
- Presence of query tokens in the product origin
- Review-based score


---

## Weighting Choices

The weights associated with each signal were chosen empirically after analysing
the results produced by the example queries in `main.py`.

- **BM25 score on the title × 2.5**  
  The title is the most informative field for determining document relevance.

- **BM25 score on the description × 1**  
  The description is less important than the title, and its raw BM25 score is
  already impactful.

- **Exact match in the title = 10**  
  An exact match in the title strongly boosts the document to the top of the
  ranking.

- **Exact match in the document(any field) = 2**  
  Less important than an exact match in the title, but still helpful to
  distinguish documents.

- **All tokens in the description = 0.5**  
  This signal may occur frequently depending on the query; therefore, its weight
  is kept low to avoid excessive boosting.

- **Token in brand = 4**

- **Token in origin = 6**  
  Brand and origin are considered secondary signals. But it's still significant.

- **Review score × 0.2**  
  Reviews are used only to introduce small differences between very similar
  documents. The raw review score is relatively high, which explains the low
  weight.


---

## Analysis of Results

### Filtered Documents

For well-formed queries (i.e., containing tokens present in the corpus), the
filtering stage typically selects between **10 and 50 documents** out of the
approximately 150 documents in the corpus for the example queries provided in
`websearcher.py`.


### One-Word Queries

BM25 is not a strong indicator for one-word queries. Since all filtered documents
contain the query term, the IDF value is close to zero, resulting in identical
BM25 scores. In this case, the ranking mainly depends on the review-based score.

### Queries with No Matching Documents

If no document satisfies the filtering criteria, the system returns no results. ( just the metadata)

### Exact Phrase Queries

A similar issue occurs for exact phrase queries. However, this limitation is
mitigated by the exact match signals applied to the title and description, which
help differentiate documents.

### Brand and Origin queries

Documents corresponding to both the product and the brand or origin are ranked
first (as we can see with "sneakers" and "italian sneakers" where the order changes), followed by documents matching only the product, and finally documents
matching only the brand or origin.

### Rare word

In this search engine, rare words are mainly handled through the **IDF component**
of the BM25 scoring function. Since the IDF value increases when a token appears
in fewer documents, documents containing rare words receive significantly higher
BM25 scores. It is difficult to provide relevant examples. Indeed, if a word is too rare, the
query may not match any document. Otherwise, the word often appears in
product variant descriptions...
But we can see the difference of ranking between "versatile sneakers" and "sneakers". In the first case, *classic leather sneakers* dominate the ranking, whereas this
is not the case in the second scenario. This clearly illustrates the behavior
described above.


### Long query

Precise and well-specified queries benefit from multiple ranking signals and
lead to a clear separation between relevant and less relevant documents.


---

## Limitations

- The title field may have too much influence on the final ranking. ( But I think it's the most relevant field)
- Synonym handling is limited due to the token-based implementation. For example, during the first implementation there are not "Italian" and "Italy" as synonyms.
- The website used in this project does not contain grammatical or spelling errors.
In a real-world application, handling such errors would be necessary.

## Requirements

The project relies on the following Python packages:

- nltk
- jsonlines
- beautifulsoup4

Install all dependencies with:
pip install -r requirements.txt


## How to Run

1. Make sure all required dependencies are installed

2. Run the search engine:
python TP3/websearcher.py

The search engine loads the pre-built indexes from the TP3/input/ directory and
saves the search results as JSON files in the TP3/output/ directory.


