# this file is largely based on https://github.com/jakevdp/mpld3/blob/master/mpld3/_display.py
# Copyright (c) 2013, Jake Vanderplas
# It was adapted for pyLDAvis by Ben Mabey
import warnings
import random
import json 
import jinja2
import re
import urls
from _server import serve
from utils import get_id, write_ipynb_local_js, NumPyEncoder
from _prepare import PreparedData
from jinja2 import Template
from flask import render_template
import random
from jinja2 import Template, escape
from flask import Markup
from flask import json as json_flask
__all__ = ["prepared_data_to_html", "display",
           "show", "save_html", "save_json",
           "enable_notebook", "disable_notebook","prepared_html_in_flask"]


# Simple HTML template. This works in standalone web pages for single visualizations,
# but will not work within the IPython notebook due to the presence of
# requirejs
SIMPLE_HTML = jinja2.Template("""
<script type="text/javascript" src="{{ d3_url }}"></script>
<script type="text/javascript" src="{{ ldavis_url }}"></script>
<link rel="stylesheet" type="text/css" href="{{ ldavis_css_url }}">

<div id={{ visid }}></div>
<script type="text/javascript">
   !function(LDAvis){
       new LDAvis("#" + {{ visid }}, {{ vis_json }});
   }(LDAvis);
</script>
""")


# RequireJS template.  If requirejs and jquery are not defined, this will
# result in an error.  This is suitable for use within the IPython notebook.
REQUIREJS_HTML = jinja2.Template("""


<link rel="stylesheet" type="text/css" href="{{ ldavis_css_url }}">





<div id={{ visid }}></div>
<script type="text/javascript">

var {{ visid_raw }}_data = {{ vis_json }};


if(typeof(window.LDAvis) !== "undefined"){
   !function(LDAvis){
       new LDAvis("#" + {{ visid }}, {{ visid_raw }}_data);
   }(LDAvis);
}else{
  require.config({paths: {d3: "{{ d3_url[:-3] }}"}});
  require(["d3"], function(d3){
    window.d3 = d3;
    $.getScript("{{ ldavis_url }}", function(){
       new LDAvis("#" + {{ visid }}, {{ visid_raw }}_data);
    });
  });
}
</script>
""")


# General HTML template.  This should work correctly whether or not requirejs
# is defined, and whether it's embedded in a notebook or in a standalone
# HTML page.
GENERAL_HTML = jinja2.Template("""
This template was replaces by templates/index.html
""")

TEMPLATE_DICT = {"simple": SIMPLE_HTML,
                 "notebook": REQUIREJS_HTML,
                 "general": GENERAL_HTML}


