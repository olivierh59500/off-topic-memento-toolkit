import distance
import string
import logging

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

from .collectionmodel import CollectionModelMementoErrorException

logger = logging.getLogger(__name__)

stemmer = PorterStemmer()

def stem_tokens(tokens):

    stemmed = []

    for item in tokens:
        stemmed.append( stemmer.stem(item) )

    return stemmed

def full_tokenize(text, stemming=True):

    stopset = stopwords.words("english") + list(string.punctuation)

    tokens = word_tokenize(text.decode("utf8"))

    if stemming:
        stems = stem_tokens(tokens)

    return [ i for i in stems if i not in stopset ]

def get_memento_data_for_measure(urim, collection_model,
    tokenize=True, stemming=True, remove_boilerplate=True):

    data = None

    if remove_boilerplate:
        data = collection_model.getMementoContentWithoutBoilerplate(urim)
    else:
        data = collection_model.getMementoContent(urim)

    if tokenize:
        data = full_tokenize(data, stemming=stemming)

    return data


def compute_score_across_TimeMap(collectionmodel, measurename,
    scoredistance_function=None, 
    scores=None, tokenize=True, stemming=True,
    remove_boilerplate=True):

    if scores == None:
        scores = {}
        scores["timemaps"] = {}

    logger.info("Computing score across TimeMap, beginning TimeMap iteration...")

    urits = collectionmodel.getTimeMapURIList()
    urittotal = len(urits)
    uritcounter = 1

    for urit in urits:

        logger.info("Processing TimeMap {} of {}".format(uritcounter, urittotal))
        logger.debug("Processing mementos from TimeMap at {}".format(urit))

        timemap = collectionmodel.getTimeMap(urit)

        scores["timemaps"].setdefault(urit, {})

        memento_list = timemap["mementos"]["list"]

        # some TimeMaps have no mementos
        # e.g., http://wayback.archive-it.org/3936/timemap/link/http://www.peacecorps.gov/shutdown/?from=hpb
        if len(memento_list) > 0:

            first_urim = timemap["mementos"]["first"]["uri"]

            logger.debug("Accessing content of first URI-M {} for calculations".format(first_urim))

            first_data = get_memento_data_for_measure(
                first_urim, collectionmodel, tokenize=tokenize, stemming=stemming, 
                remove_boilerplate=remove_boilerplate)

            mementos = timemap["mementos"]["list"]

            mementototal = len(mementos)
            logger.info("There are {} mementos in this TimeMap".format(mementototal))

            mementocounter = 1

            for memento in mementos:

                logger.info("Processing Memento {} of {}".format(mementocounter, mementototal))

                urim = memento["uri"]

                logger.debug("Accessing content of URI-M {} for calculations".format(urim))

                scores["timemaps"][urit].setdefault(urim, {})

                try:
                    memento_data = get_memento_data_for_measure(
                        urim, collectionmodel, tokenize=tokenize, 
                        stemming=stemming, 
                        remove_boilerplate=remove_boilerplate)
                        
                    scores["timemaps"][urit][urim][measurename] = \
                        scoredistance_function(first_data, memento_data)

                except CollectionModelMementoErrorException:
                    logger.warning("Errors were recorded while attempting to "
                        "access URI-M {}, skipping {} calcualtions for this "
                        "URI-M".format(urim, measurename))
                
                mementocounter += 1

            uritcounter += 1

    return scores

def bytecount_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    if type(first_data) == type(memento_data):

        if type(first_data) == list:

            first_data = ''.join(first_data)
            memento_data = ''.join(memento_data)

    first_bytecount = len(first_data)
    memento_bytecount = len(memento_data)

    # TODO: score cache for individual scores
    scoredata["individual score"] = memento_bytecount
    
    # TODO: score cache for scores of both items
    if memento_bytecount == 0:

        if first_bytecount == 0:
            scoredata["comparison score"] = 0

        else:
            scoredata["comparison score"] = 1 -  (memento_bytecount / first_bytecount)

    else:
        scoredata["comparison score"] = 1 -  (memento_bytecount / first_bytecount)
    
    return scoredata

def compute_bytecount_across_TimeMap(collectionmodel, scores=None, tokenize=False, stemming=False):

    scores = compute_score_across_TimeMap(collectionmodel, "bytecount", 
        bytecount_scoredistance, scores=scores, tokenize=False, stemming=False,
        remove_boilerplate=False
    )

    return scores

def wordcount_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    first_wordcount = len(first_data)
    memento_wordcount = len(memento_data)

    scoredata["individual score"] = memento_wordcount

    if memento_wordcount == 0:

        if first_wordcount == 0:
            scoredata["comparison score"] = 0

        else:
            scoredata["comparison score"] = 1 -  (memento_wordcount / first_wordcount)

    else:
        scoredata["comparison score"] = 1 -  (memento_wordcount / first_wordcount)

    return scoredata

def compute_wordcount_across_TimeMap(collectionmodel, scores=None, stemming=True):
    
    scores = compute_score_across_TimeMap(collectionmodel, "wordcount", 
        wordcount_scoredistance, scores=scores, tokenize=True, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def jaccard_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.jaccard(first_data, memento_data)

    return scoredata

def compute_jaccard_across_TimeMap(collectionmodel, scores=None, tokenize=True, stemming=True):

    scores = compute_score_across_TimeMap(collectionmodel, "jaccard", 
        jaccard_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def sorensen_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.sorensen(first_data, memento_data)

    return scoredata

def compute_sorensen_across_TimeMap(collectionmodel, scores=None, tokenize=False, stemming=False):
    
    scores = compute_score_across_TimeMap(collectionmodel, "sorensen", 
        sorensen_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def levenshtein_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.levenshtein(first_data, memento_data)

    return scoredata

def compute_levenshtein_across_TimeMap(collectionmodel, scores=None, tokenize=False, stemming=False):
    
    scores = compute_score_across_TimeMap(collectionmodel, "levenshtein", 
        levenshtein_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def nlevenshtein_scoredistance(first_data, memento_data, scorecache=None):

    scoredata = {}

    scoredata["comparison score"] = distance.nlevenshtein(first_data, memento_data)

    return scoredata

def compute_nlevenshtein_across_TimeMap(collectionmodel, scores=None, tokenize=False, stemming=False):

    scores = compute_score_across_TimeMap(collectionmodel, "nlevenshtein", 
        nlevenshtein_scoredistance, scores=scores, tokenize=tokenize, stemming=stemming,
        remove_boilerplate=True
    )

    return scores

def compute_cosine_across_TimeMap(collectionmodel, scores=None, stemming=True):
    scores = {}

    return scores