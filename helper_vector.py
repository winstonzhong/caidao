'''
Created on 2023年12月6日

@author: lenovo
'''
import gensim
from gensim.models.keyedvectors import KeyedVectors


def convert_to_bin(vec_path):
    wv_from_text = gensim.models.KeyedVectors.load_word2vec_format(vec_path, binary=False)
    wv_from_text.init_sims(replace=True)
    wv_from_text.save(vec_path.replace(".txt", ".bin"))
    
def load_word_vectors(vec_path):
    return KeyedVectors.load(vec_path, mmap='r')


class TxKeyedVectors(object):
    def __init__(self, vec_path):
        self.wv = load_word_vectors(vec_path)
        
        
    def get_vector(self, word):
        return self.wv[word]    
    
    