def prepared_data_to_html(data, topic_order,   type_vis, new_circle_positions=None,matrix_sankey=None,  data_2=None,  topic_order_2 = None, d3_url=None, ldavis_url=None, ldavis_css_url=None,
                          template_type="general", visid=None, use_http=False):

    """Output HTML with embedded visualization

    Parameters
    ----------
    data : PreparedData, created using :func:`prepare`
        The data for the visualization.
    d3_url : string (optional)
        The URL of the d3 library.  If not specified, a standard web path
        will be used.
    ldavis_url : string (optional)
        The URL of the LDAvis library.  If not specified, a standard web path
        will be used.
    template_type : string
        string specifying the type of HTML template to use. Options are:

        ``"simple"``
             suitable for a simple html page with one visualization.  Will
             fail if require.js is available on the page.
        ``"notebook"``
             assumes require.js and jquery are available.
        ``"general"``
             more complicated, but works both in and out of the
             notebook, whether or not require.js and jquery are available
    visid : string (optional)
        The html/css id of the visualization div, which must not contain spaces.
        If not specified, a random id will be generated.
    use_http : boolean (optional)
        If true, use http:// instead of https:// for d3_url and ldavis_url.

    Returns
    -------
    vis_html : string
        the HTML visualization

    See Also
    --------
    :func:`save_json`: save json representation of visualization to file
    :func:`save_html` : save html representation of a visualization to file
    :func:`show` : launch a local server and show a visualization in a browser
    :func:`display` : embed visualization within the IPython notebook
    :func:`enable_notebook` : automatically embed visualizations in IPython notebook
    """

    #template = TEMPLATE_DICT[template_type] 


    with open('templates/index.html') as file_:
        template = Template(file_.read())

    d3_url = d3_url or urls.D3_URL
    ldavis_url = ldavis_url or urls.LDAVIS_URL
    ldavis_css_url = ldavis_css_url or urls.LDAVIS_CSS_URL

    if use_http:
        d3_url = d3_url.replace('https://', 'http://')
        ldavis_url = ldavis_url.replace('https://', 'http://')

    if visid is None:
        visid = 'ldavis_' + get_id(data[0]) + str(int(random.random() * 1E10))
    elif re.search('\s', visid):
        raise ValueError("visid must not contain spaces")
    
    
    data_json_format = []
    #print("este es el formato de data",data)
    #print("este es el elemento", data)
    for elem in data:
        #elem = elem.to_json() esto lo borre
        elem = json.dumps(elem, cls=NumPyEncoder)
        data_json_format.append(elem)
    

    #transformar matrix en un diccionario
    if type_vis == 2:
        matrix_dict = {"nodes":[], "links":[]}
        print('este es el type', type(matrix_sankey))
        if(type(matrix_sankey) is dict):
            matrix_s = matrix_sankey[0.80]
            
        else:
            matrix_s = matrix_sankey

        for i in range(matrix_s.shape[0]):#matrix_s.shape[0]
            matrix_dict["nodes"].append({"node":i, "name":"model1-"+str(i)})
            for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
                    matrix_dict["links"].append({"source":i,"target":(matrix_s.shape[0]+j), "value":matrix_s[i][j]}) #matrix[i][j]
                

        for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
            matrix_dict["nodes"].append({"node":matrix_s.shape[0]+j, "name":"model2-"+str(j)})
        
        ##para cada valor posible de lambda
        if(type(matrix_sankey) is dict):
            dict_matrix_dict = dict()
            for lambda_ in range(0, 101):
                lambda_ = lambda_/100
                matrix_dict = {"nodes":[], "links":[]}
                matrix_s = matrix_sankey[lambda_]
                for i in range(matrix_s.shape[0]):#matrix_s.shape[0]
                    matrix_dict["nodes"].append({"node":i, "name":"model1-"+str(i)})
                    for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
                            matrix_dict["links"].append({"source":i,"target":(matrix_s.shape[0]+j), "value":matrix_s[i][j]}) #matrix[i][j]
                        
                for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
                    matrix_dict["nodes"].append({"node":matrix_s.shape[0]+j, "name":"model2-"+str(j)})
                dict_matrix_dict[lambda_]=matrix_dict
            dict_matrix_json = json.dumps(dict_matrix_dict)
        else:
            dict_matrix_dict = dict()
            for lambda_ in range(0, 1):
                lambda_ = 0.8#lambda_/100
                matrix_dict = {"nodes":[], "links":[]}
                matrix_s = matrix_sankey
                for i in range(matrix_s.shape[0]):#matrix_s.shape[0]
                    matrix_dict["nodes"].append({"node":i, "name":"model1-"+str(i)})
                    for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
                            matrix_dict["links"].append({"source":i,"target":(matrix_s.shape[0]+j), "value":matrix_s[i][j]}) #matrix[i][j]
                        

                for j in range(matrix_s.shape[1]): #matrix_s.shape[1]
                    matrix_dict["nodes"].append({"node":matrix_s.shape[0]+j, "name":"model2-"+str(j)})
                dict_matrix_dict[lambda_]=matrix_dict
            dict_matrix_json = json.dumps(dict_matrix_dict)
            print('final dict key', dict_matrix_dict.keys())
            

        #matrix_json = json.dumps(matrix_dict)
        


        data_json_format_2 = []
        for elem in data_2:
            #elem = elem.to_json()
            elem = json.dumps(elem, cls=NumPyEncoder)
            data_json_format_2.append(elem)

    
    else: #type_vis == 1
        
        dict_matrix_dict = dict()
        dict_matrix_json = json.dumps(dict_matrix_dict)
        data_json_format_2=[None]
    

    

    

    return template.render(visid=json.dumps(visid),
                           new_circle_positions = new_circle_positions,                            
                           topic_order = topic_order,
                           topic_order_2 = topic_order_2,#matrix_heatmap = matrix,#categories_row = categories_row,
                           visid_raw=visid,
                           d3_url=d3_url,
                           ldavis_url=ldavis_url,
                           vis_json=data_json_format[0], #data[0].to_json()
                           vis_json_2=data_json_format_2[0], #data[0].to_json()
                           ldavis_css_url=ldavis_css_url,
                           matrix_sankey=dict_matrix_json,#matrix_json, #matrix_sankey[0.0].tolist(), 
                           #matrix_sankey_2 = dict_matrix_json,
                           type_vis = type_vis#2: two topic modeling outputs, 1:one topic modeling output,                                               
                           )


