#/////////////////////////////Parameters////////////////////////////
# NLTK Stop words
from nltk.corpus import stopwords
stop_words = stopwords.words('english')
stop_words.extend(['usernameremoved', 'link', 'remove', 'usernameremove', 'amp', 'linkremoved',' <link removed>','usernameremoved','<usernameremoved>','<linkremoved>','usernameremoved_usernameremoved','linkremoved_linkremoved'])

name_column_text = 'texto_completo'
name_tokenizacion = 'text_cleaner'
#/////////////////////////////Parameters////////////////////////////




import json
import importlib
import topicvisexplorer
import pandas as pd
import warnings
from scipy import spatial

import sys
# !{sys.executable} -m spacy download en
import re, numpy as np, pandas as pd
from pprint import pprint

# Gensim
import gensim, spacy, logging, warnings
import gensim.corpora as corpora
from gensim.utils import lemmatize, simple_preprocess
from gensim.models import CoherenceModel
import matplotlib.pyplot as plt
from gensim.models import LdaMulticore

import unidecode
import _prepare
import _prepare_single_topic
import gensim_helpers
import spacy
import re, numpy as np, pandas as pd

#libraries to tokenize text
from string import punctuation
from string import digits
from nltk.tokenize import TweetTokenizer
from sklearn.metrics.pairwise import cosine_similarity
import time
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)





#this should be easy to change for users
punctuation+="¡¿<>'`"
punctuation+='"'
nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])    

#Remove digits and puntuaction
remove_digits = str.maketrans(digits, ' '*len(digits))#remove_digits = str.maketrans('', '', digits)
remove_punctuation = str.maketrans(punctuation, ' '*len(punctuation))#remove_punctuation = str.maketrans('', '', punctuation)
remove_hashtags_caracter = str.maketrans('#', ' '*len('#'))
#las palabras de los hashtag se mantiene, pero no el simbolo. 

tknzr = TweetTokenizer()


def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]


#this should be easy to change for users
punctuation+="¡¿<>'`"
punctuation+='"'
nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])    

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


def getDocumentVector(text, wordembedding ,  list_terms_relevance):   

    document_vector = np.array([0.0]*300)# 300 dimensions
    
    for word in text:  
        #print('esta es una word', word)
        if word in list_terms_relevance:
            raking_word = float(list_terms_relevance.index(word)+1)
            if word in wordembedding: #if word in wordembedding.wv:
                #print("WORD FOUND", word, raking_word)
                document_vector+=wordembedding[word]/raking_word #aqui hay que ponderar
            else:
                pass
                #print("WARNING, Word not found:", word)    

    return document_vector
            

def get_initial_document_vector_by_class(list_terms_relevance, topic_id, name_tokenizacion,documents_class_A, documents_class_B, wordembedding):
    relevantDocumentsvector_class_A = 0.0
    list_documents_A = []
    for row in documents_class_A:
        current_text = row[name_tokenizacion]
        current_contribution = row[str(int(topic_id) -1)]
        current_document_vector = getDocumentVector(current_text, wordembedding,  list_terms_relevance)    
        relevantDocumentsvector_class_A+= current_contribution*current_document_vector
        list_documents_A.append((current_contribution, current_text))
    
    relevantDocumentsvector_class_B= 0.0
    list_documents_B = []
    for row in documents_class_B:
        current_text = row[name_tokenizacion]
        current_contribution = row[str(int(topic_id) -1)]
        current_document_vector = getDocumentVector(current_text, wordembedding,  list_terms_relevance)    
        relevantDocumentsvector_class_B+= current_contribution*current_document_vector
        list_documents_B.append((current_contribution, current_text))

    return(relevantDocumentsvector_class_A, relevantDocumentsvector_class_B, list_documents_A, list_documents_B)



