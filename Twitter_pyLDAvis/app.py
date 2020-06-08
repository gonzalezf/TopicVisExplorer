# -*- coding: utf-8 -*-

import random, threading, webbrowser
import gensim, pickle, random
import gensim_helpers 
from gensim.corpora import Dictionary
from flask import Flask, render_template, request, json
from _display import *
from _prepare import prepare, js_PCoA, PreparedData
from flask import render_template_string
from os import path, walk


"""
Topic Models (e.g. LDA) visualization using D3
=============================================

Functions: General Use
----------------------
:func:`prepare`
    transform and prepare a LDA model's data for visualization

:func:`prepared_data_to_html`
    convert prepared data to an html string

:func:`show`
    launch a web server to view the visualization

:func:`save_html`
    save a visualization to a standalone html file

:func:`save_json`
    save the visualization JSON data of to a file


Functions: IPython Notebook
---------------------------
:func:`display`
    display a figure in an IPython notebook

:func:`enable_notebook`
    enable automatic D3 display of prepared model data in the IPython notebook.

:func:`disable_notebook`
    disable automatic D3 display of prepared model data in the IPython notebook.
"""

__all__ = ["__version__",
           "prepare", "js_PCoA",
           "PreparedData", "prepared_data_to_html",
           "display", "show", "save_html", "save_json",
           "enable_notebook", "disable_notebook"]

__version__ = 'git_1.0.0'



app = Flask(__name__)             
app.config['TEMPLATES_AUTO_RELOAD'] = True

extra_dirs = ['templates',] #directory to watch for any changes
extra_files = extra_dirs[:]
for extra_dir in extra_dirs:
    for dirname, dirs, files in walk(extra_dir):
        for filename in files:
            filename = path.join(dirname, filename)
            if path.isfile(filename):
                extra_files.append(filename)

print("Extra files to watch", extra_files)

######################Import data #########################

##Load Gensim Model
LdaModel = gensim.models.ldamodel.LdaModel
lda_model = LdaModel.load("data/cambridge_analytica/sample/collection_1_sample_gensim.model")

##Load corpus
with open('data/cambridge_analytica/sample/collection_1_sample_corpus.pkl', 'rb') as f:
    corpus = pickle.load(f)

##Load id2word
id2word = Dictionary.load("data/cambridge_analytica/sample/collection_1_sample_id2word")

##Load relevant documents
#relevant documents were already calculated
with open('data/cambridge_analytica/sample/collection_1_sample_sent_topics_sorteddf_mallet_ldamodel', 'rb') as f:
    sent_topics_sorteddf_mallet = pickle.load(f)
sent_topics_sorteddf_mallet = sent_topics_sorteddf_mallet[['Topic_Num','Topic_Perc_Contrib','text']]

relevantDocumentsDict = {}
for index,row in sent_topics_sorteddf_mallet.iterrows():
    topic_id = int(row['Topic_Num'])
    if topic_id not in relevantDocumentsDict:
        relevantDocumentsDict[topic_id]=[]
    relevantDocumentsDict[topic_id].append({
        'topic_perc_contrib':row['Topic_Perc_Contrib'],
        'text':row['text']
    })


#prepare data for first time'''
'''
data_dict = gensim_helpers.prepare(lda_model, corpus,id2word, mds='pcoa')   #retorna un dict de preparedData

PreparedDataObtained = prepare(**data_dict)

with open('data/cambridge_analytica/sample/collection_1_sample_prepared_data', 'wb') as f:
    pickle.dump(PreparedDataObtained, f)
'''

#load prepared data

with open('data/cambridge_analytica/sample/collection_1_sample_prepared_data', 'rb') as f:
    PreparedDataObtained = pickle.load(f)


PreparedData_dict= PreparedDataObtained.to_dict()
print(PreparedData_dict.keys())
topic_order = PreparedData_dict['topic.order']
    

#show(PreparedDataObtained)
#html = prepared_data_to_html(PreparedDataObtained)
html = prepared_html_in_flask(PreparedDataObtained, relevantDocumentsDict, topic_order)


@app.route("/")                   
def crosslingual():
    #show(PreparedDataObtained,local=False)
    #return render_template("index.html") 
    return render_template_string(html)

        
    
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
    app.run(port=port, debug=True, extra_files=extra_files)
    



#############
launch()