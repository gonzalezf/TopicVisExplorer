# -*- coding: utf-8 -*-

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
import sklearn
from flask import Flask, jsonify, request, render_template

#from sklearn.metrics.pairwise import cosine_similarity
#from calculate_topic_similarity import getTopicSimilarityMetric


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



def get_dicts_relevant_keywords_documents(lda_model,df_relevant_documents, n_terms):
    num_topics = lda_model.num_topics
    #create dictionary of top keywords 
    topKeywordsDict = {}
    for topic_id in range(num_topics):
        topKeywordsDict[topic_id] = []
        for term, probability in lda_model.show_topic(topic_id,topn=n_terms):
            topKeywordsDict[topic_id].append({
                "term":term,
                "probability":probability
            })

    #create dictionary of relevant documents
    relevantDocumentsDict = {}
    for index,row in df_relevant_documents.iterrows():
        topic_id = int(row['Topic_Num'])
        if topic_id not in relevantDocumentsDict:
            relevantDocumentsDict[topic_id]=[]
        relevantDocumentsDict[topic_id].append({
            'topic_perc_contrib':row['Topic_Perc_Contrib'],
            'text':row['text']
        })
    return (topKeywordsDict, relevantDocumentsDict)

def proposed_topic_similarity(wordembedding, lda_model, n_terms): #n_terms : numero de top keywords a considerar
    topKeywordsDict, relevantDocumentsDict = get_dicts_relevant_keywords_documents(lda_model, n_terms)

    #create keyword vector
    topkeywords_vectors_dict = {}
    for topic_id in range(num_topics):
        topkeywords_vector = 0
        ranking = 1.0
        for item in topKeywordsDict[topic_id]:
            if item['term'] in wordembedding: #no todas las palabras aparecerán en el ranking, que hacer con el resto
                #print(item['term'], item['probability'])
                topkeywords_vector += wordembedding.wv[item['term']]/ranking
            else:
                print("Not found", item['term'],"ranking",ranking)
            ranking+=1
        topkeywords_vectors_dict[topic_id] = topkeywords_vector



######################Import data #########################
type_vis = 2#2: two topic modeling output, 1: one topic modeling output

