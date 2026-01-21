import json
import math
import token
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import jsonlines    
from pathlib import Path

class Websearcher:

    def __init__(self,
                 title_pos_path,
                 desc_pos_path,
                 reviews_path,
                 synonyms_path,
                 origin_path,
                 brand_path):
        self.title_pos = self._load_json(title_pos_path)     
        self.desc_pos = self._load_json(desc_pos_path)       
        self.reviews = self._load_json(reviews_path)
        self.synonyms = self._load_json(synonyms_path)
        self.origin = self._load_json(origin_path)
        self.brand = self._load_json(brand_path)
        self.data = self.read_jsonl("/home/ensai/Documents/Indexation/TpScrawler/TP3/input/rearranged_products.jsonl")
        nltk.download('stopwords')
        nltk.download('punkt')
        self.stop_words = set(stopwords.words('english')) #words we dont want
        self.docs = set()
        for idx in (self.title_pos, self.desc_pos):
            for posting in idx.values():
                self.docs.update(posting.keys())
        # Number of documents
        self.N = len(self.docs)

    def tokenize(self, query):
        """
    Tokenize and normalize a user query.

    Parameters
    ----------
    query : str
        The raw query entered by the user.

    Returns
    -------
    list of str
    """
        
        raw = query.lower().split()
        cleaned = [w.strip('.,!?;"\'()[]{}').lower() for w in raw]
        return [w for w in cleaned if w and w not in self.stop_words] #if the query is not empty and not a stop word...
    
    def _load_json(self, path):
        """
    Load a JSON file from disk.

    Parameters
    ----------
    path : str
        Path to the JSON file.

    Returns
    -------
    dict
        The content of the JSON file.
    """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


    def read_jsonl(self, path):
        """
        Parameter
        ---------
        path: String
            The path of the jsonl

        Return
        ------
        Dict
            A dict containing each document dict with key equals to the url of the document
        """
        data={}
        with open(path, "r") as file:
            for page in file:
                document = (json.loads(page))
                data[document["url"]] = document
        return data
    
    def expand_query(self, tokens):
        """
    Expand a list of query tokens using a synonym dictionary.

    Parameters
    ----------
    tokens : list of str
        List of normalized query tokens.

    Returns
    -------
    set of str
        A set of expanded query tokens including the original terms
        and their synonyms.
    """
        expanded = set(tokens)

        for t in tokens:
            # Case 1: token is a key in the synonyms dictionary
            if t in self.synonyms:
                for syn in self.synonyms[t]:
                    expanded.update(syn.lower().split())

            # Case 2: token appears in a synonym list 
            for key, syns in self.synonyms.items():
                for syn in syns:
                    if t in syn.lower().split():
                        expanded.update(key.lower().split())

        return expanded
    
    def doc_contains_token(self, token, url):
        """
    Check whether a document contains a given token in any indexed field.

    Parameters
    ----------
    token : str
        Query token to be checked.
    url : str
        Id of the document (URL).

    Returns
    -------
    bool
        True if the document contains the token in any field, False otherwise.
    """
        return (url in self.title_pos.get(token, {})) or (url in self.desc_pos.get(token, {}) or url in self.brand.get(token, {}) or
        url in self.origin.get(token, {}))
    
    def has_at_least_one_token(self, tokens, url):
        """
    Check whether a document contains at least one token from a token list.

    Parameters
    ----------
    tokens : iterable of str
        Query tokens.
    url : str
        Id of the document (URL).

    Returns
    -------
    bool
        True if the document (the sppecified indexes) contains at least one token, False otherwise.
    """
        return any(self.doc_contains_token(t, url) for t in tokens)
    
    def has_all_tokens(self, tokens, url):
        """
    Check whether a document contains all tokens from a token list.

    Parameters
    ----------
    tokens : iterable of str
        Query tokens.
    url : str
        Id of the document (URL).

    Returns
    -------
    bool
        True if the document contains all tokens, False otherwise.
    """
        return all(self.doc_contains_token(t, url) for t in tokens)
    
    def is_in_brand(self, token, url):
        """
    Check whether a token appears in the brand field of a document.

    Parameters
    ----------
    token : str
        Query token.
    url : str
        Id of the document (URL).

    Returns
    -------
    bool
        True if the token matches the document brand, False otherwise.
    """
        return url in self.brand.get(token, {})

    def is_in_origin(self, token, url):
        """
    Check whether a token appears in the origin field of a document.

    Parameters
    ----------
    token : str
        Query token.
    url : str
        Id of the document (URL).

    Returns
    -------
    bool
        True if the token matches the document origin, False otherwise.
    """
        return url in self.origin.get(token, {})

    def filter_documents(self, query, mode="OR"):
        """
    Filter candidate documents according to a user query.

    Parameters
    ----------
    query : str
        User query.
    mode : str, optional
        Filtering mode, either "OR" or "AND" (default is "OR").

    Returns
    -------
    set of str
        Set of document id (URLs) that satisfy the filtering criteria.
    """
        tokens = self.expand_query(self.tokenize(query))
        if not tokens:
            return set()
        if mode == "AND":
            return {u for u in self.docs if self.has_all_tokens(tokens, u)}
        return {u for u in self.docs if self.has_at_least_one_token(tokens, u)}

