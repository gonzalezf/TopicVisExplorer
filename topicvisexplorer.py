# -*- coding: utf-8 -*-

import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
import numpy as np
import sklearn
import os
import pandas as pd
import pickle
import json as js
import time


from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json, Response, render_template_string, jsonify
from flask_classful import FlaskView,route
from _display import *
from _prepare import prepare, js_PCoA, PreparedData, _pcoa
from _topic_similarity_matrix import *
from _get_new_circle_positions import *
from _guidedLda_helpers import *

from os import path, walk
from gensim.models.keyedvectors import KeyedVectors
from scipy.spatial import procrustes


from utils import get_id, write_ipynb_local_js, NumPyEncoder
from _prepare import PreparedData


single_corpus_data = {}
multi_corpora_data = {}

class TopicVisExplorer:

    app = None
    
    def __init__(self, name):        
        self.app = Flask(name)
        TestView.register(self.app, route_base = '/')
    
    def run(self):
        self.app.run(debug=False)
    


    

        
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
        tinfo_collection_1 = pd.DataFrame.from_dict(single_corpus_data['PreparedDataObtained']['tinfo'])
        tinfo_collection_1['relevance'] = relevance_lambda * tinfo_collection_1['logprob']+ (1.00-relevance_lambda)*tinfo_collection_1['loglift']

        tinfo_collection_2 = pd.DataFrame.from_dict(single_corpus_data['PreparedDataObtained']['tinfo'])
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
        #return Response(js.dumps( single_corpus_data['relevantDocumentsDict']),  mimetype='application/json')
        return Response(js.dumps( random.sample(single_corpus_data['relevantDocumentsDict'],2000)),  mimetype='application/json')


    #Split topic

    @route('/getLdaModel',  methods=['GET', 'POST'])
    def get_new_lda_model(self):
        global single_corpus_data   
        json_file = request.get_json()


        old_circle_positions = json_file['old_circle_positions']
        topic_id = json_file['topic_id'] #tHE FIRST TOPIC IS ID=1, not 0!
        new_keywords_seeds = json_file['new_keywords_seeds']

        '''

        start = time.time()

        print('estoy en la funcion para hacer el splitting')

        #1.= Get old seeds from the topics that it shouldnt change
        lda_model = single_corpus_data['lda_model']
        id2word = single_corpus_data['id2word']
        corpus = single_corpus_data['corpus']


        new_number_topics = lda_model.num_topics+1




        #last_lda_model_dict = dict()
        #for topic_id in range(lda_model.num_topics):
            #current_list = [id2word[w]for w,p in lda_model.get_topic_terms(topic_id, topn=10)]
            #for elem in current_list:
            #last_lda_model_dict[elem] = topic_id


        last_lda_model_dict_all_terms = dict()
        for topic_id in range(lda_model.num_topics):
            current_list = [id2word[w]for w,p in lda_model.get_topic_terms(topic_id, topn=8)]
            last_lda_model_dict_all_terms[topic_id] = current_list

        print('Estas son las semillas actualeees', last_lda_model_dict_all_terms)

        #create new lda model

        # identify the new seeds given from the user 
        new_seeds_topic_a = [k for k,v in new_keywords_seeds.items() if v == 'TopicA']
        new_seeds_topic_b = [k for k,v in new_keywords_seeds.items() if v == 'TopicB']

        # replace the new seeds in the initial topic (topic_id-1) and lets create a new topic
        last_lda_model_dict_all_terms[topic_id-1] = new_seeds_topic_a
        last_lda_model_dict_all_terms[lda_model.num_topics] = new_seeds_topic_b


        eta = create_eta(last_lda_model_dict_all_terms, id2word, ntopics = new_number_topics)
        new_guided_lda_model = create_new_guided_lda_model(eta, id2word, corpus, new_number_topics)


        #print('esto fue lo q se genero', new_guided_lda_model)


        #update the LDA model
        lda_model = new_guided_lda_model 
        print('Creando nuevos archivos para actualizar la visualizacion')
        # Get new datat dict
        data_dict = gensim_helpers.prepare(lda_model, corpus,id2word) 
        single_corpus_data['data_dict']  = data_dict  
        #Update the preparedDataObtained
        print("A NEW PREPARED DATA HA SIDO CREADO -0 Topics splitting!!")
        temp = prepare(**single_corpus_data['data_dict'])            
        single_corpus_data['PreparedDataObtained'] =  temp.to_dict()
        print('Obteniendo nuevos documentos relevantes')
        matrix_documents_topic_contribution, _ = lda_model.inference(corpus)
        matrix_documents_topic_contribution /= matrix_documents_topic_contribution.sum(axis=1)[:, None]
        matrix_documents_topic_contribution = pd.DataFrame(matrix_documents_topic_contribution)

        df = pd.DataFrame(single_corpus_data['relevantDocumentsDict'])
        contents = df[df.columns[-1]].reset_index(drop=True)
        matrix_documents_topic_contribution = pd.concat([matrix_documents_topic_contribution, contents], axis=1)
        print('Esta es la matriz final resultante', matrix_documents_topic_contribution.head())


        #print('Nuevos documentos', matrix_documents_topic_contribution.head())
        relevantDocumentsDict = matrix_documents_topic_contribution.to_dict(orient='records')
        single_corpus_data['relevantDocumentsDict'] = relevantDocumentsDict

        #calcular metrica de similutd
        print('creando nueva class')
        newClass = TopicVisExplorer("name")
        word_embedding_model = single_corpus_data['word_embedding_model']
        topn_terms = 20
        topk_documents = 20
        relevance_lambda = 0.6
        print('Calculando topic similarity metrix')

        new_topic_similarity_matrix = newClass.calculate_topic_similarity_on_single_corpus(word_embedding_model, lda_model, corpus, id2word, matrix_documents_topic_contribution,topn_terms, topk_documents, relevance_lambda)
        single_corpus_data['topic_similarity_matrix'] = new_topic_similarity_matrix
        print('Topic similarity matrix has been calculated')


        old_circle_positions = json_file['old_circle_positions']


        #On procrustes, the matrixes cant be of different shape, therefore it is necessary to add a new row in each key.
        # there is going to be a new topic, therefore, the last position of this new topic is the position of the current topic that we need to split
        for omega in old_circle_positions.keys():
            old_circle_positions[omega].append(old_circle_positions[omega][topic_id-1])


        print('Calculating new circle positions with procrustes')

        new_circle_positions = get_circle_positions_from_old_matrix(old_circle_positions, new_topic_similarity_matrix )
        print('json new circle,. estas son las keys', json.loads(new_circle_positions).keys())
        print('primer arreglo', json.loads(new_circle_positions)['0.0'])

        #new_circle_positions = get_circle_positions(topic_similarity_matrix)
        single_corpus_data['new_circle_positions'] = new_circle_positions

        print('------- falta calcular el nuevo topic orderingX')                 
        topic_order =  single_corpus_data['topic.order']


        #visualizar neuvos resultados

        PreparedDataObtained = single_corpus_data['PreparedDataObtained'] 

        #prepare and run html
        #html = prepared_html_in_flask(data = [PreparedDataObtained],  topic_order = topic_order,  type_vis = 1,  new_circle_positions = new_circle_positions)
        print('obtuvo un nuevo html')





        #Return results to the visualization

        print('voy a retornar nueva lista de documentos')
        new_dict = dict()

        new_dict['new_circle_positions'] = single_corpus_data['new_circle_positions'] 
        new_dict['relevantDocumentsDict_fromPython'] =js.dumps( single_corpus_data['relevantDocumentsDict'])

        data = [single_corpus_data['PreparedDataObtained']]
        data_json_format = []
        for elem in data:
            elem = js.dumps(elem, cls=NumPyEncoder)
            data_json_format.append(elem)

        new_dict['PreparedDataObtained_fromPython'] = js.loads(data_json_format[0])


        #The following line is necessary to delete inf and nan values that javascript JSON.parse cant process
        new_dict['PreparedDataObtained_fromPython']['tinfo'] = pd.DataFrame(new_dict['PreparedDataObtained_fromPython']['tinfo']).replace([np.inf, -np.inf, np.nan], 0).to_dict()




        end = time.time()
        print("Tiempo en realizar el topic splitting - Final Sending data", end - start)
                
        with open('new_dict_topic_splitting.pickle', 'wb') as handle:
            pickle.dump(new_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

                # Load data (deserialize)
        '''
        with open('new_dict_topic_splitting.pickle', 'rb') as handle:
            new_dict = pickle.load(handle)


        print('CTMMMM FUNCIONAAAAAAAAAAAA')
        return new_dict

       

    




    #Merge topic
    @route('/get_new_topic_vector',  methods=['GET', 'POST'])
    def get_new_topic_vector(self):
        start = time.time()
        global single_corpus_data   
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
        print("calculo de nuevas posiciones ", end - start)
        
        return new_circle_positions

    
    @route('/get_topic_similarity_matrix_single_corpus',  methods=['GET'])
    def topic_similarity_matrix_excel_single_corpus(self):
        #send data regarding to current omega value selected
        lambda_lambda_topic_similarity_current = request.args.get('value', 0, type=float)        
        global single_corpus_data                
        return Response(js.dumps( single_corpus_data['topic_similarity_matrix'][lambda_lambda_topic_similarity_current].tolist()),  mimetype='application/json')


    @route('/singlecorpus')
    def single_corpus(self):           
        print('Estoy en la funcion single corpuuuus') 
        #load data
        global single_corpus_data        



        lda_model = single_corpus_data['lda_model']
        corpus = single_corpus_data['corpus']
        id2word = single_corpus_data['id2word']         
        topic_similarity_matrix = single_corpus_data['topic_similarity_matrix']         
        PreparedDataObtained = single_corpus_data['PreparedDataObtained']
        data_dict = single_corpus_data['data_dict'] 
        new_circle_positions = single_corpus_data['new_circle_positions'] 
        topic_order =  single_corpus_data['topic.order']
        topic_similarity_matrix = single_corpus_data['topic_similarity_matrix']         




        #prepare and run html
        html = prepared_html_in_flask(data = [PreparedDataObtained],  topic_order = topic_order,  type_vis = 1,  new_circle_positions = new_circle_positions)
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
        PreparedDataObtained_collection_1 = multi_corpora_data['PreparedDataObtained_collection_1']
        PreparedDataObtained_collection_2 = multi_corpora_data['PreparedDataObtained_collection_2']
        data_dict_1 = multi_corpora_data['data_dict_1']         
        data_dict_2 = multi_corpora_data['data_dict_2']         
        topic_order_collection_1 =  multi_corpora_data['topic_order_collection_1']
        topic_order_collection_2 =  multi_corpora_data['topic_order_collection_2']
        topic_similarity_matrix = multi_corpora_data['topic_similarity_matrix']         
                                                                                        
        html = prepared_html_in_flask(data = [PreparedDataObtained_collection_1],topic_order =  topic_order_collection_1, type_vis = 2, matrix_sankey = topic_similarity_matrix, data_2 = [PreparedDataObtained_collection_2], topic_order_2 = topic_order_collection_2)
        return render_template_string(html)
    


        





    