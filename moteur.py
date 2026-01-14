import json
import math
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
nltk.download('stopwords')
nltk.download('punkt')
STOP_WORDS = stopwords.words('english')

class Moteur:

    def __init__(self,indexs):
        self.indexs = ["/home/ensai/Documents/Indexation/TpScrawler/input/brand_index.json"
                       ,"/home/ensai/Documents/Indexation/TpScrawler/input/description_index.json"
                       ,"/home/ensai/Documents/Indexation/TpScrawler/input/origin_index.json"
                       ,"/home/ensai/Documents/Indexation/TpScrawler/input/origin_synonyms.json"
                       ,"/home/ensai/Documents/Indexation/TpScrawler/input/reviews_index.json"
                       ,"/home/ensai/Documents/Indexation/TpScrawler/input/title_index.json"]

    def tokeniser(self, query):
        words = query.lower().split()
        return words
    
    def read_index(self, file):
        with open(file, 'r') as f:
            index = json.load(f)
        return index
    
    def give_synonyms(self, word, file):
        synonyms = []
        with open(file, 'r') as f:
            data = json.load(f)
            for entry in data:
                if entry == word:
                    synonyms = data[entry]
                    return synonyms
                elif word in data[entry]:
                    synonyms.append(entry)
                    synonyms.extend([syn for syn in data[entry] if syn != word])
        return synonyms

    def expand_query(self, query, file):
        expanded_query = set(query)
        for word in query:
            synonyms = self.give_synonyms(word, file)
            for syn in synonyms:
                expanded_query.add(syn)
        return expanded_query
    
    def normalized_query(self, query):
        words = self.tokeniser(query)
        normalized_words = [word.strip('.,!?;"\'()[]{}') for word in words]
        normalized_words = [word for word in normalized_words if word not in STOP_WORDS]
        return normalized_words
    
    def is_there_at_least_one(self, query, document):
        words = self.normalized_query(query)
        words = self.expand_query(words, '/home/ensai/Documents/Indexation/TpScrawler/input/origin_synonyms.json')
        for word in words:
            for file in self.indexs:
                index = self.read_index(file)
                for word in index:
                    if document in index[word]:
                        return True
        return False
    
    def is_there_all(self, query, document  ):
        words = self.normalized_query(query)
        words = self.expand_query(words, '/home/ensai/Documents/Indexation/TpScrawler/input/origin_synonyms.json')
        is_present = False
        for word in words:
            for file in self.indexs:
                index = self.read_index(file)
                for word in index:
                    if document in index[word]:
                        is_present = True
            if not is_present:
                return False
        return True
    
    def filtered_documents(self, query):
        words = self.normalized_query(query)
        words = self.expand_query(words, '/home/ensai/Documents/Indexation/TpScrawler/input/origin_synonyms.json')
        filtered_docs = set()
        index_review = self.read_index('/home/ensai/Documents/Indexation/TpScrawler/input/reviews_index.json')
        for document in index_review:
            if self.is_there_at_least_one(query, document):
                filtered_docs.add(document)
        return filtered_docs
    
    def idf(self, token):
        nb_documents = 150 #faire une fonction pour le nombre de documents
        n=0
        for file in self.indexs:
            index = self.read_index(file)
            if token in index:
                n+=len(index[token])
        idf = 0
        if n>0:
            idf = math.log((nb_documents)/n )
        return idf
    
    def len_document(self, document):
        lenght = 0
        for file in self.indexs:
            index = self.read_index(file)
            for token in index:
                if document in index[token]:
                    lenght += len(index[token])
        return lenght
    
    def avg_doc_len(self):
        total_len = 0
        nb_documents = 150 #faire une fonction pour le nombre de documents
        for file in self.indexs:
            index = self.read_index(file)
            for token in index:
                total_len += len(index[token])
        avg_len = total_len / nb_documents
        return avg_len
    
    def freq(self, token, document): #séparer en deux fonctions
        n_appearance_token = 0
        n_total= self.len_document(document)
        freq = 0
        if n_total>0:
            for file in self.indexs:
                index= self.read_index(file)
                if token in index:
                    if document in index[token]:
                        n_appearance_token = len(index[token][document])
        freq = (n_appearance_token / n_total)*100
        return freq

    def bm25(self, query, index, k1=1.2, b=0.75):
        S=0
        query = self.normalized_query(query)
        query = self.expand_query(query, '/home/ensai/Documents/Indexation/TpScrawler/input/origin_synonyms.json')
        avg_len = self.avg_doc_len()
        for word in query:
            freq = self.freq(word, index)
            idf = self.idf(word)
            len_doc = self.len_document(index)
            S+= idf * ((freq * (k1 + 1)) / (freq + k1 * (1 - b + b * (len_doc / avg_len))))
        return S
        