if type_vis ==1: #load just one model
    ##Load relevant documents
    #relevant documents were already calculated
    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csvsent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
        sent_topics_sorteddf_mallet = pickle.load(f)
    sent_topics_sorteddf_mallet = sent_topics_sorteddf_mallet[['Topic_Num','Topic_Perc_Contrib','text']]

    relevantDocumentsDict = {}
    for index,row in sent_topics_sorteddf_mallet.iterrows():
        topic_id = int(row['Topic_Num'])
        if topic_id not in relevantDocumentsDict:
            relevantDocumentsDict[topic_id]=[]
        relevantDocumentsDict[topic_id].append({
            'topic_perc_contrib':str(round(row['Topic_Perc_Contrib']*100,1))+"%",
            'text':row['text']
        })
    #load prepared data
    try: #if file exits
        
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'rb') as f: #voy a echar a perder este archivo, para que siempre se tenga que calcular ../data/cambridge_analytica/collection_I/collection_1_prepared_data
            PreparedDataObtained = pickle.load(f)
        print("We found prepared data file")

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_data_dict', 'rb') as f: #voy a echar a perder este archivo, para que siempre se tenga que calcular ../data/cambridge_analytica/collection_I/collection_1_prepared_data
            data_dict = pickle.load(f)
        print("We found prepared data dict")

    except:
        print("We need to create prepared data")
        ##Load Gensim Model
        LdaModel = gensim.models.ldamodel.LdaModel
        lda_model = LdaModel.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_gensim.model")

        ##Load corpus
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_corpus.pkl', 'rb') as f:
            corpus = pickle.load(f)

        ##Load id2word
        id2word = Dictionary.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_id2word")

        data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa')   #retorna un dict de preparedData

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_data_dict', 'wb') as f:
            pickle.dump(data_dict, f)
        print("data dict ha sido guardado")

        PreparedDataObtained = prepare(**data_dict)

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'wb') as f:
            pickle.dump(PreparedDataObtained, f)

    PreparedData_dict= PreparedDataObtained.to_dict()

    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data_dict_with_more_info', 'wb') as f:
        pickle.dump(PreparedData_dict, f)

    topic_order = PreparedData_dict['topic.order']
    print("ESTE ES EL LEN DE TOPIC ORDER", len(topic_order))
    #Matriz de distancia - Topic similarity metric proposed

    #hay que calcular la matriz de distancia! no solo precalcularla
    with open('../data/cambridge_analytica/regional_datasets/matrix_europe_vs_europe_own_wordembedding_final', 'rb') as f:
        matrix = pickle.load(f)
    
    new_circle_positions = dict()
    for lambda_ in range(0, 100):
        lambda_ = lambda_/100
        matrix_cosine_distance = 1-matrix[lambda_]
        np.fill_diagonal(matrix_cosine_distance,0)
        new_circle_positions[lambda_]=_pcoa(matrix_cosine_distance, n_components=2).tolist()
    #print(new_circle_positions)
    new_circle_positions= json.dumps(new_circle_positions)
    
   
    ###############Matriz de distancia - Baseline, word embedding #####################
    '''
    try:
        #revisar si estan esos archivos
        with open('../data/cambridge_analytica/sample/matrix', 'rb') as f:
            matrix = pickle.load(f)
        with open('../data/cambridge_analytica/sample/categories_row', 'rb') as f:
            categories_row = pickle.load(f)
        print("we found a matrix distance")
    except:
        #dado de que no estan, hay que crearlos
        print("Creando matrix de distancia")
        print("Cargando word embedding")    
        ##Load word embedding
        ruta_word_embedding = '../data/wiki.multi.en.vec'
        ##wordembedding = gensim.models.Word2Vec.load(ruta_word_embedding)
        wordembedding = KeyedVectors.load_word2vec_format(ruta_word_embedding, binary=False)
        heatmap = generar_matrix_baseline_metric([PreparedDataObtained])

        with open('../data/cambridge_analytica/sample/matrix', 'wb') as f:
            pickle.dump(heatmap[0], f)

        with open('../data/cambridge_analytica/sample/categories_row', 'wb') as f:
            pickle.dump(heatmap[1], f)
        matrix = heatmap[0]
        categories_row = heatmap[1]
    matrix = matrix.tolist()

    '''

    html = prepared_html_in_flask(data = [PreparedDataObtained], relevantDocumentsDict = relevantDocumentsDict, topic_order = topic_order,  type_vis = type_vis,  new_circle_positions = new_circle_positions)