def display(data, local=False, **kwargs):

    """Display visualization in IPython notebook via the HTML display hook

    Parameters
    ----------
    data : PreparedData, created using :func:`prepare`
        The data for the visualization.
    local : boolean (optional, default=False)
        if True, then copy the d3 & mpld3 libraries to a location visible to
        the notebook server, and source them from there. See Notes below.
    **kwargs :
        additional keyword arguments are passed through to :func:`prepared_data_to_html`.

    Returns
    -------
    vis_d3 : IPython.display.HTML object
        the IPython HTML rich display of the visualization.

    Notes
    -----
    Known issues: using ``local=True`` may not work correctly in certain cases:

    - In IPython < 2.0, ``local=True`` may fail if the current working
      directory is changed within the notebook (e.g. with the %cd command).
    - In IPython 2.0+, ``local=True`` may fail if a url prefix is added
      (e.g. by setting NotebookApp.base_url).

    See Also
    --------
    :func:`show` : launch a local server and show a visualization in a browser
    :func:`enable_notebook` : automatically embed visualizations in IPython notebook
    """
    # import here, in case users don't have requirements installed
    from IPython.display import HTML

    if local:
        if 'ldavis_url' in kwargs or 'd3_url' in kwargs:
            warnings.warn(
                "display: specified urls are ignored when local=True")
        kwargs['d3_url'], kwargs['ldavis_url'], kwargs['ldavis_css_url'] = write_ipynb_local_js()

    return HTML(prepared_data_to_html(data, **kwargs))

def prepared_html_in_flask(data, topic_order,type_vis,new_circle_positions = None, matrix_sankey=None, data_2 = None, topic_order_2 = None, **kwargs):
    #kwargs['ldavis_url'] = '/LDAvis.js'
    #kwargs['d3_url'] = '/d3.js'
    #kwargs['ldavis_css_url'] = '/LDAvis.css'
    
    #uncomment these lines on debugging testing
    kwargs['ldavis_url'] = '/static/js/LDAvis.js'
    kwargs['d3_url'] = 'static/js/d3.v5.min.js'
    kwargs['ldavis_css_url'] = 'static/css/LDAvis.css'
    
    #uncomment when it is necessary to upload to heroku
    #kwargs['ldavis_url'] = 'https://topicvisexplorer.herokuapp.com/static/js/ldavis.js'
    #kwargs['d3_url'] = 'https://topicvisexplorer.herokuapp.com/static/js/d3.v5.min.js'
    #kwargs['ldavis_css_url'] = 'https://topicvisexplorer.herokuapp.com/static/css/ldavis.css'

    html = prepared_data_to_html(data = data, topic_order = topic_order,type_vis = type_vis,new_circle_positions= new_circle_positions,  matrix_sankey = matrix_sankey, data_2 =  data_2,  topic_order_2 = topic_order_2,  **kwargs)
    
    return html
    


def show(data, ip='127.0.0.1', port=8888, n_retries=50,
         local=True, open_browser=True, http_server=None, **kwargs):
    """Starts a local webserver and opens the visualization in a browser.

    Parameters
    ----------
    data : PreparedData, created using :func:`prepare`
        The data for the visualization.
    ip : string, default = '127.0.0.1'
        the ip address used for the local server
    port : int, default = 8888
        the port number to use for the local server.  If already in use,
        a nearby open port will be found (see n_retries)
    n_retries : int, default = 50
        the maximum number of ports to try when locating an empty port.
    local : bool, default = True
        if True, use the local d3 & LDAvis javascript versions, within the
        js/ folder.  If False, use the standard urls.
    open_browser : bool (optional)
        if True (default), then open a web browser to the given HTML
    http_server : class (optional)
        optionally specify an HTTPServer class to use for showing the
        visualization. The default is Python's basic HTTPServer.
    **kwargs :
        additional keyword arguments are passed through to :func:`prepared_data_to_html`

    See Also
    --------
    :func:`display` : embed visualization within the IPython notebook
    :func:`enable_notebook` : automatically embed visualizations in IPython notebook
    """
    if local:
        kwargs['ldavis_url'] = '/LDAvis.js'
        kwargs['d3_url'] = '/d3.js'
        kwargs['ldavis_css_url'] = '/LDAvis.css'
        files = {'/LDAvis.js': ["text/javascript",
                 open(urls.LDAVIS_LOCAL, 'r').read()],
                 '/LDAvis.css': ["text/css",
                                 open(urls.LDAVIS_CSS_LOCAL, 'r').read()],
                 '/d3.js': ["text/javascript",
                            open(urls.D3_LOCAL, 'r').read()]}
    else:
        files = None

    html = prepared_data_to_html(data, **kwargs)
    serve(html, ip=ip, port=port, n_retries=n_retries, files=files,
          open_browser=open_browser, http_server=http_server)


