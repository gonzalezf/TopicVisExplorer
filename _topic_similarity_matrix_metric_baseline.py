#word embedding topic similarity metric
#metrica correcta
import numpy as np 
def distance_topic_i_j(terms_list_i,terms_list_j, wordembedding):
    total_distances_topic_i = 0.0
    not_found_terms = set()
    for term_i in terms_list_i:
        if term_i in wordembedding:
            dist_for_term_i = []
            for term_j in terms_list_j:
                if term_j in wordembedding:                    
                    dist_for_term_i.append(wordembedding.wv.distance(term_i,term_j))
                    #print(term_i,term_j)
                    #dist_for_term_i.append(wordembedding.similarity(term_i,term_j))
                else:
                    #print("Not found, j", term_j)
                    not_found_terms.add(term_j)
            total_distances_topic_i+=min(dist_for_term_i)
        else:
            #print("Not found, i:",term_i)
            not_found_terms.add(term_i)
    #print("total distance",total_distances_topic_i )
    if len(not_found_terms)>0:
        print("Not found", not_found_terms)
    return total_distances_topic_i


def generar_matrix_baseline_metric(word_embedding_model, prepared_data_topic_1, prepared_data_topic_2, relevance_score = 0.6, topn=20):
    matrix = []
    i=0
    list_prepared_data_1 = [prepared_data_topic_1]
    list_prepared_data_2 = [prepared_data_topic_2]
    for topic_model_i in list_prepared_data_1:
        new_order_topics_i =  prepared_data_topic_1.topic_order
        for topic_id_i in new_order_topics_i:
            row=[]
            terms_list_i = topic_model_i.sorted_terms(topic=topic_id_i,_lambda=relevance_score)['Term'][:topn]
            #print("topic id",topic_id_i)
            #print(terms_list_i)
            #print("==============")
            for topic_model_j in list_prepared_data_2:
                new_order_topics_j = prepared_data_topic_2.topic_order
                for topic_id_j in new_order_topics_j:
                    #print("topic id j",topic_id_j)
                    terms_list_j = topic_model_j.sorted_terms(topic=topic_id_j,_lambda=relevance_score)['Term'][:topn]
                    #print(terms_list_j)
                    #print(distance_topic_i_j(terms_list_i,terms_list_j))
                    row.append(distance_topic_i_j(terms_list_i,terms_list_j, word_embedding_model))
                    #print(topic_id_i,topic_id_j)
            matrix.append(row)
        i+=1
    matrix = np.asarray(matrix)
    
    return matrix