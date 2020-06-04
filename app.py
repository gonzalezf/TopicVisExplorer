# app.py
import random, threading, webbrowser
import gensim, pickle, random

from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json
from prepare_utils import *
from gensim_utils import *

app = Flask(__name__)             # create an app instance

lista = [1,2,3]

######################Load data#########################
##Load Model
LdaModel = gensim.models.ldamodel.LdaModel
lda_model = LdaModel.load("data/sample/chiledesperto_sample_ldamodel")

##Load corpus
with open('data/sample/chiledesperto_corpus_ldamodel.pkl', 'rb') as f:
    corpus = pickle.load(f)

##Load id2word
id2word = Dictionary.load("data/sample/chiledesperto_id2word_ldamodel")



##Load relevant documents
import pickle

#relevant documents were already calculated
with open('data/sample/sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
    sent_topics_sorteddf_mallet = pickle.load(f)

sent_topics_sorteddf_mallet = sent_topics_sorteddf_mallet[['Topic_Num','Topic_Perc_Contrib','text']]

test_text = 'Lorem Ipsum es simplemente el texto de relleno de las imprentas y archivos de texto. Lorem Ipsum ha sido el texto de relleno estándar de las industrias desde el año 1500, cuando un impresor (N. del T. persona que se dedica a la imprenta) desconocido usó una galería de textos y los mezcló de tal manera que logró hacer un libro de textos especimen. No sólo sobrevivió 500 años, sino que tambien ingresó como texto de relleno en documentos electrónicos, quedando esencialmente igual al original. Fue popularizado en los 60s con la creación de las hojas "Letraset", las cuales contenian pasajes de Lorem Ipsum, y más recientemente con software de autoedición, como por ejemplo Aldus PageMaker, el cual incluye versiones de Lorem Ipsum.'


#prepared data for visualization
'''#Uncomment these lineas in production

#convert LDAMALLET to LDAModel gensim
lda_model = gensim.models.wrappers.ldamallet.malletmodel2ldamodel(lda_model)
model = extract_data(lda_model, corpus, id2word)
PreparedDataObtained= prepare(model['topic_term_dists'],model['doc_topic_dists'],model['doc_lengths'],model['vocab'],model['term_frequency'])



with open('data/sample/chiledesperto_prepared_data', 'wb') as f:
    pickle.dump(PreparedDataObtained, f)
'''

with open('data/sample/chiledesperto_prepared_data', 'rb') as f:
    PreparedDataObtained = pickle.load(f)


PreparedData_dict= PreparedDataObtained.to_dict()



#########################Visualizations###################
@app.route("/")                   
def crosslingual():
    num_topics = lda_model.num_topics
    print("numero de topicos es, ", num_topics)
    #lista.append(lda_model.num_topics)
    #my_list_json = json.dumps(lista)

    
    #create json file
    jsonCircles = {}
    jsonCircles['circles'] = []

    #x axis between [0,500]
    #y axis between[0,500]
    for i in range(num_topics):
        jsonCircles['circles'].append({
            "x_axis": random.randint(50,451),
            "y_axis": random.randint(50,451),
            "radius": random.randint(10,30),
            "color" : "skyblue",
            'fill_opacity':"0.6",
            "index":i,
            "bordercolor":'black',
            "label":str(i)

            
        })    
    
    topKeywordsDict = {}
    for topic_id in range(num_topics):
        topKeywordsDict[topic_id] = []
        for term, probability in lda_model.show_topic(topic_id,topn=10):
            topKeywordsDict[topic_id].append({
                "term":term,
                "probability":probability
            })
    
    relevantDocumentsDict = {}
    for index,row in sent_topics_sorteddf_mallet.iterrows():
        topic_id = int(row['Topic_Num'])
        if topic_id not in relevantDocumentsDict:
            relevantDocumentsDict[topic_id]=[]
        relevantDocumentsDict[topic_id].append({
            'topic_perc_contrib':row['Topic_Perc_Contrib'],
            'text':row['text']
        })
    #print(int(row['Topic_Num']), row['Topic_Perc_Contrib'],row['text'])
    #print(type(json.dumps(relevantDocumentsDict)))            
    #print(json.dumps(relevantDocumentsDict))
    
    return render_template("index.html", num_topics = num_topics, jsonCircles=jsonCircles, topKeywordsDict = topKeywordsDict, relevantDocumentsDict = relevantDocumentsDict, PreparedData_dict = PreparedData_dict) #data = my_list_json
        



    
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
    app.run(port=port, debug=True)



#############
launch()