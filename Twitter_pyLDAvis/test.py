
import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
import numpy as np
from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json
from _display import *
from _prepare import prepare, js_PCoA, PreparedData, _pcoa
from flask import render_template_string
from os import path, walk
from gensim.models.keyedvectors import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
from calculate_topic_similarity import getTopicSimilarityMetric


LdaModel = gensim.models.ldamodel.LdaModel
ruta_word_embedding = '../data/wiki.multi.en.vec'
wordembedding = KeyedVectors.load_word2vec_format(ruta_word_embedding, binary=False)

##Load Gensim Model
lda_model_collecion_1 = LdaModel.load("../data/cambridge_analytica/collection_I/collection_1_gensim.model")
lda_model_collecion_2 = LdaModel.load("../data/cambridge_analytica/collection_I/collection_1_gensim.model")


with open('../data/cambridge_analytica/collection_I/collection_1_sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
    most_relevant_documents_collection_1 = pickle.load(f)
most_relevant_documents_collection_1 = most_relevant_documents_collection_1[['Topic_Num','Topic_Perc_Contrib','text']]


with open('../data/cambridge_analytica/collection_I/collection_1_sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
    most_relevant_documents_collection_2 = pickle.load(f)
most_relevant_documents_collection_2 = most_relevant_documents_collection_2[['Topic_Num','Topic_Perc_Contrib','text']]

topn= 30
print("CALCULANDO MATRIZ")
matriz_ejemplo = getTopicSimilarityMetric(topn, wordembedding, lda_model_collecion_1, most_relevant_documents_collection_1, lda_model_collecion_2, most_relevant_documents_collection_2)
print("FIN CALCULLO MATRIZ")