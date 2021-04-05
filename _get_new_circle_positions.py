

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
import json as js


def get_circle_positions(topic_similarity_matrix):
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


def get_circle_positions_from_old_matrix(old_circle_positions, topic_similarity_matrix):
    data_keys = list(old_circle_positions.keys())
    
    #get new positions from new matrix
    new_circle_positions = dict()
    for lambda_ in range(0, 101):
        lambda_ = lambda_/100
        matrix_cosine_distance = 1-topic_similarity_matrix[lambda_]
        np.fill_diagonal(matrix_cosine_distance,0)
        new_circle_positions[str(lambda_)]=_pcoa(matrix_cosine_distance, n_components=2).tolist()   
        
        
    #Apply procrusteres. Compare old positions with new positions
    standardized_matrix = dict()
    disparity_values = dict()
    
    for i in range(len(data_keys)):
    
        current_omega = data_keys[i]    
        original_a  = np.array(old_circle_positions[current_omega])
        original_b = np.array(new_circle_positions[current_omega])
        mtx1, mtx2, disparity = procrustes(original_a, original_b)
        disparity_values[current_omega] = disparity
        standardized_matrix[current_omega] = mtx2.tolist()
      
    
    new_circle_positions = standardized_matrix
    new_circle_positions= json.dumps(new_circle_positions)
    return new_circle_positions

