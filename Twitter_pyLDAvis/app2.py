# -*- coding: utf-8 -*-

import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
import numpy as np
from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json
from _display import *
from _prepare import prepare, js_PCoA, PreparedData
from flask import render_template_string
from os import path, walk
from gensim.models.keyedvectors import KeyedVectors


###BORRAR ESTE CODIGO
"""
Topic Models (e.g. LDA) visualization using D3
=============================================

Functions: General Use
----------------------
:func:`prepare`
    transform and prepare a LDA model's data for visualization

:func:`prepared_data_to_html`
    convert prepared data to an html string

:func:`show`
    launch a web server to view the visualization

:func:`save_html`
    save a visualization to a standalone html file

:func:`save_json`
    save the visualization JSON data of to a file


Functions: IPython Notebook
---------------------------
:func:`display`
    display a figure in an IPython notebook

:func:`enable_notebook`
    enable automatic D3 display of prepared model data in the IPython notebook.

:func:`disable_notebook`
    disable automatic D3 display of prepared model data in the IPython notebook.
"""

__all__ = ["__version__",
           "prepare", "js_PCoA",
           "PreparedData", "prepared_data_to_html",
           "display", "show", "save_html", "save_json",
           "enable_notebook", "disable_notebook"]

__version__ = 'git_1.0.0'



app = Flask(__name__)             
app.config['TEMPLATES_AUTO_RELOAD'] = True

extra_dirs = ['templates',] #directory to watch for any changes
extra_files = extra_dirs[:]
for extra_dir in extra_dirs:
    for dirname, dirs, files in walk(extra_dir):
        for filename in files:
            filename = path.join(dirname, filename)
            if path.isfile(filename):
                extra_files.append(filename)



######################Import data #########################


type_vis = 2


##Load Gensim Model
LdaModel = gensim.models.ldamodel.LdaModel
lda_model = LdaModel.load("data/cambridge_analytica/sample/collection_1_sample_gensim.model")

##Load corpus
with open('data/cambridge_analytica/sample/collection_1_sample_corpus.pkl', 'rb') as f:
    corpus = pickle.load(f)

##Load id2word
id2word = Dictionary.load("data/cambridge_analytica/sample/collection_1_sample_id2word")

