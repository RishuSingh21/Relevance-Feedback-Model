import Classes.Query as Query
import Classes.Document as Document
from operator import attrgetter

class QueryRetrievalModel:

    indexReader=[]
    total_docs=0
    mu = 2000
    def __init__(self, ixReader):
        self.indexReader = ixReader
        
        #to get the length of the collection
        for i in range(self.indexReader.getDocCount()):
            self.total_docs += self.indexReader.getDocLength(i)
        return


    # query:  The query to be searched for.
    # topN: The maximum number of returned documents.
    # The returned results (retrieved documents) should be ranked by the score (from the most relevant to the least).
    # You will find our IndexingLucene.Myindexreader provides method: docLength().
    # Returned documents should be a list of Document.
    def retrieveQuery(self, query, topN):
        score = {}
        relevant_doc_id = set()
        col_freq = {}
        relevant_doc = {}
        document = []
        query_words = query.queryContent.split()
        for word in query_words:
            #Checking whether query term exist in the collection or not 
            if self.indexReader.getPostingList(word) != {}:  
                posting_list = self.indexReader.getPostingList(word)
                #this dictionary will be used to get the freq of a word for a specific doc_id
            #it will be used for ranking
                relevant_doc[word]=posting_list 
                col_freq[word]=self.indexReader.CollectionFreq(word)
                #creating a set of doc_ids containing atleast one query term
                for doc in posting_list.keys():
                    relevant_doc_id.add(doc)
        #iterating through all the relevant doc_ids to calculate the score and further use it for ranking
        for doc_id in relevant_doc_id:
            doc = Document.Document()
            doc.setDocId(doc_id)
            doc.setDocNo(self.indexReader.getDocNo(doc_id))
            score = 1
            doc_len = self.indexReader.getDocLength(doc_id)
            alpha = doc_len/(doc_len+self.mu)
            for word in relevant_doc.keys():
                prob_word_col = col_freq[word]/self.total_docs
                #if query term exist in the current doc then we are calculating its frequency else assigning 0 to its frequency
                if doc_id in relevant_doc[word].keys():
                    freq = relevant_doc[word][doc_id]
                else:
                    freq = 0
                score *= (freq+(self.mu*prob_word_col))/(doc_len+self.mu)
            doc.setScore(score)
            document.append(doc)
        #Sorting the list on the basis of descending score
        ranklist = sorted(document, key=attrgetter('score'),reverse=True)
        #Shortlisting top N documents to return
        Nranklist = ranklist[:topN]
        return Nranklist