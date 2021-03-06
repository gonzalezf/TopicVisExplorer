
import numpy as np
import gensim

def create_eta(priors, etadict, ntopics):
    print('Creando eta')
    eta = np.full(shape=(ntopics, len(etadict)), fill_value=1) # create a (ntopics, nterms) matrix and fill with 1
    for word, topic in priors.items(): # for each word in the list of priors
        keyindex = [index for index,term in etadict.items() if term==word] # look up the word in the dictionary
        if (len(keyindex)>0): # if it's in the dictionary
            eta[topic,keyindex[0]] = 1e7  # put a large number in there
    #eta = np.divide(eta, eta.sum(axis=0)) # normalize so that the probabilities sum to 1 over all topics
    print('eta fue creadoooo!! yayy')
    return eta



def create_new_guided_lda_model(eta, dictionary,corpus, ntopics, print_topics=True, print_dist=True):
    print( 'Create new guided lda model ')
    np.random.seed(42) # set the random seed for repeatability
    with (np.errstate(divide='ignore')):  # ignore divide-by-zero warnings        
        model = gensim.models.LdaMulticore(
            corpus=corpus, id2word=dictionary, num_topics=ntopics,
            eta=eta)
    # visuzlize the model term topics
    #viz_model(model, dictionary)
    print('Perplexity: {:.2f}'.format(model.log_perplexity(corpus)))
    if print_topics:
        # display the top terms for each topic
        for topic in range(ntopics):
            print('Topic {}: {}'.format(topic, [dictionary[w] for w,p in model.get_topic_terms(topic, topn=20)]))
    return model


