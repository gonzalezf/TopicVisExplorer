# -*- coding: utf-8 -*-

import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
import numpy as np
import sklearn
import os
import pandas as pd
import pickle  #Descomentar segun la version de python
#import pickle5 as pickle

import json as js
import time


from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json, Response, render_template_string, jsonify
from flask_classful import FlaskView,route
from _display import *
from _prepare import prepare, js_PCoA, PreparedData, _pcoa
from _topic_similarity_matrix import *
from _topic_similarity_matrix_metric_baseline import *

from _get_new_circle_positions import *
from _topic_splitting_helpers import *
from os import path, walk
from gensim.models.keyedvectors import KeyedVectors
from scipy.spatial import procrustes

from random import sample
from utils import get_id, write_ipynb_local_js, NumPyEncoder
from _prepare import PreparedData
from copy import deepcopy


scenarios = {
}

single_corpus_data = {}
multi_corpora_data = {}
previous_single_corpus_data = []
class TopicVisExplorer:

    app = None
    
    def __init__(self, name):        
        self.app = Flask(name)
        TestView.register(self.app, route_base = '/')
    
    def run(self):
        self.app.run(debug=False)
    


    
    def calculate_topic_similarity_on_single_corpus_for_topic_splitting(self, current_number_of_topics,  word_embedding_model, lda_model, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda ):        
        #single_corpus_data['lda_model'].num_topics = single_corpus_data['lda_model'].num_topics+1
        #single_corpus_data['lda_model'].num_topics
        temp_lda = lda_model
        temp_lda.num_topics = current_number_of_topics+1
        return self.calculate_topic_similarity_on_single_corpus(word_embedding_model, temp_lda, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda )

        
    def calculate_topic_similarity_on_single_corpus(self, word_embedding_model, lda_model, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda ):        
        print("we are calculating a new topic similarity matirx")
        if 'data_dict' not in single_corpus_data:
            data_dict = gensim_helpers.prepare(lda_model, corpus,id2word) 
            single_corpus_data['data_dict']  = data_dict  
        if 'PreparedDataObtained' not in single_corpus_data:         
            temp = prepare(**data_dict)            
            single_corpus_data['PreparedDataObtained'] =  temp.to_dict()

        if 'relevantDocumentsDict' not in single_corpus_data:
            relevantDocumentsDict = matrix_documents_topic_contribution.to_dict(orient='records')
            single_corpus_data['relevantDocumentsDict'] = relevantDocumentsDict

        #update word embedding model
        single_corpus_data['word_embedding_model'] = word_embedding_model

        #get most relevant keywords sorted by relevance     
        #in merging, we should update this list
        tinfo_collection_1 = pd.DataFrame.from_dict(single_corpus_data['PreparedDataObtained']['tinfo'])
        tinfo_collection_1['relevance'] = relevance_lambda * tinfo_collection_1['logprob']+ (1.00-relevance_lambda)*tinfo_collection_1['loglift']

        # We need the topkeywords and toprelevantdocuments  vectors here!!!
        topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1 = get_topkeywords_relevantdocuments_vectors(word_embedding_model, lda_model,pd.DataFrame(single_corpus_data['relevantDocumentsDict']),  topn_terms, tinfo_collection_1, topk_documents)

        #save data
        single_corpus_data['tinfo_collection'] = tinfo_collection_1
        single_corpus_data['topkeywords_vectors_dict'] = topkeywords_vectors_dict_1
        single_corpus_data['relevantdocuments_vectors_dict'] = relevantdocuments_vectors_dict_1
        

        return get_dict_topic_similarity_matrix(word_embedding_model, lda_model,matrix_documents_topic_contribution,lda_model,matrix_documents_topic_contribution, topn_terms, single_corpus_data['PreparedDataObtained'], single_corpus_data['PreparedDataObtained'], topk_documents, relevance_lambda, tinfo_collection_1, tinfo_collection_1,topkeywords_vectors_dict_1,topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_1)

    
    def calculate_topic_similarity_on_multi_corpora(self, word_embedding_model, lda_model_1, lda_model_2, corpus_1,corpus_2,  id2word_1,id2word_2, matrix_documents_topic_contribution_1, matrix_documents_topic_contribution_2, topn_terms, topk_documents, relevance_lambda ):        


        if 'data_dict_1' not in multi_corpora_data:
            data_dict_1 = gensim_helpers.prepare(lda_model_1, corpus_1,id2word_1) 
            multi_corpora_data['data_dict_1']  = data_dict_1  
        if 'PreparedDataObtained_collection_1' not in multi_corpora_data:         
            temp_1 = prepare(**data_dict_1)            
            multi_corpora_data['PreparedDataObtained_collection_1'] =  temp_1.to_dict()

        if 'relevantDocumentsDict_collection_1' not in multi_corpora_data:
            relevantDocumentsDict_collection_1 = matrix_documents_topic_contribution_1.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_1'] = relevantDocumentsDict_collection_1

        if 'data_dict_2' not in multi_corpora_data:
            data_dict_2 = gensim_helpers.prepare(lda_model_2, corpus_2,id2word_2) 
            multi_corpora_data['data_dict_2']  = data_dict_2
        if 'PreparedDataObtained_collection_2' not in multi_corpora_data:         
            temp_2 = prepare(**data_dict_2)            
            multi_corpora_data['PreparedDataObtained_collection_2'] =  temp_2.to_dict()

        if 'relevantDocumentsDict_collection_2' not in multi_corpora_data:
            relevantDocumentsDict_collection_2 = matrix_documents_topic_contribution_2.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_2'] = relevantDocumentsDict_collection_2

        #get most relevant keywords sorted by relevance     
        #in merging, we should update this list
        tinfo_collection_1 = pd.DataFrame.from_dict(multi_corpora_data['PreparedDataObtained_collection_1']['tinfo'])
        tinfo_collection_1['relevance'] = relevance_lambda * tinfo_collection_1['logprob']+ (1.00-relevance_lambda)*tinfo_collection_1['loglift']

        tinfo_collection_2 = pd.DataFrame.from_dict(multi_corpora_data['PreparedDataObtained_collection_2']['tinfo'])
        tinfo_collection_2['relevance'] = relevance_lambda * tinfo_collection_2['logprob']+ (1.00-relevance_lambda)*tinfo_collection_2['loglift']

        # We need the topkeywords and toprelevantdocuments  vectors here!!!
        topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1 = get_topkeywords_relevantdocuments_vectors(word_embedding_model, lda_model_1,pd.DataFrame(multi_corpora_data['relevantDocumentsDict_collection_1']),  topn_terms, tinfo_collection_1, topk_documents)
        topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_2 = get_topkeywords_relevantdocuments_vectors(word_embedding_model, lda_model_2,pd.DataFrame(multi_corpora_data['relevantDocumentsDict_collection_2']),  topn_terms, tinfo_collection_2, topk_documents)

        #save data
        single_corpus_data['tinfo_collection_1'] = tinfo_collection_1
        single_corpus_data['tinfo_collection_2'] = tinfo_collection_2

        single_corpus_data['topkeywords_vectors_dict_1'] = topkeywords_vectors_dict_1
        single_corpus_data['topkeywords_vectors_dict_2'] = topkeywords_vectors_dict_2

        single_corpus_data['relevantdocuments_vectors_dict_1'] = relevantdocuments_vectors_dict_1
        single_corpus_data['relevantdocuments_vectors_dict_2'] = relevantdocuments_vectors_dict_2
        

        return get_dict_topic_similarity_matrix(word_embedding_model, lda_model_1,matrix_documents_topic_contribution_1,lda_model_2,matrix_documents_topic_contribution_2, topn_terms, multi_corpora_data['PreparedDataObtained_collection_1'], multi_corpora_data['PreparedDataObtained_collection_2'], topk_documents, relevance_lambda, tinfo_collection_1, tinfo_collection_2,topkeywords_vectors_dict_1, topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_2)


    def calculate_topic_similarity_on_multi_corpora_metric_baseline(self, word_embedding_model, lda_model_1, lda_model_2, corpus_1,corpus_2,  id2word_1,id2word_2, relevance_lambda = 0.6, topn_terms=20):            
        # get prepared data of lda_model_1, and lda_model_2
        data_dict_1 = gensim_helpers.prepare(lda_model_1, corpus_1,id2word_1) 
        prepared_data_topic_1 = prepare(**data_dict_1)            
        #PreparedDataObtained_1_dict = PreparedDataObtained_1.to_dict()
        # get prepared data of lda_model_1, and lda_model_2
        data_dict_2 = gensim_helpers.prepare(lda_model_2, corpus_2,id2word_2) 
        prepared_data_topic_2 = prepare(**data_dict_2)            
        #PreparedDataObtained_2_dict = PreparedDataObtained_2.to_dict()

        return  generar_matrix_baseline_metric(word_embedding_model,   prepared_data_topic_1, prepared_data_topic_2, relevance_lambda, topn_terms)
    
    def prepare_single_corpus(self, lda_model, corpus, id2word, matrix_documents_topic_contribution, topic_similarity_matrix):
        
        if 'data_dict' not in single_corpus_data:
            data_dict = gensim_helpers.prepare(lda_model, corpus,id2word) 
            single_corpus_data['data_dict']  = data_dict  
        if 'PreparedDataObtained' not in single_corpus_data:         
            print("A NEW PREPARED DATA HA SIDO CREADO!!")
            temp = prepare(**single_corpus_data['data_dict'])            
            single_corpus_data['PreparedDataObtained'] =  temp.to_dict()

        if 'relevantDocumentsDict' not in single_corpus_data:
            relevantDocumentsDict = matrix_documents_topic_contribution.to_dict(orient='records')
            single_corpus_data['relevantDocumentsDict'] = relevantDocumentsDict


        new_circle_positions = get_circle_positions(topic_similarity_matrix)
        

        single_corpus_data['lda_model'] = lda_model
        single_corpus_data['corpus'] = corpus
        single_corpus_data['id2word'] = id2word
        single_corpus_data['topic_similarity_matrix'] = topic_similarity_matrix        
        single_corpus_data['topic.order'] = single_corpus_data['PreparedDataObtained']['topic.order']
        single_corpus_data['new_circle_positions'] = new_circle_positions

    def prepare_multi_corpora(self, lda_model_1,lda_model_2, corpus_1, corpus_2,  id2word_1,id2word_2, matrix_documents_topic_contribution_1,matrix_documents_topic_contribution_2, topic_similarity_matrix):

        if 'data_dict_1' not in multi_corpora_data:
            data_dict_1 = gensim_helpers.prepare(lda_model_1, corpus_1,id2word_1) 
            multi_corpora_data['data_dict_1']  = data_dict_1  
        if 'PreparedDataObtained_collection_1' not in multi_corpora_data:         
            temp_1 = prepare(**multi_corpora_data['data_dict_1'] )            
            multi_corpora_data['PreparedDataObtained_collection_1'] =  temp_1.to_dict()

        if 'relevantDocumentsDict_collection_1' not in multi_corpora_data:
            relevantDocumentsDict_collection_1 = matrix_documents_topic_contribution_1.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_1'] = relevantDocumentsDict_collection_1

        if 'data_dict_2' not in multi_corpora_data:
            data_dict_2 = gensim_helpers.prepare(lda_model_2, corpus_2,id2word_2) 
            multi_corpora_data['data_dict_2']  = data_dict_2
        if 'PreparedDataObtained_collection_2' not in multi_corpora_data:         
            temp_2 = prepare(**multi_corpora_data['data_dict_2'] )            
            multi_corpora_data['PreparedDataObtained_collection_2'] =  temp_2.to_dict()

        if 'relevantDocumentsDict_collection_2' not in multi_corpora_data:
            relevantDocumentsDict_collection_2 = matrix_documents_topic_contribution_2.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_2'] = relevantDocumentsDict_collection_2

        
        multi_corpora_data['lda_model_1'] = lda_model_1,
        multi_corpora_data['lda_model_2'] = lda_model_2,

        multi_corpora_data['corpus_1'] = corpus_1
        multi_corpora_data['corpus_2'] = corpus_2

        multi_corpora_data['id2word_1'] = id2word_1
        multi_corpora_data['id2word_2'] = id2word_2

        multi_corpora_data['topic_similarity_matrix'] = topic_similarity_matrix        

        multi_corpora_data['topic_order_collection_1'] = multi_corpora_data['PreparedDataObtained_collection_1']['topic.order']
        multi_corpora_data['topic_order_collection_2'] = multi_corpora_data['PreparedDataObtained_collection_2']['topic.order']
        

        
    #save the visualization data of to a file        
    def save_single_corpus_data(self, route_file): #hay que indicar a si corresponde al single corpus o al multicorpora
        save = True
        single_corpus_data_keys = ['lda_model','corpus',
        'id2word','topic_similarity_matrix', 'topic.order', 
        'new_circle_positions', 'relevantDocumentsDict', 
        'PreparedDataObtained', 'data_dict']

        for key in single_corpus_data_keys:
            if key not in single_corpus_data.keys():
                save = False
                print("Error. Data it is incomplete. It is necessary to get", key)
        if(save):    
            with open(route_file, 'wb') as handle:
                pickle.dump(single_corpus_data, handle, protocol=4) #protocol 4 is compatible with python 3.6+
                print("Single corpus data saved sucessfully")

    def save_multi_corpora_data(self, route_file): #hay que indicar a si corresponde al single corpus o al multicorpora
        save = True
        multi_corpora_data_keys = ['lda_model_1','lda_model_2',
        'corpus_1','corpus_2','id2word_1','id2word_2',
        'relevantDocumentsDict_collection_1','relevantDocumentsDict_collection_2',
        'PreparedDataObtained_collection_1','PreparedDataObtained_collection_2',
        'data_dict_1','data_dict_2','topic_order_collection_1','topic_order_collection_2',
        'topic_similarity_matrix']

        for key in multi_corpora_data_keys:
            if key not in multi_corpora_data.keys():
                save = False
                print("Error. Data it is incomplete. It is necessary to get", key)
        if(save):    
            with open(route_file, 'wb') as handle:
                pickle.dump(multi_corpora_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
                print("Multi corpora data saved sucessfully")


    def load_corpus_data(self, route_file, scenario_name, multi=False):#human_in_the_loop=True):

        with open(route_file, 'rb') as handle:
            global scenarios
            scenarios[scenario_name] = pickle.load(handle)
            scenarios[scenario_name]["multi"] = multi
            #single_corpus_data['human_in_the_loop'] = human_in_the_loop 

            print("Data loaded sucessfully")


        


class TestView(FlaskView):

    @route('/')
    def index(self):
    # http://localhost:5000/
        return "<h1>index</h1>"

    @route('/MultiCorpora_documents_1')
    def get_documents_data_multicorpus_1(self):
        global multi_corpora_data        
        #return Response(js.dumps(random.sample(multi_corpora_data['relevantDocumentsDict_collection_1'],10)),  mimetype='application/json')
        return Response(js.dumps(multi_corpora_data['relevantDocumentsDict_collection_1']),  mimetype='application/json')

    @route('/MultiCorpora_documents_2')
    def get_documents_data_multicorpus_2(self):
        global multi_corpora_data        
        #return Response(js.dumps(random.sample(multi_corpora_data['relevantDocumentsDict_collection_2'],10)),  mimetype='application/json')
        return Response(js.dumps(multi_corpora_data['relevantDocumentsDict_collection_2']),  mimetype='application/json')

    @route('/SingleCorpus_documents')
    def get_documents_data_singlecorpus(self):

        global single_corpus_data   
        return Response(js.dumps( single_corpus_data['relevantDocumentsDict']),  mimetype='application/json')
        #return Response(js.dumps( random.sample(single_corpus_data['relevantDocumentsDict'],2000)),  mimetype='application/json')


    #Split topic

    @route('/undo_merge_splitting',  methods=['POST'])
    def undo_merge_splitting(self):
        print('doing el undo merge splitting operation ')
        global single_corpus_data
        global previous_single_corpus_data
        single_corpus_data = previous_single_corpus_data.pop()


        return 'se ha quiitado el ultimo single corpus data del arreglo'
        
    @route('/Topic_Splitting_Document_Based',  methods=['GET', 'POST'])
    def get_new_sub_topics(self):
            print('Calculando nuevos dos subtopicos')
            #save single corpus data
            start = time.time()
            
            global single_corpus_data
            global previous_single_corpus_data

            previous_single_corpus_data.append(deepcopy(single_corpus_data))
            print("**************************************************************************************")
            print('Topic order INICIAL - TOPIC SPLITTING',single_corpus_data['PreparedDataObtained']['topic.order'])
            print("**************************************************************************************")


            json_file = request.get_json()
            
            #get data from user     
            old_circle_positions = json_file['old_circle_positions']
            current_number_of_topics = json_file['current_number_of_topics']
            topic_id = json_file['topic_id'] #tHE FIRST TOPIC IS ID=1, not 0!
            new_document_seeds_TopicA = json_file['new_document_seeds']['TopicA']
            new_document_seeds_TopicB = json_file['new_document_seeds']['TopicB']

            word_embedding_model = single_corpus_data['word_embedding_model']

            print('este es el numero actual de topicos antes de hacer splitting', current_number_of_topics)
            
            
            with open('json_file_topic_splitting_test.json', 'w') as current_file:
                js.dump(json_file, current_file)
            
            #print('esto fue lo enviado desde el usuario para el splitting document based', json_file)
            print('Json RECIBIDO')
            PreparedData_dict_with_more_info = single_corpus_data['tinfo_collection']

            list_terms_relevance = PreparedData_dict_with_more_info.loc[PreparedData_dict_with_more_info['Category'] == 'Topic'+str(topic_id)].sort_values(by='relevance', ascending=False)['Term'].tolist()
            list_relevant_documents = random.sample(single_corpus_data['relevantDocumentsDict'],200)
            list_relevant_documents = pd.DataFrame(list_relevant_documents).sort_values(int(topic_id)-1, ascending=False).reset_index()
            #the idea is do this only ONCE! and tenerlo precalculado para el user study

            end = time.time()
            print("Topic splitting - Getting data", end - start)
            start = time.time()

            print('cleaning sample fo text')
            list_relevant_documents[name_tokenizacion] = list_relevant_documents[name_column_text].apply(lambda x: text_cleaner(x))
            list_relevant_documents = list_relevant_documents.to_dict('records')
            print('cleaning documents seeds topic a')

            new_document_seeds_TopicA = pd.DataFrame(new_document_seeds_TopicA).reset_index()
            new_document_seeds_TopicA[name_tokenizacion] = new_document_seeds_TopicA[name_column_text].apply(lambda x: text_cleaner(x))
            new_document_seeds_TopicA = new_document_seeds_TopicA.to_dict('records')
            print('cleaning documents seeds topic B')

            new_document_seeds_TopicB = pd.DataFrame(new_document_seeds_TopicB).reset_index()
            new_document_seeds_TopicB[name_tokenizacion] = new_document_seeds_TopicB[name_column_text].apply(lambda x: text_cleaner(x))
            new_document_seeds_TopicB = new_document_seeds_TopicB.to_dict('records')
            end = time.time()
            print("Topic splitting - Cleaning text", end - start)
  
            start = time.time()
            results  = get_new_subtopics(list_terms_relevance, list_relevant_documents, topic_id, name_tokenizacion,name_column_text, new_document_seeds_TopicA, new_document_seeds_TopicB, word_embedding_model)
            model_topic_A, model_topic_B, most_relevant_documents_topic, freq_topic_A, freq_topic_B = results
            end = time.time()
            print("Topic splitting - Getting new subtopics", end - start)
            start = time.time()

            #  CREAR PICKLEEE!!! CON ESTA DATAAA!!!
            #with open('models_output/testing_spliting_models_topic_A_B.pkl', 'wb') as handle:
                #pickle.dump(results, handle, protocol=4) #protocol 4 is compatible with python 3.6+
                #print("Results for topic splitting has been saved")
            
            
            print('Geeting new term-topic distributions')
            # Get new term-topic distributions in the new subtopics
            #get new distribution of terms, topic A
            corpus_topic_A, dictionary_topic_A = model_topic_A
            data_model_A = extract_data_without_topic_model(corpus_topic_A, dictionary_topic_A)


            corpus_topic_B, dictionary_topic_B = model_topic_B
            data_model_B = extract_data_without_topic_model(corpus_topic_B, dictionary_topic_B)
            print('actualizando el modelo A and B')
            #filtrar por terminos que si aparezcan en lists terms relevance
            df_temp = pd.DataFrame(data_model_A)
            df_temp = df_temp[df_temp['vocab'].isin(list_terms_relevance)]
            data_model_A = df_temp.to_dict()
            df_temp = pd.DataFrame(data_model_B)
            df_temp = df_temp[df_temp['vocab'].isin(list_terms_relevance)]
            data_model_B = df_temp.to_dict()

            end = time.time()
            print("Topic splitting - Getting new topic term distributions", end - start)
            start = time.time()


            #Get most relevant documents
            print('Getting most relevant documents')
            new_dict = dict()
            #set columns of the new subtopics to NaN values
            df = pd.DataFrame(single_corpus_data['relevantDocumentsDict'])

            df[int(topic_id-1)]= 0.0
            df[current_number_of_topics]= 0.0

            for row in most_relevant_documents_topic:
                contribution_to_topic_a = row[0]
                contribution_to_topic_b = row[1]
                indexs = df.index[df['texto_completo'] == row[-1]].tolist()
                if len(indexs)<1:
                    print('Error, text not found')
                #set final contribution to topic a, is contribution to topic_a multiply by the previous contribuiton
                df.loc[indexs,int(topic_id-1)] = contribution_to_topic_a
                df.loc[indexs,current_number_of_topics] = contribution_to_topic_b
                    
                
            #order columns
            intList=sorted([i for i in df.columns.values if type(i) is int])
            strList=sorted([i for i in df.columns.values if type(i) is str])
            new_order = intList+strList
            df = df[new_order]
            single_corpus_data['relevantDocumentsDict'] = df.to_dict('records')

            new_dict['relevantDocumentsDict_fromPython'] =json.dumps( single_corpus_data['relevantDocumentsDict'])

            end = time.time()
            print("Topic splitting - Getting new topic relevant documents ", end - start)
            start = time.time()

            #Get prepared data
            print('Getting new prepared data')
            temp = single_corpus_data['PreparedDataObtained']

            #update MdsDat
            #add temporal coordinates. We are going to change these later with the new topic similarity metric.
            temp['mdsDat']['x'].append(temp['mdsDat']['x'][topic_id-1])
            temp['mdsDat']['y'].append(temp['mdsDat']['y'][topic_id-1])
            temp['mdsDat']['topics'].append(len(temp['mdsDat']['topics'])+1)
            temp['mdsDat']['cluster'].append(temp['mdsDat']['cluster'][topic_id-1])
            #update the frequency of the topic
            old_frequency = temp['mdsDat']['Freq'][topic_id-1]
            temp['mdsDat']['Freq'][topic_id-1] = old_frequency*freq_topic_A
            temp['mdsDat']['Freq'].append(old_frequency*freq_topic_B)
            #Update topic.order
            temp['topic.order'].append(len(temp['topic.order'])+1)

            temp_tinfo_df = pd.DataFrame(temp[ 'tinfo'])
            temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(topic_id)].sort_values(by=['Freq'], ascending=False)
            temp_tinfo_df = pd.DataFrame(temp[ 'tinfo'])

            data_model_A_df = pd.DataFrame(data_model_A)
            data_model_B_df = pd.DataFrame(data_model_B)
            total_sum_frequency_corpus = data_model_A_df['term_frequency'].sum()+data_model_B_df['term_frequency'].sum()
            list_terms_A = list(data_model_A_df['vocab'])
            list_terms_B = list(data_model_B_df['vocab'])

            
            temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(topic_id)] = temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(topic_id)].apply(lambda row:  update_current_freq_and_total_freq_on_prepared_data(row, data_model_A_df,data_model_B_df, list_terms_A, list_terms_B,total_sum_frequency_corpus), axis=1)


            #copy values for the new subtopic b
            temp2 = temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(topic_id)]
            temp2.Category = 'Topic'+str(current_number_of_topics+1) 
            temp_tinfo_df = temp_tinfo_df.append(temp2, ignore_index=True)

            #update those values with the current terms probability\
            temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(current_number_of_topics+1)] = temp_tinfo_df[temp_tinfo_df.Category == 'Topic'+str(current_number_of_topics+1)].apply(lambda row:  update_current_freq_and_total_freq_on_prepared_data(row, data_model_B_df,data_model_A_df, list_terms_B, list_terms_A,total_sum_frequency_corpus), axis=1)

        
            #save the new tinfo
            temp_tinfo_df.reset_index(drop=True, inplace=True)
            temp[ 'tinfo']  = temp_tinfo_df.to_dict(orient='list')
            single_corpus_data['PreparedDataObtained'] = temp 


            end = time.time()
            print("Topic splitting - Getting new prepared data  ", end - start)
            start = time.time()


            #Get new topic similarity matrix
            print('Getting new topic similarity matrix')
            newClass = TopicVisExplorer("name") #dejar esta en el codigo final
            word_embedding_model = single_corpus_data['word_embedding_model']
            topn_terms = 20
            topk_documents = 20
            relevance_lambda = 0.6
            print('Calculando topic similarity metrix')

            lda_model = single_corpus_data['lda_model']
            corpus = single_corpus_data['corpus']
            id2word = single_corpus_data['id2word']
            matrix_documents_topic_contribution = pd.DataFrame(single_corpus_data['relevantDocumentsDict'])


            new_topic_similarity_matrix = newClass.calculate_topic_similarity_on_single_corpus_for_topic_splitting(current_number_of_topics, word_embedding_model, lda_model, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda)
            single_corpus_data['topic_similarity_matrix'] = new_topic_similarity_matrix
            print('Topic similarity matrix has been calculated')



            old_circle_positions = json_file['old_circle_positions']
    
            for omega in old_circle_positions.keys():
                old_circle_positions[omega].append(old_circle_positions[omega][topic_id-1])


            print('Calculating new circle positions with procrustes')

            new_circle_positions = get_circle_positions_from_old_matrix(old_circle_positions, new_topic_similarity_matrix )
            #print('json new circle,. estas son las keys', json.loads(new_circle_positions).keys())
            #print('primer arreglo', json.loads(new_circle_positions)['0.0'])

            single_corpus_data['new_circle_positions'] = new_circle_positions
            end = time.time()
            print("Topic splitting - Getting topic similarity metric  ", end - start)
            start = time.time()

            print('------- falta calcular el nuevo topic orderingX')                 
            topic_order =  single_corpus_data['topic.order']


            #visualizar neuvos resultados

            #PreparedDataObtained = single_corpus_data['PreparedDataObtained'] 

            #Return results in a dictionary


            new_dict['new_circle_positions'] = single_corpus_data['new_circle_positions'] 

            data = [single_corpus_data['PreparedDataObtained']]
            data_json_format = []
            for elem in data:
                elem = js.dumps(elem, cls=NumPyEncoder)
                data_json_format.append(elem)

            new_dict['PreparedDataObtained_fromPython'] = js.loads(data_json_format[0])


            #The following line is necessary to delete inf and nan values that javascript JSON.parse cant process
            new_dict['PreparedDataObtained_fromPython']['tinfo'] = pd.DataFrame(new_dict['PreparedDataObtained_fromPython']['tinfo']).replace([np.inf, -np.inf, np.nan], 0).to_dict()


            end = time.time()
            print("Tiempo en realizar el topic splitting - others", end - start)
                    
                
            with open('new_dict_topic_splitting.pickle', 'wb') as handle:
                pickle.dump(new_dict, handle, protocol=4)
           
            '''
            with open('new_dict_topic_splitting.pickle', 'rb') as handle:
                new_dict = pickle.load(handle)
            '''

            #print('--------En el topic splitting este es el mds data. Hay que revisar si el error viene de python o de javascript', temp['mdsDat'])
            print("**************************************************************************************")
            print('Topic order FINAL - TOPIC SPLITTING',single_corpus_data['PreparedDataObtained']['topic.order'])
            print("**************************************************************************************")
            return new_dict


    #save user study data. Create a pickle. Export to google drive
    @route('/export_user_study_data',  methods=['GET', 'POST'])
    def export_user_study_data(self):
        json_file = request.get_json()
        with open('user_study_results/user_study_data.pkl', 'wb') as handle:
            pickle.dump(json_file, handle, protocol=4) #protocol 4 is compatible with python 3.6+
            print("Single corpus data saved sucessfully")



        return 'exito!! user study saved'

    #Merge topic
    @route('/get_new_topic_vector',  methods=['GET', 'POST'])
    def get_new_topic_vector(self):
        start = time.time()
        global single_corpus_data
        global previous_single_corpus_data
        previous_single_corpus_data.append(deepcopy(single_corpus_data))
        
        json_file = request.get_json()


        index_topic_name_1 = json_file['index_topic_name_1']
        index_topic_name_2 = json_file['index_topic_name_2']

        #replace nuevos valores
        #single_corpus_data['tinfo_collection'] = json_file['lamData_new']    
        single_corpus_data['relevantDocumentsDict'] = json_file['relevantDocumentsDict_new']
        single_corpus_data['PreparedDataObtained']['tinfo']= pd.DataFrame(json_file['lamData_new']).to_dict()
        old_circle_positions = json_file['old_circle_positions']
        


        word_embedding_model = single_corpus_data['word_embedding_model']
        lda_model = single_corpus_data['lda_model']
        corpus = single_corpus_data['corpus']
        id2word = single_corpus_data['id2word']
        matrix_documents_topic_contribution = pd.DataFrame(single_corpus_data['relevantDocumentsDict'])
        topn_terms = 20
        topk_documents = 20
        relevance_lambda = 0.6
        
        
        #hay que hacer que get dict topic similarity matrix no reciba el prepared data, solo el lmabdata
        
        
        
        #get most relevant keywords sorted by relevance     
        #in merging, we should update this list
        tinfo_collection_1 = pd.DataFrame.from_dict(single_corpus_data['PreparedDataObtained']['tinfo'])
        tinfo_collection_1['relevance'] = relevance_lambda * tinfo_collection_1['logprob']+ (1.00-relevance_lambda)*tinfo_collection_1['loglift']

        # We need the topkeywords and toprelevantdocuments  vectors here!!!

        topkeywords_vectors_dict_1 = single_corpus_data['topkeywords_vectors_dict'] 
        relevantdocuments_vectors_dict_1 = single_corpus_data['relevantdocuments_vectors_dict']            
        topkeywords_vectors_new_merged_topic, relevantdocuments_vectors_new_merged_topic = get_topkeywords_relevantdocuments_by_topic_id(index_topic_name_1, word_embedding_model, lda_model,pd.DataFrame(single_corpus_data['relevantDocumentsDict']),  topn_terms, tinfo_collection_1, topk_documents)

        
        topkeywords_vectors_dict_1[index_topic_name_1] = topkeywords_vectors_new_merged_topic[index_topic_name_1]
        relevantdocuments_vectors_dict_1[index_topic_name_1] = relevantdocuments_vectors_new_merged_topic[index_topic_name_1]
        topkeywords_vectors_dict_1[index_topic_name_2] = topkeywords_vectors_new_merged_topic[index_topic_name_1]
        relevantdocuments_vectors_dict_1[index_topic_name_2] = relevantdocuments_vectors_new_merged_topic[index_topic_name_1]

        end = time.time()
        print("calculo de nuevos vectores", end - start)
        start = time.time()


        #old methods
        #new_topic_similarity_matrix =  get_dict_topic_similarity_matrix(word_embedding_model, lda_model,matrix_documents_topic_contribution,lda_model,matrix_documents_topic_contribution, topn_terms, single_corpus_data['PreparedDataObtained'], single_corpus_data['PreparedDataObtained'], topk_documents, relevance_lambda, tinfo_collection_1, tinfo_collection_1,topkeywords_vectors_dict_1,topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_1)

        #optimized method
        new_topic_similarity_matrix =  get_dict_topic_similarity_matrix_by_topic_ids(single_corpus_data['topic_similarity_matrix'], index_topic_name_1, index_topic_name_2, word_embedding_model, lda_model,matrix_documents_topic_contribution,lda_model,matrix_documents_topic_contribution, topn_terms, single_corpus_data['PreparedDataObtained'], single_corpus_data['PreparedDataObtained'], topk_documents, relevance_lambda, tinfo_collection_1, tinfo_collection_1,topkeywords_vectors_dict_1,topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_1)
        single_corpus_data['topic_similarity_matrix'] = new_topic_similarity_matrix

        end = time.time()
        print("calculo de nueva matrix ", end - start)
        start = time.time()
        new_circle_positions = get_circle_positions_from_old_matrix(old_circle_positions, new_topic_similarity_matrix )

        #save data
        single_corpus_data['new_circle_positions']  = new_circle_positions
        single_corpus_data['tinfo_collection'] = tinfo_collection_1
        single_corpus_data['topkeywords_vectors_dict'] = topkeywords_vectors_dict_1
        single_corpus_data['relevantdocuments_vectors_dict'] = relevantdocuments_vectors_dict_1
        print("se ha calculado con optimization numer 1s")

        end = time.time()



        #with open('models_output/testing_spliting.pkl', 'wb') as handle:
            #pickle.dump(single_corpus_data, handle, protocol=4) #protocol 4 is compatible with python 3.6+
            #print("Single corpus data saved sucessfully")


        print('modelo guardado para probar splitting')


        print("calculo de nuevas posiciones ", end - start)
        return new_circle_positions

    
    @route('/get_topic_similarity_matrix_single_corpus',  methods=['GET'])
    def topic_similarity_matrix_excel_single_corpus(self):
        #send data regarding to current omega value selected
        lambda_lambda_topic_similarity_current = request.args.get('value', 0, type=float)        
        global single_corpus_data                
        return Response(js.dumps( single_corpus_data['topic_similarity_matrix'][lambda_lambda_topic_similarity_current].tolist()),  mimetype='application/json')


    @route('/singlecorpus')
    def single_corpus(self,  methods=['GET']):           
        print('Estoy en la funcion single corpuuuus') 
        #load data
        global scenarios
        global single_corpus_data
        single_corpus_data = scenarios[request.args.get("scenario")]       
        
        assert  single_corpus_data["multi"] == False, "Scenario not for single corpus"


        lda_model = single_corpus_data['lda_model']
        corpus = single_corpus_data['corpus']
        id2word = single_corpus_data['id2word']         
        topic_similarity_matrix = single_corpus_data['topic_similarity_matrix']         
        PreparedDataObtained = single_corpus_data['PreparedDataObtained']
        data_dict = single_corpus_data['data_dict'] 
        new_circle_positions = single_corpus_data['new_circle_positions'] 
        topic_order =  single_corpus_data['topic.order']
        topic_similarity_matrix = single_corpus_data['topic_similarity_matrix']         
        PreparedDataObtained['human_in_the_loop'] = False if request.args.get("hitl") == "false" else True 
        #prepare and run html
        html = prepared_html_in_flask(data = [PreparedDataObtained],  topic_order = topic_order,  type_vis = 1,  new_circle_positions = new_circle_positions)
        return render_template_string(html)
    
    @route('/multicorpora')
    def multi_corpora(self):            
        #load data
        global scenarios
        global multi_corpora_data
        multi_corpora_data = scenarios[request.args.get("scenario")]
        assert  multi_corpora_data["multi"] == True, "Scenario not for multicorpora comparison"

        lda_model_1 = multi_corpora_data['lda_model_1']
        lda_model_2 = multi_corpora_data['lda_model_2']
        corpus_1 = multi_corpora_data['corpus_1']
        corpus_2 = multi_corpora_data['corpus_2']
        id2word_1 = multi_corpora_data['id2word_1'] 
        id2word_2 = multi_corpora_data['id2word_2']                 
        PreparedDataObtained_collection_1 = multi_corpora_data['PreparedDataObtained_collection_1']
        PreparedDataObtained_collection_2 = multi_corpora_data['PreparedDataObtained_collection_2']
        data_dict_1 = multi_corpora_data['data_dict_1']         
        data_dict_2 = multi_corpora_data['data_dict_2']         
        topic_order_collection_1 =  multi_corpora_data['topic_order_collection_1']
        topic_order_collection_2 =  multi_corpora_data['topic_order_collection_2']
        topic_similarity_matrix = multi_corpora_data['topic_similarity_matrix']         
                                                                                        
        html = prepared_html_in_flask(data = [PreparedDataObtained_collection_1],topic_order =  topic_order_collection_1, type_vis = 2, matrix_sankey = topic_similarity_matrix, data_2 = [PreparedDataObtained_collection_2], topic_order_2 = topic_order_collection_2)
        return render_template_string(html)



        





    