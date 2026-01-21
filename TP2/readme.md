This project implements several indexing structures from a web crawl of product
pages. The input data is obtained from "https://github.com/PeriLara/TP_ENSAI/tree/main/TP2/input".
Then, we modify this input and we obtain the same with the product ids.

## Requirements

The project relies on the following Python packages:

- nltk
- jsonlines
- beautifulsoup4

Install all dependencies with:
pip install -r requirements.txt

## How to Run


1. Preprocess the crawled data:
```bash
python TP2/pre-traitement.py
```

2. Build the indexes (TP2):
```bash
python TP2/index.py
```

All generated indexes are saved in the `TP2/output/` directory.

## My Implementation Choices

- URL preprocessing (extraction of `id_product` and `variant`) is performed in a
  separate preprocessing script.
- An object-oriented approach is used: all indexing logic is implemented in a
  single `Index` class.
- Stopwords are removed using the NLTK stopwords corpus.
- Positional indexes for title and description are built separetly of the corresponding inverted_index(and not in the first method)
- Feature indexing is generic and allows adding new features easily.
- Each index is saved in a separate JSON file.

## Index Structure obtained

### Title Positional Index

This is a positional inverted index built from the `title` field.  
For each token, the index stores the URLs of the documents in which it appears
and the corresponding positions in the title.

Structure:
```json
{
  "token": {
    "document_url": [4]
  }
}
```

### Description Positional Index

This is a positional inverted index built from the `description` field.  
For each token, the index stores the URLs of the documents in which it appears
and the corresponding positions in the description.

Structure:
```json
{
  "token": {
    "document_url": [2, 34]
  }
}
```

### Feature Inverted Indexes

This inverted indexes is built from selected features of the `product_features` field.
Each selected feature has its own inverted index mapping feature tokens to
product identifiers.

#### Selected Features

The following features were selected because they are frequent in the dataset
and relevant for search and filtering:

- brand
- made in
- material
- size

These features are sufficient to identify products efficiently. Variants of the
same product usually share identical feature values, so indexing additional
features would not significantly improve retrieval for this dataset.

Structure:
```json
{
  "feature_token": ["product_id_1", "product_id_2"]
}
```

### Reviews Index

A non-inverted index built from the `product_reviews` field.

For each document, the index stores:
- the number of ratings,
- the average rating,
- the last rating.

Structure:
```json
{
  "document_url": {
    "nb_ratings": 4,
    "avg_rating": 4.75,
    "last_rating": 5
  }
}
```



