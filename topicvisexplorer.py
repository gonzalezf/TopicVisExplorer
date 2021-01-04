# -*- coding: utf-8 -*-

import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
import numpy as np
import sklearn
import os
import pandas as pd
import pickle

from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json, Response, render_template_string, jsonify
from flask_classful import FlaskView,route
from _display import *
from _prepare import prepare, js_PCoA, PreparedData, _pcoa
from _topic_similarity_matrix import *
from os import path, walk
from gensim.models.keyedvectors import KeyedVectors
from scipy.spatial import procrustes


single_corpus_data = {}
multi_corpora_data = {}

class TopicVisExplorer:

    app = None
    
    def __init__(self, name):        
        self.app = Flask(name)
        TestView.register(self.app, route_base = '/')
    
    def run(self):
        self.app.run(debug=False)
    

    def get_circle_positions(self, topic_similarity_matrix):
        #Get new circle position regarding to proposed topic similarity matrix
        new_circle_positions = dict()
        for lambda_ in range(0, 101):
            lambda_ = lambda_/100
            matrix_cosine_distance = 1-topic_similarity_matrix[lambda_]
            np.fill_diagonal(matrix_cosine_distance,0)
            new_circle_positions[lambda_]=_pcoa(matrix_cosine_distance, n_components=2).tolist()        
        #Apply procrusteres 
        lambdas = list(new_circle_positions.keys())
        standardized_matrix = dict()
        disparity_values = dict()
        original_a = new_circle_positions[0.0]
        for i in range(len(lambdas)-1):
            #print(lambdas[i], lambdas[i+1])
            original_b = new_circle_positions[lambdas[i+1]]
            mtx1, mtx2, disparity = procrustes(original_a, original_b)
            disparity_values[lambdas[i]] = disparity
            standardized_matrix[lambdas[i]] = mtx1.tolist()
            original_a = mtx2            
        standardized_matrix[lambdas[len(lambdas)-1]] = mtx2.tolist()
        disparity_values[lambdas[len(lambdas)-1]] = disparity

        new_circle_positions = standardized_matrix
        new_circle_positions= json.dumps(new_circle_positions)
        return new_circle_positions


    
    

        
    def calculate_topic_similarity_on_single_corpus(self, word_embedding_model, lda_model, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda ):        
        if 'data_dict' not in single_corpus_data:
            data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa') 
            single_corpus_data['data_dict']  = data_dict  
        if 'PreparedDataObtained' not in single_corpus_data:         
            temp = prepare(**data_dict)            
            single_corpus_data['PreparedDataObtained'] =  temp.to_dict()

        if 'relevantDocumentsDict' not in single_corpus_data:
            relevantDocumentsDict = matrix_documents_topic_contribution.to_dict(orient='records')
            single_corpus_data['relevantDocumentsDict'] = relevantDocumentsDict

        return get_dict_topic_similarity_matrix(word_embedding_model, lda_model,matrix_documents_topic_contribution,lda_model,matrix_documents_topic_contribution, topn_terms, single_corpus_data['PreparedDataObtained'], single_corpus_data['PreparedDataObtained'], topk_documents, relevance_lambda)


    def calculate_topic_similarity_on_multi_corpora(self, word_embedding_model, lda_model_1, lda_model_2, corpus_1,corpus_2,  id2word_1,id2word_2, matrix_documents_topic_contribution_1, matrix_documents_topic_contribution_2, topn_terms, topk_documents, relevance_lambda ):        


        if 'data_dict_1' not in multi_corpora_data:
            data_dict_1 = gensim_helpers.prepare(lda_model_1, corpus_1,id2word_1, mds='pcoa') 
            multi_corpora_data['data_dict_1']  = data_dict_1  
        if 'PreparedDataObtained_collection_1' not in multi_corpora_data:         
            temp_1 = prepare(**data_dict_1)            
            multi_corpora_data['PreparedDataObtained_collection_1'] =  temp_1.to_dict()

        if 'relevantDocumentsDict_collection_1' not in multi_corpora_data:
            relevantDocumentsDict_collection_1 = matrix_documents_topic_contribution_1.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_1'] = relevantDocumentsDict_collection_1

        if 'data_dict_2' not in multi_corpora_data:
            data_dict_2 = gensim_helpers.prepare(lda_model_2, corpus_2,id2word_2, mds='pcoa') 
            multi_corpora_data['data_dict_2']  = data_dict_2
        if 'PreparedDataObtained_collection_2' not in multi_corpora_data:         
            temp_2 = prepare(**data_dict_2)            
            multi_corpora_data['PreparedDataObtained_collection_2'] =  temp_2.to_dict()

        if 'relevantDocumentsDict_collection_2' not in multi_corpora_data:
            relevantDocumentsDict_collection_2 = matrix_documents_topic_contribution_2.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_2'] = relevantDocumentsDict_collection_2


        return get_dict_topic_similarity_matrix(word_embedding_model, lda_model_1,matrix_documents_topic_contribution_1,lda_model_2,matrix_documents_topic_contribution_2, topn_terms, multi_corpora_data['PreparedDataObtained_collection_1'], multi_corpora_data['PreparedDataObtained_collection_2'], topk_documents, relevance_lambda)


    
    def prepare_single_corpus(self, lda_model, corpus, id2word, matrix_documents_topic_contribution, topic_similarity_matrix):
        
        if 'data_dict' not in single_corpus_data:
            data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa') 
            single_corpus_data['data_dict']  = data_dict  
        if 'PreparedDataObtained' not in single_corpus_data:         
            temp = prepare(**data_dict)            
            single_corpus_data['PreparedDataObtained'] =  temp.to_dict()

        if 'relevantDocumentsDict' not in single_corpus_data:
            relevantDocumentsDict = matrix_documents_topic_contribution.to_dict(orient='records')
            single_corpus_data['relevantDocumentsDict'] = relevantDocumentsDict


        new_circle_positions = self.get_circle_positions(topic_similarity_matrix)
        

        single_corpus_data['lda_model'] = lda_model,
        single_corpus_data['corpus'] = corpus
        single_corpus_data['id2word'] = id2word
        single_corpus_data['topic_similarity_matrix'] = topic_similarity_matrix        
        single_corpus_data['topic.order'] = single_corpus_data['PreparedDataObtained']['topic.order']
        single_corpus_data['new_circle_positions'] = new_circle_positions

    def prepare_multi_corpora(self, lda_model_1,lda_model_2, corpus_1, corpus_2,  id2word_1,id2word_2, matrix_documents_topic_contribution_1,matrix_documents_topic_contribution_2, topic_similarity_matrix):

        if 'data_dict_1' not in multi_corpora_data:
            data_dict_1 = gensim_helpers.prepare(lda_model_1, corpus_1,id2word_1, mds='pcoa') 
            multi_corpora_data['data_dict_1']  = data_dict_1  
        if 'PreparedDataObtained_collection_1' not in multi_corpora_data:         
            temp_1 = prepare(**data_dict_1)            
            multi_corpora_data['PreparedDataObtained_collection_1'] =  temp_1.to_dict()

        if 'relevantDocumentsDict_collection_1' not in multi_corpora_data:
            relevantDocumentsDict_collection_1 = matrix_documents_topic_contribution_1.to_dict(orient='records')
            multi_corpora_data['relevantDocumentsDict_collection_1'] = relevantDocumentsDict_collection_1

        if 'data_dict_2' not in multi_corpora_data:
            data_dict_2 = gensim_helpers.prepare(lda_model_2, corpus_2,id2word_2, mds='pcoa') 
            multi_corpora_data['data_dict_2']  = data_dict_2
        if 'PreparedDataObtained_collection_2' not in multi_corpora_data:         
            temp_2 = prepare(**data_dict_2)            
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
                pickle.dump(single_corpus_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
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


    def load_single_corpus_data(self, route_file):
        with open(route_file, 'rb') as handle:
            global single_corpus_data
            single_corpus_data = pickle.load(handle)            
            print("Data loaded sucessfully")

    def load_multi_corpora_data(self, route_file):
        with open(route_file, 'rb') as handle:
            global multi_corpora_data
            multi_corpora_data = pickle.load(handle)            
            print("Data loaded sucessfully")

        


class TestView(FlaskView):

    @route('/')
    def index(self):
    # http://localhost:5000/
        return "<h1>index</h1>"

    @route('/singlecorpus')
    def single_corpus(self):            
        #load data
        global single_corpus_data        
        lda_model = single_corpus_data['lda_model']
        corpus = single_corpus_data['corpus']
        id2word = single_corpus_data['id2word'] 
        relevantDocumentsDict = single_corpus_data['relevantDocumentsDict']
        topic_similarity_matrix = single_corpus_data['topic_similarity_matrix']         
        PreparedDataObtained = single_corpus_data['PreparedDataObtained']
        data_dict = single_corpus_data['data_dict'] 
        new_circle_positions = single_corpus_data['new_circle_positions'] 
        topic_order =  single_corpus_data['topic.order']

        #prepare and run html
        html = prepared_html_in_flask(data = [PreparedDataObtained], relevantDocumentsDict = relevantDocumentsDict, topic_order = topic_order,  type_vis = 1,  new_circle_positions = new_circle_positions)
        return render_template_string(html)
    
    @route('/multicorpora')
    def multi_corpora(self):            
        #load data
        global multi_corpora_data        
        lda_model_1 = multi_corpora_data['lda_model_1']
        lda_model_2 = multi_corpora_data['lda_model_2']
        corpus_1 = multi_corpora_data['corpus_1']
        corpus_2 = multi_corpora_data['corpus_2']
        id2word_1 = multi_corpora_data['id2word_1'] 
        id2word_2 = multi_corpora_data['id2word_2'] 
        relevantDocumentsDict_collection_1 = multi_corpora_data['relevantDocumentsDict_collection_1']
        relevantDocumentsDict_collection_2 = multi_corpora_data['relevantDocumentsDict_collection_2']        
        PreparedDataObtained_collection_1 = multi_corpora_data['PreparedDataObtained_collection_1']
        PreparedDataObtained_collection_2 = multi_corpora_data['PreparedDataObtained_collection_2']
        data_dict_1 = multi_corpora_data['data_dict_1']         
        data_dict_2 = multi_corpora_data['data_dict_2']         
        topic_order_collection_1 =  multi_corpora_data['topic_order_collection_1']
        topic_order_collection_2 =  multi_corpora_data['topic_order_collection_2']
        topic_similarity_matrix = multi_corpora_data['topic_similarity_matrix']         
                                                                                        
        html = prepared_html_in_flask(data = [PreparedDataObtained_collection_1], relevantDocumentsDict = relevantDocumentsDict_collection_1,topic_order =  topic_order_collection_1, type_vis = 2, matrix_sankey = topic_similarity_matrix, data_2 = [PreparedDataObtained_collection_2], relevantDocumentsDict_2 = relevantDocumentsDict_collection_2, topic_order_2 = topic_order_collection_2)
        return render_template_string(html)
    


        





    