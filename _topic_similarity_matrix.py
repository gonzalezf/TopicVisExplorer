import unidecode
import _prepare
import gensim_helpers
import spacy
import re, numpy as np, pandas as pd

from string import punctuation
from string import digits
from nltk.tokenize import TweetTokenizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from gensim.utils import lemmatize, simple_preprocess
import time

from pandarallel import pandarallel
pandarallel.initialize()
'''My own tokenizer '''
def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]


#this should be easy to change for users
punctuation+="¡¿<>'`"
punctuation+='"'
nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])    
stop_words = stopwords.words('english')

#Remove digits and puntuaction
remove_digits = str.maketrans(digits, ' '*len(digits))#remove_digits = str.maketrans('', '', digits)
remove_punctuation = str.maketrans(punctuation, ' '*len(punctuation))#remove_punctuation = str.maketrans('', '', punctuation)
remove_hashtags_caracter = str.maketrans('#', ' '*len('#'))
#las palabras de los hashtag se mantiene, pero no el simbolo. 

tknzr = TweetTokenizer()
def sent_to_words(sentence):
    return tknzr.tokenize(sentence)
    
def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    """https://spacy.io/api/annotation"""
    texts_out = []
    doc = nlp(" ".join(texts)) 
    texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out
        
def text_cleaner(tweet):
    tweet = tweet.translate(remove_digits)
    #tweet = tweet.lower() it wasn't a good idea,, we lost a lot of
    tweet = tweet.translate(remove_punctuation)
    tweet = tweet.translate(remove_hashtags_caracter)
    tweet = tweet.lower()
    tweet = unidecode.unidecode(tweet)
    tweet = sent_to_words(tweet)
    tweet = remove_stopwords(tweet)
    new_tweet  = []
    for elem in tweet:
        if len(elem)>0:
            new_tweet.append(elem[0])
    tweet = lemmatization(new_tweet, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])
    return tweet[0]

#Note, that vectors are going to be calculated according to topic order of PreparedData
def get_dicts_relevant_keywords_documents(lda_model,df_relevant_documents, n_terms, PreparedData_dict_with_more_info):
    num_topics = lda_model.num_topics
    topKeywordsDict = {}
    for topic_id in range(num_topics):        
        topKeywordsDict[topic_id] = []        
        def save_relevant_keywords_in_dict(row):
            topKeywordsDict[topic_id].append({  #el topic_id, debe ser segun el orden de lda_model
                "term":row['Term'],
                "relevance":row['relevance']
            })
        PreparedData_dict_with_more_info.loc[PreparedData_dict_with_more_info['Category'] == 'Topic'+str(topic_id+1)].sort_values(by='relevance', ascending=False)[['Term','relevance']][:n_terms].parallel_apply(save_relevant_keywords_in_dict, axis=1)    
    return topKeywordsDict

def get_dicts_relevant_keywords_documents_by_topic_id(topic_id, lda_model,df_relevant_documents, n_terms, PreparedData_dict_with_more_info):    
    topKeywordsDict = {}
    topKeywordsDict[topic_id] = []        
    def save_relevant_keywords_in_dict(row):
        topKeywordsDict[topic_id].append({  #el topic_id, debe ser segun el orden de lda_model
            "term":row['Term'],
            "relevance":row['relevance']
        })
    PreparedData_dict_with_more_info.loc[PreparedData_dict_with_more_info['Category'] == 'Topic'+str(topic_id+1)].sort_values(by='relevance', ascending=False)[['Term','relevance']][:n_terms].parallel_apply(save_relevant_keywords_in_dict, axis=1)    
    return topKeywordsDict


def getDocumentVector(text, wordembedding,  topic_id ,  PreparedData_dict_with_more_info):    
    #print("este es el texto", text)
    list_terms_relevance = PreparedData_dict_with_more_info.loc[PreparedData_dict_with_more_info['Category'] == 'Topic'+str(topic_id+1)].sort_values(by='relevance', ascending=False)['Term'].tolist()
    document_vector = 0.0
    words_found = set()
    for word in text_cleaner(text):    
        if word in list_terms_relevance:
            raking_word = float(list_terms_relevance.index(word)+1)
            if word in wordembedding: #if word in wordembedding.wv:
                #print("WORD FOUND", word, raking_word)
                document_vector+=wordembedding[word]/raking_word #aqui hay que ponderar
                words_found.add(word.upper())
            else:
                pass
                #print("WARNING, Word not found:", word)    
    return document_vector
            