#Ranking

    def idf(self, token, field="desc"):
        """
    Compute the Inverse Document Frequency (IDF) of a token.

    Parameters
    ----------
    token : str
        Query token.
    field : str, optional
        Field to consider ("desc" for description or "title").
        Default is "desc".

    Returns
    -------
    float
        IDF value of the token. Returns 0.0 if the token does not appear
        in any document.
    """
        idx = self.desc_pos if field == "desc" else self.title_pos
        n = len(idx.get(token, {}))
        if n == 0:
            return 0.0
        return math.log(self.N / n)

    
    def _compute_doc_lengths(self, pos_index):
        """
    Compute document lengths and average document length from a positional index.

    Parameters
    ----------
    pos_index : dict
        Positional index mapping tokens to documents and positions.

    Returns
    -------
    tuple
        - dict: document lengths (document URL -> length)
        - float: average document length over the collection
    """
        dl = {}
        for _, posting in pos_index.items():
            for url, positions in posting.items():
                dl[url] = dl.get(url, 0) + len(positions)
        avg = sum(dl.values()) / len(dl) if dl else 0.0
        return dl, avg
    
    def tf(self, token, url, field="desc"):
        """
    Compute the Term Frequency (TF) of a token in a document.

    Parameters
    ----------
    token : str
        Query token.
    url : str
        Identifier of the document (URL).
    field : str, optional
        Field to consider ("desc" for description or "title").
        Default is "desc".

    Returns
    -------
    int
        Number of occurrences of the token in the document.
    """
        idx = self.desc_pos if field == "desc" else self.title_pos
        postings = idx.get(token, {})
        if url not in postings:
            return 0
        return len(postings[url])

    def bm25_doc(self, tokens, url, field="desc", k1=1.2, b=0.75):
        """
    Compute the BM25 score of a document for a given set of query tokens.

    Parameters
    ----------
    tokens : iterable of str
        Query tokens used for scoring.
    url : str
        Identifier of the document (URL).
    field : str, optional
        Field to consider ("desc" for description or "title").
        Default is "desc".
    k1 : float, optional
        Term frequency saturation parameter (default is 1.2).
    b : float, optional
        Document length normalization parameter (default is 0.75).

    Returns
    -------
    float
        BM25 relevance score of the document for the given tokens and field.
    """
    
        if field == "title":
            dl_dict, avg_len = self._compute_doc_lengths(self.title_pos)
        else:
            dl_dict, avg_len = self._compute_doc_lengths(self.desc_pos)
        dl = dl_dict.get(url, 0)
        score = 0.0
        for t in tokens:
            f = self.tf(t, url, field=field)   
            if f == 0:
                continue

            idf = self.idf(t, field=field)
            denom = f + k1 * (1 - b + b * (dl / avg_len if avg_len > 0 else 0.0))
            score += idf * ((f * (k1 + 1)) / (denom if denom > 0 else 1.0))

        return score
    
    def exact_match(self, tokens, document, index):
        """
    Detect an exact consecutive match of query tokens in a document.

    Parameters
    ----------
    tokens : list of str
        Ordered list of query tokens.
    document : str
        Identifier of the document (URL).
    index : dict
        Positional index mapping tokens to documents and positions.

    Returns
    -------
    int
        1 if an exact consecutive match is found, 0 otherwise.
    """
        if len(tokens) < 2:
            return 0

        positions = []
        for t in tokens:
            if t not in index:
                return 0
            if document not in index[t]:
                return 0
            positions.append(set(index[t][document])) 

        for p in positions[0]:
            if all((p + i) in positions[i] for i in range(len(tokens))):
                return 1
        return 0
    
    def linear_scoring(self, base_tokens, expanded_tokens, filtered_documents):
        """
    Compute a linear relevance score for a set of candidate documents.

    Parameters
    ----------
    base_tokens : list of str
        Original query tokens (ordered), used for exact phrase matching.
    expanded_tokens : list of str
        Expanded query tokens (including synonyms), used for scoring.
    filtered_documents : iterable of str
        Set of candidate document identifiers (URLs).

    Returns
    -------
    list of tuple
        List of (score, document URL) pairs, sorted by decreasing score.
    """
        results = []

        for url in filtered_documents:
            score = 0.0

            score += 2.5 * self.bm25_doc(expanded_tokens, url, field="title")
            score += 1.0 * self.bm25_doc(expanded_tokens, url, field="desc")

            score += 10.0 * self.exact_match(base_tokens, url, self.title_pos)
            score += 2.0 * self.exact_match(base_tokens, url, self.desc_pos)

            score += 2.0 * self.has_all_tokens(base_tokens, url)

            #brand/origin
            brand_hits  = sum(1 for t in expanded_tokens if self.is_in_brand(t, url))
            origin_hits = sum(1 for t in expanded_tokens if self.is_in_origin(t, url))
            score += 4.0 * brand_hits
            score += 6.0 * origin_hits

            r = self.reviews.get(url, {})
            nb = r.get("nb_ratings", 0)
            avg = r.get("avg_rating", 0)
            score += math.log(1 + nb) * avg * 0.5

            results.append((score, url))

        results.sort(key=lambda x: x[0], reverse=True)
        return results

    
    def load_docstore(self, jsonl_path):
        """
    Load the document store from a JSONL file.

    Parameters
    ----------
    jsonl_path : str
        Path to the JSONL document store file.

    Returns
    -------
    dict
        Dictionary mapping document URLs to their textual content
        (title and description).
    """
        data = {}
        with jsonlines.open(jsonl_path) as reader:
            for obj in reader:
                url = obj["url"]
                data[url] = {
                    "title": obj.get("title", ""),
                    "description": obj.get("description", "")
                }
        return data
    
    def extract_title_and_description(self, document):
        """
    Extract the title and description of a document.

    Parameters
    ----------
    document : str
        Identifier of the document (URL).

    Returns
    -------
    tuple of str
        The document title and description.
    """
        title = self.data[document]["title"]
        description = self.data[document]["description"]
        return title, description
    
    def search(self, request, mode="OR", top_k=20):
        """
        Run a search query and return ranked results with metadata.

        Parameters
        ----------
        request : str
            User query.
        mode : str, optional
            Filtering mode ("OR" or "AND").
        top_k : int, optional
            Number of top results to return.

        Returns
        -------
        dict
            Dictionary containing search results and metadata.
        """
        metadata = {}

        # Tokenize + expand (keep order for exact match)
        base_tokens = self.tokenize(request)
        expanded_set = self.expand_query(base_tokens)
        print( expanded_set)
        expanded_tokens = [t for t in expanded_set if t and t not in self.stop_words]

        # Filter documents (uses expanded tokens internally)
        filtered_documents = self.filter_documents(request, mode=mode)

        # Rank documents
        scored = self.linear_scoring(base_tokens, expanded_tokens,filtered_documents)

        # Metadata
        metadata["number_of_documents"] = self.N
        metadata["number_of_filtered_documents"] = len(filtered_documents)
        metadata["tokens"] = base_tokens
        metadata["expanded_tokens"] = expanded_tokens
        metadata["mode"] = mode

        # Keep top-k
        scored = scored[:top_k]

        # Build output
        search_result = {}
        for score, doc in scored:
            title, description = self.extract_title_and_description(doc)
            search_result[doc] = {
                "rank": score,
                "title": title,
                "description": description
            }

        return {
            "search_result": search_result,
            "metadata": metadata
        }

    def save_search(self, search_result, file_name):
        """
    Save search results to a JSON file.

    Parameters
    ----------
    search_result : dict
        Dictionary containing search results and associated metadata.
    file_name : str
        Name of the output file (without extension).

    Returns
    -------
    None
    """
        out_dir = Path("TP3/output")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{file_name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)



if __name__ == "__main__":
    websearcher = Websearcher(
        title_pos_path="TP3/input/title_index.json",
        desc_pos_path="TP3/input/description_index.json",
        reviews_path="TP3/input/reviews_index.json",
        synonyms_path="TP3/input/origin_synonyms.json",
        origin_path="TP3/input/origin_index.json",
        brand_path="TP3/input/brand_index.json"
    )
    queries = [
        # Simple keywords
        "sandals",
        "candy",
        "sneakers",
        
        # Exact match
        "energy potion",
        "cat-ear beanie",
        
        # Origin / brand tests
        "american cat-ear beanie",
        "italian sneakers",
        
        # Query with no matching documents
        "man",

        #Rare Word
        "versatile sneakers",

        #long query
        "versatile italian sneakers with good reviews"
    ]
    for query in queries:
        search_result = websearcher.search(query)
        websearcher.save_search(search_result, query)