def create_two_list_of_documents(list_terms_relevance, list_relevant_documents, topic_id, name_tokenizacion,name_column_text, new_document_seeds_TopicA, new_document_seeds_TopicB, wordembedding):
    vector_A, vector_B, seeds_documents_A, seeds_documents_B = get_initial_document_vector_by_class(list_terms_relevance, topic_id, name_tokenizacion,new_document_seeds_TopicA, new_document_seeds_TopicB, wordembedding)

    vector_A = vector_A.reshape(-1, 1)
    vector_B = vector_B.reshape(-1, 1)
    documents_A = []
    documents_B = []
    most_relevant_documents_topic = set()

    list_relevant_documents = pd.DataFrame(list_relevant_documents).sort_values(int(topic_id)-1, ascending=False).reset_index()
    #print('vectores crreadoos', vector_A, vector_B)
    for index, row in list_relevant_documents.head(100).iterrows():
        if index%100 == 0:
            print(index)
        current_contribution = row[int(topic_id)-1]
        current_text = row[name_tokenizacion]
        current_document_vector = getDocumentVector(current_text, wordembedding, list_terms_relevance).reshape(-1, 1)
        similarity_vectorA_currentvector =  1 - spatial.distance.cosine(vector_A, current_document_vector)
        similarity_vectorB_currentvector =  1 - spatial.distance.cosine(vector_B, current_document_vector)
        
        #I need this information to get the matrix of most relevant documents according to the similarity score
        most_relevant_documents_topic.add((similarity_vectorA_currentvector,similarity_vectorB_currentvector,  current_contribution, row[name_column_text]))
            
        if similarity_vectorA_currentvector>= similarity_vectorB_currentvector:
            #append element to documentsA
            documents_A.append((current_contribution, row[name_tokenizacion]))
        else:
            documents_B.append((current_contribution, row[name_tokenizacion]))
    print('Documentos en A', len(documents_A))
    print('Documentos en B', len(documents_B))

    #In the set of most relevant documents, we also need to calculate the similarity between the topic vector and the documents as seeds
    for row in new_document_seeds_TopicA:
        current_contribution = row[str(int(topic_id)-1)]
        current_text = row[name_tokenizacion]
        #print('agregando este texto', current_text)
        current_document_vector = getDocumentVector(current_text, wordembedding, list_terms_relevance).reshape(-1, 1)
        similarity_vectorA_currentvector =  1 - spatial.distance.cosine(vector_A, current_document_vector)
        similarity_vectorB_currentvector =  1 - spatial.distance.cosine(vector_B, current_document_vector)
        
        most_relevant_documents_topic.add((similarity_vectorA_currentvector, similarity_vectorB_currentvector, current_contribution, row[name_column_text]))
    
    for row in new_document_seeds_TopicB:
        current_contribution = row[str(int(topic_id)-1)]
        current_text = row[name_tokenizacion]
        #print('agregando este texto', current_text)
        current_document_vector = getDocumentVector(current_text, wordembedding, list_terms_relevance).reshape(-1, 1)
        similarity_vectorA_currentvector =  1 - spatial.distance.cosine(vector_A, current_document_vector)
        similarity_vectorB_currentvector =  1 - spatial.distance.cosine(vector_B, current_document_vector)
        
        most_relevant_documents_topic.add((similarity_vectorA_currentvector, similarity_vectorB_currentvector, current_contribution, row[name_column_text]))
    
                
    
    return (seeds_documents_A, seeds_documents_B, documents_A, documents_B, most_relevant_documents_topic)

        
    def getLdaModelfromSentences(sentences):
        print('lda started')
        #data_words = list(sent_to_words(sentences))
        #data_ready = process_words(sentences)  # processed Text Data!
        # Create Dictionary
        id2word = corpora.Dictionary(sentences)

        # Create Corpus: Term Document Frequency
        corpus = [id2word.doc2bow(text) for text in sentences]
        # Build LDA model
        print('building model')
        lda_model = LdaMulticore(corpus=corpus,
                                id2word=id2word,
                                num_topics=1, 
                                random_state=100,
                                chunksize=10,
                                passes=10,
                                alpha='symmetric',
                                iterations=100,
                                per_word_topics=True)
        print('termine de calcular el modelo')
    return (lda_model, corpus, id2word)


