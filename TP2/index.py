import jsonlines
import nltk
import json
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from pathlib import Path



class Index:
    def __init__(self):
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
    
    def tokenize(self, text):
        """
        Parameter
        ---------
        text: String
            The original text to tokenize
        
        Return
        ------
        List[String]
            the tokenized version of the text
        """
        return text.lower().split()
    
    def normalize(self, tokens):
        """
        Parameter
        ---------
        tokens: List[String]
            The original tokens to normalize
        """
        tokenizer = RegexpTokenizer(r"[A-Za-z0-9]+")
        tokens_normalized = []
        for token in tokens:
            words = tokenizer.tokenize(token)
            for word in words:
                if word not in self.stop_words:
                    tokens_normalized.append(word)
        return tokens_normalized

    def read_file(self,file):
        """
    Read a JSONL file and load its content into memory.

    Parameters
    ----------
    file : str
        Path to the input JSONL file.

    Returns
    -------
    list of dict
        List of JSON objects read from the file.
    """
        L=[]
        with jsonlines.open(file) as reader:
            for obj in reader:
                L.append(obj)
        return L

    def create_inverted_index_description(self,file):
        """
    Create an inverted index from the description field of the documents.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.

    Returns
    -------
    dict
        Inverted index mapping tokens to lists of document URLs.
    """
        L=self.read_file(file)
        index={}
        for o in L: #objects in the list
            words=self.tokenize(o['description'])
            words=self.normalize(words)
            for w in words:
                if w not in index:
                    index[w]=set()
                    index[w].add((o['url']))
                elif w in index:
                    index[w].add((o['url']))
        for k in index:
            index[k]=list(index[k])
        return index 
    
    def create_inverted_index_title(self,file):
        """
    Create an inverted index from the title field of the documents.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.

    Returns
    -------
    dict
        Inverted index mapping tokens to lists of document URLs.
    """
        L=self.read_file(file)
        index={}
        for o in L:
            words=self.tokenize(o['title'].lower())
            words=self.normalize(words)
            for w in words:
                if w not in index:
                    index[w]=set()
                    index[w].add((o['url']))
                elif w in index:
                    index[w].add((o['url']))
        for k in index:
            index[k]=list(index[k])
        return index 
    
    def extract_reviews(self,product_obj):
        """
    Extract rating values from the reviews of a product.

    Parameters
    ----------
    product_obj : dict
        Dictionary representing a product document.

    Returns
    -------
    list of int or float
        List of rating values extracted from the product reviews.
    """
        return [r["rating"] for r in product_obj.get("product_reviews", []) if "rating" in r]

    def create_index_reviews(self,file):
        """
    Create a reviews index for the documents.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.

    Returns
    -------
    dict
        Dictionary mapping document URLs to review statistics.
    """
        L=self.read_file(file)
        index={}

        for o in L:
            ratings = self.extract_reviews(o)
            index[o["url"]] = {
            "nb_ratings": len(ratings),
            "avg_rating": (sum(ratings)/len(ratings)) if ratings else 0,
            "last_rating": ratings[-1] if ratings else 0
        }
        return index 

    def create_inverted_index_features(self, file, features_to_keep=None):
        """
    Create inverted indexes for selected product features.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.
    features_to_keep : list of str, optional
        List of feature names to index. If None, no feature is indexed.

    Returns
    -------
    dict
        Dictionary mapping each feature name to its corresponding inverted index.
        Each inverted index maps tokens to sorted lists of product identifiers.
    """
        L = self.read_file(file)
        feature_indexes = {feat: {} for feat in features_to_keep}

        for obj in L:
            url = obj.get("url")
            if not url:
                continue

            feats = obj.get("product_features", {}) or {}

            for feat_name in features_to_keep:
                if feat_name not in feats:
                    continue

                # Feature value can be string, number, list... -> stringify
                value = feats[feat_name]
                if isinstance(value, list):
                    text = " ".join(str(x) for x in value)
                else:
                    text = str(value)

                tokens = self.normalize(self.tokenize(text))

                for tok in tokens:
                    feature_indexes[feat_name].setdefault(tok, set()).add(url)

        # Convert sets to sorted lists for JSON compatibility and stable output
        for feat_name in feature_indexes:
            for tok in list(feature_indexes[feat_name].keys()):
                feature_indexes[feat_name][tok] = sorted(feature_indexes[feat_name][tok])

        return feature_indexes
    
    def create_position_index_description(self, file):
        """
    Create a positional inverted index from the description field.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.

    Returns
    -------
    dict
        Positional inverted index of the form:
        token -> {document_url: [positions]}.
    """
        L = self.read_file(file)

        pos_index = {} 

        for o in L:
            url = o["url"]
            words = self.tokenize((o.get("description") or "").lower())
            words = self.normalize(words)
            position = 0
            for w in words:

                if w not in pos_index:
                    pos_index[w] = {}
                if url not in pos_index[w]:
                    pos_index[w][url] = []

                pos_index[w][url].append(position)
                position += 1

        return pos_index
    
    def create_position_index(self, file, field_name):
        """
    Create a positional inverted index from the title field.

    Parameters
    ----------
    file : str
        Path to the input JSONL file containing the documents.

    Returns
    -------
    dict
        Positional inverted index of the form:
        token -> {document_url: [positions]}.
    """
        L = self.read_file(file)
        pos_index = {}

        for o in L:
            url = o["url"]
            tokens = self.tokenize(o.get(field_name, ""))

            pos = 0
            for tok in tokens:
                if tok in self.stop_words:
                    pos += 1
                    continue
                pos_index.setdefault(tok, {}).setdefault(url, []).append(pos)
                pos += 1

        return pos_index

    
    def save_index(self, index_obj, out_path):
        """
    Save an index structure to a JSON file.

    Parameters
    ----------
    index_obj : dict
        Index structure to be saved.
    out_path : str
        Path to the output JSON file.
    """
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(index_obj, f, ensure_ascii=False, indent=2)

    

index = Index()
index_rewiews = index.create_index_reviews("/home/ensai/Documents/Indexation/TpScrawler/TP2/input/products.jsonl")
print("Index reviews créé:", index_rewiews)

if __name__ == "__main__":

    input_file = "/home/ensai/Documents/Indexation/TpScrawler/TP2/input/products_with_id.jsonl"
    output_dir = "/home/ensai/Documents/Indexation/TpScrawler/TP2/output"

    index = Index()

    # Inverted indexes
    index_title = index.create_inverted_index_title(input_file)
    index_desc = index.create_inverted_index_description(input_file)

    # Reviews index
    index_reviews = index.create_index_reviews(input_file)

    # Features inverted index
    feature_indexes = index.create_inverted_index_features(
        input_file,
        features_to_keep=["brand", "origin", "material", "size"]
    )

    # Positional indexes
    pos_index_title = index.create_position_index(input_file, "title")
    pos_index_desc = index.create_position_index(input_file, "description")

    # Save all indexes
    index.save_index(index_title, f"{output_dir}/inverted_title.json")
    index.save_index(index_desc, f"{output_dir}/inverted_description.json")
    index.save_index(index_reviews, f"{output_dir}/reviews.json")
    index.save_index(pos_index_title, f"{output_dir}/positional_title.json")
    index.save_index(pos_index_desc, f"{output_dir}/positional_description.json")

    index.save_index(feature_indexes["brand"], f"{output_dir}/brand_index.json")
    index.save_index(feature_indexes["origin"], f"{output_dir}/origin_index.json")
    index.save_index(feature_indexes["material"], f"{output_dir}/material_index.json")
    index.save_index(feature_indexes["size"], f"{output_dir}/size_index.json")

        