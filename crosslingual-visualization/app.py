# app.py
import random, threading, webbrowser
import gensim, pickle, random
from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json






app = Flask(__name__)             # create an app instance

lista = [1,2,3]

######################Load data#########################
##Load Model
LdaModel = gensim.models.ldamodel.LdaModel
lda_model = LdaModel.load("data/tutorial_ldamodel")

##Load corpus
with open('data/tutorial_corpus.pkl', 'rb') as f:
    corpus = pickle.load(f)

##Load id2word
id2word = Dictionary.load("data/tutorial_id2word")



#########################Visualizations###################
@app.route("/")                   
def crosslingual():
    num_topics = lda_model.num_topics
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
            "label":"prueba"

            
        })    
    


    return render_template("index.html", num_topics = num_topics, jsonCircles=jsonCircles) #data = my_list_json
        



    
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