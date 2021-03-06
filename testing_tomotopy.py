#Load gensim model

from gensim.corpora import Dictionary
import pickle
from gensim.models import LdaModel

id2word = Dictionary.load('data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_id2word')
with open('data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_corpus.pkl', 'rb') as f:
    corpus = pickle.load(f)

# En drive buscar el archivo topic labeling europe dataset
# https://docs.google.com/spreadsheets/d/1kOvfZeOfVX38CgMkty5NUCrjkUOhAdYc/edit#gid=1118211458

lda_model = LdaModel.load('data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_gensim.model')
lda_model.print_topics()
# Obtener las seeds para tomotopy
last_lda_model_dict_all_terms = dict()
for topic_id in range(lda_model.num_topics):
    last_lda_model_dict_all_terms[topic_id] = dict()
    for word, probability in lda_model.get_topic_terms(topic_id, topn=3):
        last_lda_model_dict_all_terms[topic_id][id2word[word]] = probability*1000

#creating the new topic modeling with tomotopy

import tomotopy as tp
import nltk
import re
import numpy as np
import pyLDAvis

import pandas as pd
file_name = 'english_europe_tweets_20190411.csv'
df  = pd.read_csv('data/cambridge_analytica/regional_datasets/'+file_name)
df.head()

from nltk.corpus import stopwords
stop_words = stopwords.words('english')
stop_words.extend(['linkremoved',' <link removed>','usernameremoved','<usernameremoved>','<linkremoved>','usernameremoved_usernameremoved','linkremoved_linkremoved'])
##stop_words.extend(['from', 'subject', 're', 'edu', 'use'])

try:
    # load if preprocessed corpus exists
    corpus = tp.utils.Corpus.load('preprocessed_cambridge_europe.cps')
except IOError:
    porter_stemmer = nltk.PorterStemmer().stem
    english_stops = set(porter_stemmer(w) for w in stopwords.words('english'))
    pat = re.compile('^[a-z]{2,}$')
    corpus = tp.utils.Corpus(
        tokenizer=tp.utils.SimpleTokenizer(porter_stemmer), 
        stopwords=lambda x: x in english_stops or not pat.match(x)
    )
    print('vamos aqui')
    corpus.process(d.lower() for d in df['texto_completo'].tolist())
    # save preprocessed corpus for reuse
    corpus.save('preprocessed_cambridge_europe.cps')



mdl = tp.LDAModel(min_df=5, rm_top=40, k=11, corpus=corpus)

number_topics = 11


for topic_id, value in last_lda_model_dict_all_terms.items():
    for term, probability in last_lda_model_dict_all_terms[topic_id].items():
        mdl.set_word_prior(term, [1.0 if k == topic_id else 0.1 for k in range(number_topics)])
        print(topic_id, term)

print( 'voy a entrenaaar')
mdl.train(0)

print( '    LOGRE ENTRENAAAR')

print('Num docs:{}, Num Vocabs:{}, Total Words:{}'.format(
    len(mdl.docs), len(mdl.used_vocabs), mdl.num_words
))
print('Removed Top words: ', *mdl.removed_top_words)


# Let's train the model
for i in range(0, 1000, 20):
    print('Iteration: {:04}, LL per word: {:.4}'.format(i, mdl.ll_per_word))
    mdl.train(20)
print('Iteration: {:04}, LL per word: {:.4}'.format(1000, mdl.ll_per_word))

mdl.summary()