##Load relevant documents
#relevant documents were already calculated
with open('data/cambridge_analytica/sample/collection_1_sample_sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
    sent_topics_sorteddf_mallet = pickle.load(f)
sent_topics_sorteddf_mallet = sent_topics_sorteddf_mallet[['Topic_Num','Topic_Perc_Contrib','text']]

relevantDocumentsDict = {}
for index,row in sent_topics_sorteddf_mallet.iterrows():
    topic_id = int(row['Topic_Num'])
    if topic_id not in relevantDocumentsDict:
        relevantDocumentsDict[topic_id]=[]
    relevantDocumentsDict[topic_id].append({
        'topic_perc_contrib':row['Topic_Perc_Contrib'],
        'text':row['text']
    })


#prepare data for first time'''





print("cargando prepared data collection 1")
with open('../data/cambridge_analytica/collection_I/collection_1_prepared_data', 'rb') as f:
    PreparedDataObtained = pickle.load(f)


PreparedData_dict= PreparedDataObtained.to_dict()

topic_order = PreparedData_dict['topic.order']
print("cargado!!!")



#load prepared data

with open('data/cambridge_analytica/sample/collection_1_sample_prepared_data', 'rb') as f:
    PreparedDataObtained = pickle.load(f)


PreparedData_dict= PreparedDataObtained.to_dict()

topic_order = PreparedData_dict['topic.order']
    
###Use word embedding proposed metric


def get_new_order_topic(prepared_data):
    new_order_prensa_pacifico = []
    for i in range(len(prepared_data.topic_order)):
        #FIND index topic i+1
        current_index = prepared_data.topic_order.index(i+1)+1
        new_order_prensa_pacifico.append(current_index)
    return new_order_prensa_pacifico
    
    


def distance_topic_i_j(terms_list_i,terms_list_j):
    total_distances_topic_i = 0.0
    not_found_terms = set()
    for term_i in terms_list_i:
        if term_i in wordembedding:
            dist_for_term_i = []
            for term_j in terms_list_j:
                if term_j in wordembedding:                    
                    dist_for_term_i.append(wordembedding.wv.distance(term_i,term_j))                    
                else:
                    not_found_terms.add(term_j)
            total_distances_topic_i+=min(dist_for_term_i)
        else:
            #print("Not found, i:",term_i)
            not_found_terms.add(term_i)
    #print("total distance",total_distances_topic_i )
    if len(not_found_terms)>0:
        print("Not found", not_found_terms)
    return total_distances_topic_i
categories = ['twitter']

def generar_matrix_baseline_metric(list_prepared_data, relevance_score = 0.6, topn=30):
    relevance_score = 0.6
    topn=20
    matrix = []
    categories_row = []
    i=0
    for topic_model_i in list_prepared_data:
        new_order_topics_i = get_new_order_topic(topic_model_i)
        for topic_id_i in new_order_topics_i:
            row=[]
            categories_row.append(categories[i])
            terms_list_i = topic_model_i.sorted_terms(topic=topic_id_i,_lambda=relevance_score)['Term'][:topn]
            for topic_model_j in list_prepared_data:
                new_order_topics_j = get_new_order_topic(topic_model_j)
                for topic_id_j in new_order_topics_j:
                    terms_list_j = topic_model_j.sorted_terms(topic=topic_id_j,_lambda=relevance_score)['Term'][:topn]
                    row.append(distance_topic_i_j(terms_list_i,terms_list_j))
            matrix.append(row)
        i+=1
    matrix = np.asarray(matrix)
    
    return (matrix, categories_row)









''' #descomentar esto cuando se ejecuta por primera vez
##Load word embedding
ruta_word_embedding = 'data/wiki.multi.en.vec'
##wordembedding = gensim.models.Word2Vec.load(ruta_word_embedding)
wordembedding = KeyedVectors.load_word2vec_format(ruta_word_embedding, binary=False)


heatmap = generar_matrix_baseline_metric([PreparedDataObtained])
print(heatmap)


with open('data/cambridge_analytica/sample/matrix', 'wb') as f:
    pickle.dump(heatmap[0], f)

with open('data/cambridge_analytica/sample/categories_row', 'wb') as f:
    pickle.dump(heatmap[1], f)
'''
with open('data/cambridge_analytica/sample/matrix', 'rb') as f:
    matrix = pickle.load(f)

with open('data/cambridge_analytica/sample/categories_row', 'rb') as f:
    categories_row = pickle.load(f)

print("tipo de matrix", type(matrix))
print("tipo de matrix", type(matrix.tolist()))
print("tipo de matrix", matrix.tolist())
#matrix  = [dict(zip(keys, values)) for values in matrix[0:]]
#matrix = json.dumps(matrix)



matrix = matrix.tolist()
html = prepared_html_in_flask([PreparedDataObtained], relevantDocumentsDict, topic_order, matrix, categories_row , type_vis)









@app.route("/")                   
def crosslingual():
    #show(PreparedDataObtained,local=False)
    #return render_template("index.html") 
    return render_template_string(html)

        
    
def launch():    # on running python app.py

    #al momento de empaquetar
    '''
    port = 5000 + random.randint(0, 999)
    url = "http://127.0.0.1:{0}".format(port)
    threading.Timer(1.25, lambda: webbrowser.open(url,new=2) ).start() #new = 2, open the window in a new tab
    app.run(port=port, debug=False)
    '''
    #debug
    port = 5000
    app.run(port=port, debug=True, extra_files=extra_files)
    



#############
launch()

'''
#Compare two topic modeling outputs
##Load Gensim Model
LdaModel = gensim.models.ldamodel.LdaModel
lda_model_collection_1 = LdaModel.load("../data/cambridge_analytica/collection_I/collection_1_gensim.model")
lda_model_collection_2 = LdaModel.load("../data/cambridge_analytica/collection_II/collection_2_gensim.model")
#C:\Users\gonza\Desktop\TopicVisExplorer\data\cambridge_analytica\collection_I
##Load corpus
with open('../data/cambridge_analytica/collection_I/collection_1_corpus.pkl', 'rb') as f:
    corpus_collection_1 = pickle.load(f)
with open('../data/cambridge_analytica/collection_II/collection_2_corpus.pkl', 'rb') as f:
    corpus_collection_2 = pickle.load(f)

##Load id2word
id2word_collection_1 = Dictionary.load("../data/cambridge_analytica/collection_I/collection_1_id2word")
id2word_collection_2 = Dictionary.load("../data/cambridge_analytica/collection_II/collection_2_id2word")


print("preparando prepared data - collection 1")
data_dict = gensim_helpers.prepare(lda_model_collection_1, corpus_collection_1,id2word_collection_1, mds='pcoa')   #retorna un dict de preparedData

PreparedDataObtained = prepare(**data_dict)

with open('../data/cambridge_analytica/collection_I/collection_1_prepared_data', 'wb') as f:
    pickle.dump(PreparedDataObtained, f)

print("preparando prepared data - collection 2")
data_dict = gensim_helpers.prepare(lda_model_collection_2, corpus_collection_2,id2word_collection_2, mds='pcoa')   #retorna un dict de preparedData

PreparedDataObtained = prepare(**data_dict)

with open('../data/cambridge_analytica/collection_II/collection_2_prepared_data', 'wb') as f:
    pickle.dump(PreparedDataObtained, f)


data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa')   #retorna un dict de preparedData

PreparedDataObtained = prepare(**data_dict)

with open('data/cambridge_analytica/sample/collection_1_sample_prepared_data', 'wb') as f:
    pickle.dump(PreparedDataObtained, f)'''