def get_topkeywords_relevantdocuments_by_topic_id(topic_id, wordembedding, lda_model,matrix_documents_topic_contribution,  n_terms,PreparedData_dict_with_more_info, topkdocuments): #n_terms : numero de top keywords a considerar
    matrix_documents_topic_contribution.columns = matrix_documents_topic_contribution.columns.map(str)
    topKeywordsDict = get_dicts_relevant_keywords_documents_by_topic_id(topic_id, lda_model, matrix_documents_topic_contribution, n_terms,   PreparedData_dict_with_more_info)    

    ##Create top keyword vector per topic
    topkeywords_vectors_dict = {}    
    topkeywords_vector = 0
    ranking = 1.0
    for item in topKeywordsDict[topic_id]: #cambiar esta parte!
        if item['term'] in wordembedding: 
            topkeywords_vector += wordembedding[item['term']]/ranking
        else:
            pass
            #print("WARNING NOT FOUND: ", item['term']," position:",ranking)
        ranking+=1
    topkeywords_vectors_dict[topic_id] = topkeywords_vector
        
    #Create a top relevant document vector    
    relevantdocuments_vectors_dict = {}

    relevantDocumentsvector = 0.0
    j = 0
    for index, item in matrix_documents_topic_contribution.sort_values(by=[str(topic_id)], ascending=False)[0:topkdocuments].iterrows():
        j+=1                                    
        relevantDocumentsvector+= float(item[str(topic_id)])*getDocumentVector(item[matrix_documents_topic_contribution.columns[-1]], wordembedding, topic_id, PreparedData_dict_with_more_info)             
    relevantdocuments_vectors_dict[topic_id] = relevantDocumentsvector        
    
    return (topkeywords_vectors_dict, relevantdocuments_vectors_dict)


def get_topkeywords_relevantdocuments_vectors(wordembedding, lda_model,matrix_documents_topic_contribution,  n_terms,PreparedData_dict_with_more_info, topkdocuments): #n_terms : numero de top keywords a considerar
    matrix_documents_topic_contribution.columns = matrix_documents_topic_contribution.columns.map(str)
    topKeywordsDict = get_dicts_relevant_keywords_documents(lda_model, matrix_documents_topic_contribution, n_terms,   PreparedData_dict_with_more_info)    

    ##Create top keyword vector per topic
    topkeywords_vectors_dict = {}
    num_topics = lda_model.num_topics
    for topic_id in range(num_topics):
        topkeywords_vector = 0
        ranking = 1.0
        for item in topKeywordsDict[topic_id]:
            if item['term'] in wordembedding: 
                topkeywords_vector += wordembedding[item['term']]/ranking
            else:
                pass
                #print("WARNING NOT FOUND: ", item['term']," position:",ranking)
            ranking+=1
        topkeywords_vectors_dict[topic_id] = topkeywords_vector
        
    #Create a top relevant document vector    
    relevantdocuments_vectors_dict = {}
    for topic_id in range(num_topics):
        relevantDocumentsvector = 0.0
        j = 0
        print('//////////////////////////////////////////')
        print('COLUMNS, ', matrix_documents_topic_contribution.columns)
        print('SEARCHING', str(topic_id))
        print('//////////////////////////////////////////')
        for index, item in matrix_documents_topic_contribution.sort_values(by=[str(topic_id)], ascending=False)[0:topkdocuments].iterrows():
            j+=1                                    
            relevantDocumentsvector+= float(item[str(topic_id)])*getDocumentVector(item[matrix_documents_topic_contribution.columns[-1]], wordembedding, topic_id, PreparedData_dict_with_more_info)             
        relevantdocuments_vectors_dict[topic_id] = relevantDocumentsvector        
    
    return (topkeywords_vectors_dict, relevantdocuments_vectors_dict)

#Here, we calculate once the topkeywords_vector and the relevant documents_vector for each topic
#We are going to calculate several times:      #final topic vector = (lambda)topic_keyword_vector + (lambda-1)topic_document_vector
#because we are going to try different lambda (between 0 and 1)


#This matrix is calculated by a specific lambda. 
def get_matrix_by_lambda(wordembedding, lda_model_1,most_relevant_documents_1,lda_model_2,most_relevant_documents_2, n_terms, lambda_, PreparedData_dict_with_more_info_1, PreparedData_dict_with_more_info_2, topkdocuments, relevance_lambda, topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1, topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_2):
    #final topic vector = (lambda)topic_keyword_vector + (lambda-1)topic_document_vector
    

    #get final topic vectors model 1    
    num_topics_1 = lda_model_1.num_topics
    final_topic_vectors_dict_1 = dict()
    for topic_id in range(num_topics_1):
        final_topic_vector = lambda_*topkeywords_vectors_dict_1[topic_id]+(1-lambda_)*relevantdocuments_vectors_dict_1[topic_id]
        final_topic_vectors_dict_1[topic_id] = final_topic_vector
    
    #get final topic vectors model 2
    num_topics_2 = lda_model_2.num_topics
    final_topic_vectors_dict_2 = dict()
    for topic_id in range(num_topics_2):
        final_topic_vector = lambda_*topkeywords_vectors_dict_2[topic_id]+(1-lambda_)*relevantdocuments_vectors_dict_2[topic_id]
        final_topic_vectors_dict_2[topic_id] = final_topic_vector
    


    #lets calculate the topic similarity matrix for this omega (lambda_)
    topic_similarity_matrix = []
    for i in range(num_topics_1):
        row = []
        for j in range(num_topics_2):
            topic_i = final_topic_vectors_dict_1[i].reshape(1,-1)
            topic_j = final_topic_vectors_dict_2[j].reshape(1,-1)
            row.append(float(cosine_similarity(topic_i,topic_j)))
        topic_similarity_matrix.append(row)
    topic_similarity_matrix= np.asarray(topic_similarity_matrix)
    return topic_similarity_matrix

