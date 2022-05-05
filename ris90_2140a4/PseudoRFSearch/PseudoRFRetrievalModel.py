import Classes.Document as Document
import SearchWithWhoosh.QueryRetreivalModel as QueryRetreivalModel
from operator import attrgetter
class PseudoRFRetreivalModel:

    indexReader=[]
    mu = 2000
    total_docs = 0
    def __init__(self, ixReader):
        self.indexReader = ixReader
        self.search = QueryRetreivalModel.QueryRetrievalModel(self.indexReader)
         #to get the length of the collection
        for i in range(self.indexReader.getDocCount()):
            self.total_docs += self.indexReader.getDocLength(i)
        return

    # Search for the topic with pseudo relevance feedback.
    # The returned results (retrieved documents) should be ranked by the score (from the most relevant to the least).
    # query: The query to be searched for.
    # TopN: The maximum number of returned document
    # TopK: The count of feedback documents
    # alpha: parameter of relevance feedback model
    # return TopN most relevant document, in List structure

    def retrieveQuery(self, query, topN, topK, alpha):
        # this method will return the retrieval result of the given Query, and this result is enhanced with pseudo relevance feedback
        # (1) you should first use the original retrieval model to get TopK documents, which will be regarded as feedback documents
        # (2) implement GetTokenRFScore to get each query token's P(token|feedback model) in feedback documents
        # (3) implement the relevance feedback model for each token: combine the each query token's original retrieval score P(token|document) with its score in feedback documents P(token|feedback model)
        # (4) for each document, use the query likelihood language model to get the whole query's new score, P(Q|document)=P(token_1|document')*P(token_2|document')*...*P(token_n|document')
        
        #To get query terms
        querytoken=query.queryContent.split()
        #To get topK feedback doc 
        feedback_doc = self.search.retrieveQuery(query, topK)
        # get P(token|feedback documents)
        TokenRFScore = self.GetTokenRFScore(query, feedback_doc)
        
        #Calculating pseudoscore based on TokenRFScore
        score = {}
        col_freq = {}
        relevant_doc = {}
        document = []
        for word in querytoken:
            #Checking whether query term exist in the collection or not 
            if self.indexReader.getPostingList(word) != {}:  
                posting_list = self.indexReader.getPostingList(word)
                #this dictionary will be used to get the freq of a word for a specific doc_id
                #it will be used for ranking
                relevant_doc[word]=posting_list 
                col_freq[word]=self.indexReader.CollectionFreq(word)
       
        
       #iterating through all the relevant doc_ids to calculate the score and further use it for ranking
        for doc in feedback_doc:
            score = 1
            doc_id = doc.getDocId()
            doc_len = self.indexReader.getDocLength(doc.getDocId())
            for word in relevant_doc.keys():
                prob_word_col =  col_freq[word]/self.total_docs
                if doc_id in relevant_doc[word]:
                    freq = relevant_doc[word][doc_id]
                else:
                    freq = 0
                score *= alpha*((freq+(self.mu*prob_word_col))/(doc_len+self.mu)) + (1-alpha)*(TokenRFScore[word])
            doc.setScore(score)
            document.append(doc)
        
        # sort all retrieved documents from most relevant to least, and return TopN
        ranklist = sorted(document,  key=attrgetter('score'),reverse=True)
        #Shortlisting top N documents to return
        results = ranklist[:topN]
        return results

    def GetTokenRFScore(self, query, feedback_doc):
        # for each token in the query, you should calculate token's score in feedback documents: P(token|feedback documents)
        # use Dirichlet smoothing
        # save {token: score} in dictionary TokenRFScore, and return it
        TokenRFScore={}
        pseudoFreq=0
        pseudoLen=0
        
        querytoken=query.queryContent.split()
        
        #To get Documents Pseudo length
        for doc in feedback_doc:
            pseudoLen += self.indexReader.getDocLength(doc.getDocId())
        for token in querytoken:
            colFreq = self.indexReader.CollectionFreq(token)
            prob_word_col = colFreq/self.total_docs

            if colFreq != 0:
                posting = self.indexReader.getPostingList(token)
                #To get pseudo term document frequency
                for doc in feedback_doc:
                    doc_id = doc.getDocId()
                    if doc_id in posting.keys():
                        pseudoFreq += posting[doc_id]
                TokenRFScore[token] = (pseudoFreq+(self.mu*prob_word_col))/(pseudoLen+self.mu)
            else:
                TokenRFScore[token] = 0
        return TokenRFScore