if type_vis == 2: #load two topic modeling output
    
    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csvsent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
        most_relevant_documents_collection_1 = pickle.load(f)
    most_relevant_documents_collection_1 = most_relevant_documents_collection_1[['Topic_Num','Topic_Perc_Contrib','text']]

    relevantDocumentsDict_collection_1 = {}
    for index,row in most_relevant_documents_collection_1.iterrows():
        topic_id = int(row['Topic_Num'])
        if topic_id not in relevantDocumentsDict_collection_1:
            relevantDocumentsDict_collection_1[topic_id]=[]
        relevantDocumentsDict_collection_1[topic_id].append({
            'topic_perc_contrib':str(round(row['Topic_Perc_Contrib']*100,1))+"%",
            'text':row['text']
        })

    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csvsent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
        most_relevant_documents_collection_2 = pickle.load(f)
    most_relevant_documents_collection_2 = most_relevant_documents_collection_2[['Topic_Num','Topic_Perc_Contrib','text']]

    relevantDocumentsDict_collection_2 = {}
    for index,row in most_relevant_documents_collection_2.iterrows():
        topic_id = int(row['Topic_Num'])
        if topic_id not in relevantDocumentsDict_collection_2:
            relevantDocumentsDict_collection_2[topic_id]=[]
        relevantDocumentsDict_collection_2[topic_id].append({
            'topic_perc_contrib':str(round(row['Topic_Perc_Contrib']*100,1))+"%",
            'text':row['text']
        })
    try: 
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'rb') as f:
            PreparedDataObtained_collection_1 = pickle.load(f)
    except:
        print("We need to create prepared data, collection 1")
        ##Load Gensim Model
        LdaModel = gensim.models.ldamodel.LdaModel
        lda_model_collection_1 = LdaModel.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_gensim.model")

        ##Load corpus
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_corpus.pkl', 'rb') as f:
            corpus_collection_1 = pickle.load(f)

        ##Load id2word
        id2word_collection_1 = Dictionary.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_id2word")

        data_dict_collection_1 = gensim_helpers.prepare(lda_model_collection_1, corpus_collection_1,id2word_collection_1, mds='pcoa')   #retorna un dict de preparedData

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_data_dict', 'wb') as f:
            pickle.dump(data_dict_collection_1, f)
        print("data dict collection 1 ha sido guardado")

        PreparedDataObtained_collection_1 = prepare(**data_dict_collection_1)

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'wb') as f:
            pickle.dump(PreparedDataObtained_collection_1, f)
    try:
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'rb') as f:
            PreparedDataObtained_collection_2 = pickle.load(f)
        print("We found prepared data file collection2")
    except:
        print("We need to create prepared data, collection 2")
        ##Load Gensim Model
        LdaModel = gensim.models.ldamodel.LdaModel
        lda_model_collection_2 = LdaModel.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_gensim.model")

        ##Load corpus
        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_corpus.pkl', 'rb') as f:
            corpus_collection_2 = pickle.load(f)

        ##Load id2word
        id2word_collection_2 = Dictionary.load("../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411.csv_id2word")

        data_dict_collection_2 = gensim_helpers.prepare(lda_model_collection_2, corpus_collection_2,id2word_collection_2, mds='pcoa')   #retorna un dict de preparedData

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_data_dict', 'wb') as f:
            pickle.dump(data_dict_collection_2, f)
        print("data dict collection 2 ha sido guardado")

        PreparedDataObtained_collection_2 = prepare(**data_dict_collection_2)

        with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data', 'wb') as f:
            pickle.dump(PreparedDataObtained_collection_2, f)

    PreparedData_dict_collection_1= PreparedDataObtained_collection_1.to_dict()    
    topic_order_collection_1 = PreparedData_dict_collection_1['topic.order']

    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data_dict_with_more_info', 'wb') as f:
            pickle.dump(PreparedData_dict_collection_1, f)

    PreparedData_dict_collection_2= PreparedDataObtained_collection_2.to_dict()
    topic_order_collection_2 = PreparedData_dict_collection_2['topic.order']

    with open('../data/cambridge_analytica/regional_datasets/files_europe/english_europe_tweets_20190411_prepared_data_dict_with_more_info', 'wb') as f:
            pickle.dump(PreparedData_dict_collection_2, f)
    


    ###############Matriz de distancia - Baseline, word embedding #####################
    ###ESTO HAY QUE HACER UN UPDATE!!! Con el nuevo dataset (europe and northamerica datasets)
    try:
        #revisar si estan esos archivos
        with open('../data/cambridge_analytica/sample/matrix', 'rb') as f:
            matrix = pickle.load(f)
        with open('../data/cambridge_analytica/sample/categories_row', 'rb') as f:
            categories_row = pickle.load(f)

        with open('../data/cambridge_analytica/regional_datasets//matrix_europe_vs_europe_own_wordembedding_final', 'rb') as f:
            matrix_sankey = pickle.load(f)
                
        print("we found a matrix distance")
    except:
        print("We can't load matrix")
    matrix = matrix.tolist()
    
    

                                                                                
    html = prepared_html_in_flask(data = [PreparedDataObtained_collection_1], relevantDocumentsDict = relevantDocumentsDict_collection_1,topic_order =  topic_order_collection_1, type_vis = type_vis, matrix_sankey = matrix_sankey, data_2 = [PreparedDataObtained_collection_2], relevantDocumentsDict_2 = relevantDocumentsDict_collection_2, topic_order_2 = topic_order_collection_2)




@app.route("/")                   
def crosslingual():
    #show(PreparedDataObtained,local=False)
    #return render_template("index.html") 
    return render_template_string(html)


