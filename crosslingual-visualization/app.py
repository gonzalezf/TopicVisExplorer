# app.py
from flask import Flask, render_template,json           # import libraries
app = Flask(__name__)             # create an app instance

@app.route("/")                   # at the end point /
def crosslingual():
    lista = [20,40,60]
    print("holaa",lista)
    
    my_list_json = json.dumps(lista)
    return render_template("index.html", data = my_list_json)
        



if __name__ == "__main__":        # on running python app.py
    app.run(debug=True)                     # run the flask app