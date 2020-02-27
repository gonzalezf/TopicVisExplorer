from flask import Flask, render_template, request, json
import random, threading, webbrowser

class TopicExplorer():
    
    def __init__(self, model, tweets, lista):
        self.model = model
        self.tweets = tweets
        self.lista = lista
        self.app = Flask(__name__)
        
    def launch(self):
