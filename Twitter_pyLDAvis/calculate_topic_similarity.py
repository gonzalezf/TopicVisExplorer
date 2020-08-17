import numpy as np
import gensim, pickle
import sklearn
#from sklearn.metrics.pairwise import sklearn.metrics.pairwise.cosine_similarity
#from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models.keyedvectors import KeyedVectors



#################################################

'''My own tokenizer '''
import unidecode
from string import punctuation
from string import digits
punctuation+="¡¿<>'`"
punctuation+='"'

#Remove digits and puntuaction
remove_digits = str.maketrans(digits, ' '*len(digits))#remove_digits = str.maketrans('', '', digits)
remove_punctuation = str.maketrans(punctuation, ' '*len(punctuation))#remove_punctuation = str.maketrans('', '', punctuation)
remove_hashtags_caracter = str.maketrans('#', ' '*len('#'))
#las palabras de los hashtag se mantiene, pero no el simbolo. 


def text_cleaner(tweet):
    tweet = tweet.translate(remove_digits)
    #tweet = tweet.lower() it wasn't a good idea,, we lost a lot of
    tweet = tweet.translate(remove_punctuation)
    tweet = tweet.translate(remove_hashtags_caracter)
    tweet = tweet.lower()
    tweet = unidecode.unidecode(tweet)
    #tweet = tweet.strip().split()
    #filtered_words = [word for word in tweet if word not in stopWords]
    #corpus[id_tweet]= filtered_words
    #id_tweet+=1
    tweet = tweet.split()
    return tweet

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

def getDocumentVector(text, wordembedding):
    #preprocesar    
    #encontrar palabras en word embedding
    #ponderas palabras TF-IDF
    document_vector = 0.0
    words_found = 0.0
    for word in text_cleaner(text):
        if word in wordembedding:
            document_vector+=wordembedding.wv[word] #aqui hay que ponderar
            words_found+=1
    return document_vector/words_found

        
    
def get_topkeywords_relevantdocuments_vectors(wordembedding, lda_model,most_relevant_documents,  n_terms): #n_terms : numero de top keywords a considerar
    topKeywordsDict, relevantDocumentsDict = get_dicts_relevant_keywords_documents(lda_model, most_relevant_documents, n_terms)

    ### Create top keyword vector per topic
    #create keyword vector
    topkeywords_vectors_dict = {}
    num_topics = lda_model.num_topics
    for topic_id in range(num_topics):
        topkeywords_vector = 0
        ranking = 1.0
        for item in topKeywordsDict[topic_id]:
            if item['term'] in wordembedding: #no todas las palabras aparecerán en el ranking, que hacer con el resto
                #print(item['term'], item['probability'])
                topkeywords_vector += wordembedding.wv[item['term']]/ranking
            else:
                print(item['term']," position:",ranking)
            ranking+=1
        topkeywords_vectors_dict[topic_id] = topkeywords_vector
        
    relevantdocuments_vectors_dict = {}
    for topic_id in range(num_topics):
        relevantDocumentsvector = 0.0
        for item in relevantDocumentsDict[topic_id]:
            #quizas esto hacerlo para los primero 100 docs, 500 docs, el resto es un % pequeño que se pierde, optimizar
            #revisar si multiplicar por la contribucion es lo correcto, eso no da 1 o si? OHHHHHH, habria que sacar todooos los docs no solo los 100 primeros
            relevantDocumentsvector+= float(item['topic_perc_contrib'])*getDocumentVector(item['text'], wordembedding)
        relevantdocuments_vectors_dict[topic_id] = relevantDocumentsvector
        
    return (topkeywords_vectors_dict, relevantdocuments_vectors_dict)


def get_topic_vectors(wordembedding, lda_model,most_relevant_documents,  n_terms, lambda_):
    num_topics = lda_model.num_topics
    topkeywords_vectors_dict, relevantdocuments_vectors_dict = get_topkeywords_relevantdocuments_vectors(wordembedding, lda_model,most_relevant_documents,  n_terms)
    final_topic_vectors_dict = dict()
    for topic_id in range(num_topics):
        final_topic_vector = lambda_*topkeywords_vectors_dict[topic_id]+(1-lambda_)*relevantdocuments_vectors_dict[topic_id]
        final_topic_vectors_dict[topic_id] = final_topic_vector
    return final_topic_vectors_dict

def get_matrix(wordembedding, lda_model_1,most_relevant_documents_1,lda_model_2,most_relevant_documents_2, n_terms, lambda_):
    
    final_topic_vectors_dict_1 =  get_topic_vectors(wordembedding, lda_model_1,most_relevant_documents_1,  n_terms, lambda_)
    final_topic_vectors_dict_2 =  get_topic_vectors(wordembedding, lda_model_2,most_relevant_documents_2,  n_terms, lambda_)
    
    topic_similarity_matrix = []
    for i in range(lda_model_1.num_topics):
        row = []
        for j in range(lda_model_2.num_topics):
            topic_i = final_topic_vectors_dict_1[i].reshape(1,-1)
            topic_j = final_topic_vectors_dict_2[j].reshape(1,-1)
            row.append(float(cosine_similarity(topic_i,topic_j)))
        topic_similarity_matrix.append(row)
    topic_similarity_matrix= np.asarray(topic_similarity_matrix)
    return topic_similarity_matrix


##############Calculate topic similarity

def getTopicSimilarityMetric(topn, wordembedding, lda_model_collecion_1, most_relevant_documents_collection_1, lda_model_collecion_2, most_relevant_documents_collection_2):
    #topn = 30
    #lambda_ = 0.8
    i = 0.0
    matrices_dict = dict()
    while i <=1.01:
        lambda_ = round(i,2)
        print(lambda_)
        matrix = get_matrix(wordembedding, lda_model_collecion_1, most_relevant_documents_collection_1, lda_model_collecion_2, most_relevant_documents_collection_2,topn, lambda_)
        matrices_dict[lambda_] = matrix
        i+=0.01
    return matrices_dict  #la matriz devuelve la matriz de distancia segun distintos lambda_ en la metrica de similitud  de topicos