#optimize this function. Right now is the same than get_matrix_by_lambda
def get_matrix_by_lambda_by_topic_ids(old_topic_similarity_matrix, id_topic_1, id_topic_2, wordembedding, lda_model_1,most_relevant_documents_1,lda_model_2,most_relevant_documents_2, n_terms, lambda_, PreparedData_dict_with_more_info_1, PreparedData_dict_with_more_info_2, topkdocuments, relevance_lambda, topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1, topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_2):
    #final topic vector = (lambda)topic_keyword_vector + (lambda-1)topic_document_vector
    

    #get final topic vectors model 1    
    num_topics_1 = lda_model_1.num_topics
    final_topic_vectors_dict_1 = dict()
    for topic_id in range(num_topics_1):
        final_topic_vector = lambda_*topkeywords_vectors_dict_1[topic_id]+(1-lambda_)*relevantdocuments_vectors_dict_1[topic_id]
        final_topic_vectors_dict_1[topic_id] = final_topic_vector
    
    #get final topic vectors model 2
    num_topics_2 = lda_model_2.num_topics
    final_topic_vectors_dict_2 = dict()
    for topic_id in range(num_topics_2):
        final_topic_vector = lambda_*topkeywords_vectors_dict_2[topic_id]+(1-lambda_)*relevantdocuments_vectors_dict_2[topic_id]
        final_topic_vectors_dict_2[topic_id] = final_topic_vector
    

    #replace the values only when it is necessary
    
    #lets calculate the topic similarity matrix for this omega (lambda_)
    topic_similarity_matrix = []
    for i in range(num_topics_1):
        row = []
        for j in range(num_topics_2):
            topic_i = final_topic_vectors_dict_1[i].reshape(1,-1)
            topic_j = final_topic_vectors_dict_2[j].reshape(1,-1)
            row.append(float(cosine_similarity(topic_i,topic_j)))
        topic_similarity_matrix.append(row)
    topic_similarity_matrix= np.asarray(topic_similarity_matrix)

    return topic_similarity_matrix


#this function only recalculate the similarity between the new merged topic and the others
def get_dict_topic_similarity_matrix_by_topic_ids(old_topic_similarity_matrix, id_topic1, id_topic2, wordembedding, lda_model_1,relevantDocumentsDict_1,lda_model_2,relevantDocumentsDict_2, topn_terms, PreparedData_dict_with_more_info_1, PreparedData_dict_with_more_info_2, topkdocuments, relevance_lambda, tinfo_collection_1, tinfo_collection_2, topkeywords_vectors_dict_1,topkeywords_vectors_dict_2,  relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_2):    
    relevantDocumentsDict_1.columns = relevantDocumentsDict_1.columns.map(str)
    relevantDocumentsDict_2.columns = relevantDocumentsDict_2.columns.map(str)

    #calculate topic similarity metric for different omega values
    
    i = 0.0
    matrices_dict = dict()
    print("Calculating for different omegas")
    while i <=1.01:
        lambda_ = round(i*100/100,2)        
        
        matrix = get_matrix_by_lambda_by_topic_ids(old_topic_similarity_matrix, id_topic1, id_topic2, wordembedding, lda_model_1, relevantDocumentsDict_1, lda_model_2, relevantDocumentsDict_2,topn_terms, lambda_,  tinfo_collection_1, tinfo_collection_2, topkdocuments, relevance_lambda, topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1 , topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_2 )    
        matrices_dict[lambda_] = matrix
        i+=0.01
    return matrices_dict



def get_dict_topic_similarity_matrix(wordembedding, lda_model_1,relevantDocumentsDict_1,lda_model_2,relevantDocumentsDict_2, topn_terms, PreparedData_dict_with_more_info_1, PreparedData_dict_with_more_info_2, topkdocuments, relevance_lambda, tinfo_collection_1, tinfo_collection_2, topkeywords_vectors_dict_1,topkeywords_vectors_dict_2,  relevantdocuments_vectors_dict_1, relevantdocuments_vectors_dict_2):    
    relevantDocumentsDict_1.columns = relevantDocumentsDict_1.columns.map(str)
    relevantDocumentsDict_2.columns = relevantDocumentsDict_2.columns.map(str)

    #calculate topic similarity metric for different omega values
    
    i = 0.0
    matrices_dict = dict()
    print("Calculating for different omegas")
    while i <=1.01:
        lambda_ = round(i*100/100,2)        
        
        matrix = get_matrix_by_lambda(wordembedding, lda_model_1, relevantDocumentsDict_1, lda_model_2, relevantDocumentsDict_2,topn_terms, lambda_,  tinfo_collection_1, tinfo_collection_2, topkdocuments, relevance_lambda, topkeywords_vectors_dict_1, relevantdocuments_vectors_dict_1 , topkeywords_vectors_dict_2, relevantdocuments_vectors_dict_2 )    
        matrices_dict[lambda_] = matrix
        i+=0.01
    return matrices_dict