@app.route('/merge_topics', methods=['POST'])
def merge_topics():  #Se debe añadir el parametro data_dict de alguna forma, para que no tengamos que cargarlo a cada rato
    if request.method == 'POST':
        '''
        topic_index_1 = request.get_json(force=True)['merging_topic_1'] 
        topic_index_2 = request.get_json(force=True)['merging_topic_2']

        

        with open('../data/cambridge_analytica/collection_I/collection_1_data_dict', 'rb') as f: #voy a echar a perder este archivo, para que siempre se tenga que calcular ../data/cambridge_analytica/collection_I/collection_1_prepared_data
            data_dict = pickle.load(f)
        print("MERGE OPERATION - WE FOUND  A DATA DICT!!!!!!!!!!!")
        print("COMENZO A HACER EL MERGE de los topicos", topic_index_1, "y ", topic_index_2)
        
        #create a ne topic_term_dists
        #the first column of the merge is going to be equal to =first_column_merge+second_column_merge (point wise)
        data_dict['topic_term_dists'][topic_index_1] = np.add(data_dict['topic_term_dists'][topic_index_1],data_dict['topic_term_dists'][topic_index_2])
        data_dict['topic_term_dists'] =  np.delete(data_dict['topic_term_dists'], topic_index_2, 0) #borramos la segunda columna con la que hicimos el merge
        #we must delete all the references to the topic_index_2 (it doesn't exist anymore)
        
        #create a new doc_topic_dists:
        data_dict['doc_topic_dists'][:,topic_index_1] = data_dict['doc_topic_dists'][:,topic_index_1]+data_dict['doc_topic_dists'][:,topic_index_2]
        data_dict['doc_topic_dists'] = np.delete(data_dict['doc_topic_dists'], topic_index_2, 1)

        '''
        #things that keep the the same
        #VAMOS A OMITIR ESTO, para que de esta forma podamos ver el cambio!!

        '''
        with open('../data/cambridge_analytica/collection_I/collection_1_data_dict', 'wb') as f:
            pickle.dump(data_dict, f)
        print("NUEVO data dict ha sido guardado")
        '''
        #print("TERMINO DE HACER EL MERGE!!!")
        
        #Generate a new mdsData


        with open('../data/cambridge_analytica/collection_I/collection_1_prepared_data_merging', 'rb') as f: #voy a echar a perder este archivo, para que siempre se tenga que calcular ../data/cambridge_analytica/collection_I/collection_1_prepared_data
            PreparedDataObtained = pickle.load(f)

        print("ENCONTRAMOS UN PREPARED DATA DEL MERGING")


        '''
        PreparedDataObtained = prepare(**data_dict)
        with open('../data/cambridge_analytica/collection_I/collection_1_prepared_data_merging', 'wb') as f:
            pickle.dump(PreparedDataObtained, f)

        print("GUARDAMOS EL PREPARED DATA AFTER MERGIN")
        '''

        PreparedData_dict= PreparedDataObtained.to_dict()
        topic_order = PreparedData_dict['topic.order'] #ojo, aqui hay que mantener un historial de los nombres
        print("EL LEN DE TOPIC ORDER ES ", len(topic_order))
        print("topic order es", topic_order)
        #Matriz de distancia - Topic similarity metric proposed
        
        #Generate new relevantDocumentsDict
        #######load the inicial relevantDocuments Dict, sobre este aplicar el merge

        with open('../data/cambridge_analytica/collection_I/collection_1_sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
            sent_topics_sorteddf_mallet = pickle.load(f)
        sent_topics_sorteddf_mallet = sent_topics_sorteddf_mallet[['Topic_Num','Topic_Perc_Contrib','text']]

        relevantDocumentsDict = {}
        for index,row in sent_topics_sorteddf_mallet.iterrows():
            topic_id = int(row['Topic_Num'])
            if topic_id not in relevantDocumentsDict:
                relevantDocumentsDict[topic_id]=[]
            relevantDocumentsDict[topic_id].append({
                'topic_perc_contrib':str(round(row['Topic_Perc_Contrib']*100,1))+"%",
                'text':row['text']
            })

        #hay que calcular la matriz de distancia! no solo precalcularla
        with open('../data/cambridge_analytica/matrix_collection_1_1', 'rb') as f: #hay que calcular una nueva matriz de distancia
            matrix = pickle.load(f)
        
        new_circle_positions = dict()
        for lambda_ in range(0, 100):
            lambda_ = lambda_/100
            matrix_cosine_distance = 1-matrix[lambda_]
            np.fill_diagonal(matrix_cosine_distance,0)
            new_circle_positions[lambda_]=_pcoa(matrix_cosine_distance, n_components=2).tolist()
        #print(new_circle_positions)
        new_circle_positions= json.dumps(new_circle_positions)

        html = prepared_html_in_flask(data = [PreparedDataObtained], relevantDocumentsDict = relevantDocumentsDict, topic_order = topic_order,  type_vis = type_vis,  new_circle_positions = new_circle_positions)
        return render_template_string(html)
        #return PreparedData_dict
    
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



