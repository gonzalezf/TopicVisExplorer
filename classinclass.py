from flask import Flask
from flask_classful import FlaskView, route

__datadict = {}

class TopicVisExplorer:

    app = None
    
    def __init__(self, name):        
        self.app = Flask(name)
        TestView.register(self.app, route_base = '/')
        datadict["title"] = "hola"
    
    def run(self):
        
        self.app.run(debug=False)


class TestView(FlaskView):

    @route('/')
    def index(self):
    # http://localhost:5000/
        return f"<h1>{datadict['title']}</h1>"




    