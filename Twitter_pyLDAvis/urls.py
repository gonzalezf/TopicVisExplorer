"""
LDAvis URLs
==========
URLs and filepaths for the LDAvis javascript libraries
"""

import os
#from . import __path__, __version__

__all__ = ["D3_URL", "LDAVIS_URL", "LDAVISMIN_URL", "LDAVIS_CSS_URL",
           "D3_LOCAL", "LDAVIS_LOCAL", "LDAVISMIN_LOCAL", "LDAVIS_CSS_LOCAL"]

D3_URL = "https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js"

#DEV = 'git' in __version__

DEV = True #Modo de desarrollo, cambiar a produccion
#LOCAL_JS_DIR = os.path.join(__path__[0], "js")
LOCAL_JS_DIR = 'static/js/'
D3_LOCAL = os.path.join(LOCAL_JS_DIR, "d3.v3.min.js")

if DEV:
    WWW_JS_DIR = "https://objectstorage.sa-saopaulo-1.oraclecloud.com/n/grynqsphwqoi/b/twitter_pyldavis/o/"
    LDAVIS_URL = WWW_JS_DIR + "ldavis.js"
    LDAVIS_CSS_URL = WWW_JS_DIR + "ldavis.css"
    LDAVIS_TWEET_CSS_URL = WWW_JS_DIR + "tweet.css"
    LDAVIS_LOCAL = os.path.join(LOCAL_JS_DIR, "ldavis.js")

    LDAVIS_CSS_LOCAL = os.path.join(LOCAL_JS_DIR, "ldavis.css")
else:
    WWW_JS_DIR = "https://objectstorage.sa-saopaulo-1.oraclecloud.com/n/grynqsphwqoi/b/twitter_pyldavis/o/"
    JS_VERSION = '1.0.0'
    CSS_VERSION = '1.0.0'

    LDAVIS_URL = WWW_JS_DIR + "ldavis.js".format(JS_VERSION)
    LDAVIS_TWEET_CSS_URL = WWW_JS_DIR + "tweet.css"
    LDAVIS_CSS_URL = WWW_JS_DIR + "ldavis.v{0}.css".format(CSS_VERSION)

    LDAVIS_LOCAL = os.path.join(LOCAL_JS_DIR,
                                "ldavis.js".format(JS_VERSION))

    LDAVIS_CSS_LOCAL = os.path.join(LOCAL_JS_DIR,
                                    "ldavis.v{0}.css".format(CSS_VERSION))

LDAVISMIN_URL = LDAVIS_URL
LDAVISMIN_LOCAL = LDAVIS_LOCAL