def getCorpusDictionaryfromSentences(sentences):
    print('lda started')
    #data_words = list(sent_to_words(sentences))
    #data_ready = process_words(sentences)  # processed Text Data!
    # Create Dictionary
    id2word = corpora.Dictionary(sentences)

    # Create Corpus: Term Document Frequency
    corpus = [id2word.doc2bow(text) for text in sentences]
    # Build LDA model
    print('sendind corpus and dictionary')
    return (corpus, id2word)


def get_new_subtopics(list_terms_relevance, list_relevant_documents, topic_id, name_tokenizacion,name_column_text, new_document_seeds_TopicA, new_document_seeds_TopicB, wordembedding):
    final_list_A = []
    final_list_B = []

    seeds_documents_A, seeds_documents_B, documents_A, documents_B, most_relevant_documents_topic = create_two_list_of_documents(list_terms_relevance, list_relevant_documents, topic_id, name_tokenizacion,name_column_text, new_document_seeds_TopicA, new_document_seeds_TopicB, wordembedding)
    print('seeds documents a', len(seeds_documents_A))
    print('seeds documents b', len(seeds_documents_B))
    print('seeds documents a', len(documents_A))
    print('seeds documents a', len(documents_B))
    
    for contribution, text in seeds_documents_A:
        final_list_A.extend([text]*int(contribution*100))
    for contribution, text in seeds_documents_B:
        final_list_B.extend([text]*int(contribution*100))

    for contribution, text in documents_A:
        final_list_A.extend([text]*int(contribution*100))
    for contribution, text in documents_B:
        final_list_B.extend([text]*int(contribution*100))
    
    freq_topic_A = len(final_list_A)/(len(final_list_A)+len(final_list_B))
    freq_topic_B = len(final_list_B)/(len(final_list_A)+len(final_list_B))
    
    return(getCorpusDictionaryfromSentences(final_list_A), getCorpusDictionaryfromSentences(final_list_B), most_relevant_documents_topic, freq_topic_A, freq_topic_B)

def extract_data_without_topic_model(corpus, dictionary):


    topic_model = None
    if not gensim.matutils.ismatrix(corpus):
        corpus_csc = gensim.matutils.corpus2csc(corpus, num_terms=len(dictionary))
    else:
        corpus_csc = corpus
        # Need corpus to be a streaming gensim list corpus for len and inference functions below:
        corpus = gensim.matutils.Sparse2Corpus(corpus_csc)

    vocab = list(dictionary.token2id.keys())
    
    beta = 0.01
    fnames_argsort = np.asarray(list(dictionary.token2id.values()), dtype=np.int_)
    term_freqs = corpus_csc.sum(axis=1).A.ravel()[fnames_argsort]
    term_freqs[term_freqs == 0] = beta

    assert term_freqs.shape[0] == len(dictionary),\
        'Term frequencies and dictionary have different shape {} != {}'.format(
        term_freqs.shape[0], len(dictionary))



    topic_term_dists = term_freqs/term_freqs.sum(axis=0) # esta bien esto! 
    return {'topic_term_dists': topic_term_dists, 'vocab': vocab, 'term_frequency': term_freqs}


def change_frequency_on_prepared_data(row, new_subtopic_df):
    current_term = row['Term']
    if current_term in list(new_subtopic_df['vocab']):
        new_subtopic_df = pd.DataFrame(new_subtopic_df)
        old_freq = row['Freq']
        new_prob = float(new_subtopic_df.loc[new_subtopic_df['vocab'] == current_term]['topic_term_dists'])
        current_total = row['Total']
        row['Freq'] = new_prob*row['Total']
    else:
        row['Freq'] = 0    
    return row
    

    