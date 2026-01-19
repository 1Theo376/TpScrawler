import jsonlines
import nltk
import json
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
nltk.download('stopwords')
nltk.download('punkt')


class Index:
    pass

    def __init__(self):
        pass
    
    def read_file(self,file):
        L=[]
        with jsonlines.open(file) as reader:
            for obj in reader:
                L.append(obj)
        return L

    def create_inverted_index_description(self,file):
        L=self.read_file(file)
        stop_words = set(stopwords.words('english'))
        index={}
        tokenizer = RegexpTokenizer(r'\w+|\$[\d\.]+|\S+')
        for o in L:
            words=tokenizer.tokenize(o['description'].lower())
            for w in words:
                if w not in index and w not in stop_words and w not in ',.?;"-{()}!:':
                    index[w]=set()
                    index[w].add((o['url']))
                elif w in index and w not in stop_words and w not in ',.?;"-{()}!:':
                    index[w].add((o['url']))
        return index 
    
    def create_inverted_index_title(self,file):
        L=self.read_file(file)
        stop_words = set(stopwords.words('english'))
        index={}
        tokenizer = RegexpTokenizer(r'\w+|\$[\d\.]+|\S+')
        for o in L:
            words=tokenizer.tokenize(o['title'].lower())
            for w in words:
                if w not in index and w not in stop_words and w not in ',.?;"-{()}!:':
                    index[w]=set()
                    index[w].add((o['url']))
                elif w in index and w not in stop_words and w not in ',.?;"-{()}!:':
                    index[w].add((o['url']))
        for k in index:
            index[k]=list(index[k])
        return index 
    
    def extract_reviews(self,file):
        L=self.read_file(file)
        ratings=[]
        for o in L:
            for r in o["product_reviews"]:
                ratings.append(r['rating'])
        return ratings

    def create_index_reviews(self,file):
        L=self.read_file(file)
        index={}
        ratings = self.extract_reviews(file)
        for o in L:
            index[o['url']]={"nb_ratings":len(ratings), "avg_rating": sum(ratings)/len(ratings) if len(ratings)>0 else 0, "last_rating": ratings[-1] if len(ratings)>0 else 0}
        return index 

    def create_inverted_index_features(self, file, features_to_keep=[]):
        L=self.read_file(file)
        stop_words = set(stopwords.words('english'))
        index={}
        indexes=[]
        tokenizer = RegexpTokenizer(r'\w+|\$[\d\.]+|\S+')
        for feature in features_to_keep:
            index={}
            for o in L:
                if feature in o["product_features"]:
                    words = o["product_features"][feature] #en faire une fonction
                    words = tokenizer.tokenize(words.lower())
                    for w in words:
                        if w not in index and w not in stop_words and w not in ',.?;"-{()}!:':
                            index[w]=set()
                            index[w].add(o['url'])
                        elif w in index and w not in stop_words and w not in ',.?;"-{()}!:':
                            index[w].add(o['url'])
            for k in index:
                index[k]=list(index[k])
            indexes.append(index)

        return indexes
    
    def create_position_index_description(self, file): #fusionner , pas fini
        L=self.read_file(file)
        index_description = self.create_inverted_index_description(file)
        stop_words = set(stopwords.words('english'))
        tokenizer = RegexpTokenizer(r'\w+|\$[\d\.]+|\S+')
        for index_word in index_description:
            for link in index_description[index_word]:
                index_description[index_word][link]=list(set())

        for o in L:
            position = 0
            words= tokenizer.tokenize(o['description'].lower())
            for word in words:
                if word not in stop_words and word not in ',.?;"-{()}!:':
                    index_description[word][o['url']]=[]
                    index_description[word][o['url']].append(position)
                    position += 1
        return index_description
    

index = Index()
index_description2 = index.create_position_index_description("/home/ensai/Documents/Indexation/TpScrawler/input/products.jsonl")
print(index_description2)
                


        