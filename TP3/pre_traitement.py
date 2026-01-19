import jsonlines
import json
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer


def extract_information(file):
    L=[]
    with jsonlines.open(file) as reader:
        for obj in reader:
            L.append(obj)
    for o in L:
        url=o['url']
        if url.split('/')[-1]!="products" and '?' not in url:
            id_product=url.split('/')[-1] 
        elif '?' in url:
            id_product=url.split('/')[-1].split('?')[0]
        else:
            id_product='No id'
        if len(url.split('/')[-1])<=2 or url.split('/')[-1]=="products":
            variant='No variant'
        else:
            variant=url.split('=')[-1] 
        o['id_product']=id_product
        o['variant']=variant
    return L

def add_information(L):
    with jsonlines.open("/home/ensai/Documents/Indexation/TpScrawler/output/products_with_id.jsonl", mode='w') as writer:
        for o in L:
            writer.write(o)