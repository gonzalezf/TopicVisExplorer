import gensim, pickle, random
import gensim_helpers 
from gensim.corpora import Dictionary
import numpy as np

def merge_topics(topic_index_1, topic_index_2):  #Se debe añadir el parametro data_dict de alguna forma, para que no tengamos que cargarlo a cada rato
    #return a new data_dict, this is the input for prepare(**data_dict)
    print("COMENZO A HACER EL MERGE")
    LdaModel = gensim.models.ldamodel.LdaModel
    lda_model = LdaModel.load("../data/cambridge_analytica/collection_I/collection_1_gensim.model")
    ##Load corpus
    with open('../data/cambridge_analytica/collection_I/collection_1_corpus.pkl', 'rb') as f:
        corpus = pickle.load(f)

    ##Load id2word
    id2word = Dictionary.load("../data/cambridge_analytica/collection_I/collection_1_id2word")

    data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa')   #retorna un dict de preparedData

    #create a ne topic_term_dists
    #the first column of the merge is going to be equal to =first_column_merge+second_column_merge (point wise)
    data_dict['topic_term_dists'][topic_index_1] = np.add(data_dict['topic_term_dists'][topic_index_1],data_dict['topic_term_dists'][topic_index_2])
    data_dict['topic_term_dists'] =  np.delete(data_dict['topic_term_dists'], topic_index_2, 0) #borramos la segunda columna con la que hicimos el merge
    #we must delete all the references to the topic_index_2 (it doesn't exist anymore)
    
    #create a new doc_topic_dists:
    data_dict['doc_topic_dists'][:,topic_index_1] = data_dict['doc_topic_dists'][:,topic_index_1]+data_dict['doc_topic_dists'][:,topic_index_2]
    data_dict['doc_topic_dists'] = np.delete(data_dict['doc_topic_dists'], topic_index_2, 1)
    

    #things that keep the the same
    print("TERMINO DE HACER EL MERGE!!!", data_dict)
    return data_dict