def enable_notebook(local=False, **kwargs):
    """Enable the automatic display of visualizations in the IPython Notebook.

    Parameters
    ----------
    local : boolean (optional, default=False)
        if True, then copy the d3 & LDAvis libraries to a location visible to
        the notebook server, and source them from there. See Notes below.
    **kwargs :
        all keyword parameters are passed through to :func:`prepared_data_to_html`

    Notes
    -----
    Known issues: using ``local=True`` may not work correctly in certain cases:

    - In IPython < 2.0, ``local=True`` may fail if the current working
      directory is changed within the notebook (e.g. with the %cd command).
    - In IPython 2.0+, ``local=True`` may fail if a url prefix is added
      (e.g. by setting NotebookApp.base_url).

    See Also
    --------
    :func:`disable_notebook` : undo the action of enable_notebook
    :func:`display` : embed visualization within the IPython notebook
    :func:`show` : launch a local server and show a visualization in a browser
    """
    try:
        from IPython.core.getipython import get_ipython
    except ImportError:
        raise ImportError('This feature requires IPython 1.0+')

    if local:
        if 'ldavis_url' in kwargs or 'd3_url' in kwargs:
            warnings.warn(
                "enable_notebook: specified urls are ignored when local=True")
        kwargs['d3_url'], kwargs['ldavis_url'], kwargs['ldavis_css_url'] = write_ipynb_local_js()

    ip = get_ipython()
    formatter = ip.display_formatter.formatters['text/html']
    formatter.for_type(PreparedData,
                       lambda data, kwds=kwargs: prepared_data_to_html(data, **kwds))


def disable_notebook():
    """Disable the automatic display of visualizations in the IPython Notebook.

    See Also
    --------
    :func:`enable_notebook` : automatically embed visualizations in IPython notebook
    """
    try:
        from IPython.core.getipython import get_ipython
    except ImportError:
        raise ImportError('This feature requires IPython 1.0+')
    ip = get_ipython()
    formatter = ip.display_formatter.formatters['text/html']
    formatter.type_printers.pop(PreparedData, None)


def save_html(data, fileobj, **kwargs):
    """Save an embedded visualization to file.

    This will produce a self-contained HTML file. Internet access is still required
    for the D3 and LDAvis libraries.

    Parameters
    ----------
    data : PreparedData, created using :func:`prepare`
        The data for the visualization.
    fileobj : filename or file object
        The filename or file-like object in which to write the HTML
        representation of the visualization.
    **kwargs :
        additional keyword arguments will be passed to :func:`prepared_data_to_html`

    See Also
    --------
    :func:`save_json`: save json representation of a visualization to file
    :func:`prepared_data_to_html` : output html representation of the visualization
    :func:`fig_to_dict` : output dictionary representation of the visualization
    """
    try:
        if isinstance(fileobj, basestring):
            fileobj = open(fileobj, 'w')
    except NameError:
        if isinstance(fileobj, str):
            fileobj = open(fileobj, 'w')
    if not hasattr(fileobj, 'write'):
        raise ValueError("fileobj should be a filename or a writable file")
    fileobj.write(prepared_data_to_html(data, **kwargs))


def save_json(data, fileobj):
    """Save the visualization's data a json file.

    Parameters
    ----------
    data : PreparedData, created using :func:`prepare`
        The data for the visualization.
    fileobj : filename or file object
        The filename or file-like object in which to write the HTML
        representation of the visualization.

    See Also
    --------
    :func:`save_html` : save html representation of a visualization to file
    :func:`prepared_data_to_html` : output html representation of the visualization
    """
    try:
        if isinstance(fileobj, basestring):
            fileobj = open(fileobj, 'w')
    except NameError:
        if isinstance(fileobj, str):
            fileobj = open(fileobj, 'w')
    if not hasattr(fileobj, 'write'):
        raise ValueError("fileobj should be a filename or a writable file")
    json.dump(data.to_dict(), fileobj, cls=NumPyEncoder)