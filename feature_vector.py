import numpy as np
import string
from scipy.sparse import coo_matrix
import utils
import inspect

"""
Class template for feature vectors. f(x,c)
Extending the dictionary class to return 0 if one tries to acceess a feature vector for a missing key.
An alternative implementation is commented below in case the method of extending the dict class is not adequate.
"""
class FeatureVector():
    # this extended dictionary class is initialised by passing a list of functions to it. These are then assigned as dictionary items upon init.
    def __init__(self, mode = 'argument'):
        if mode not in ['argument', 'trigger', 'joint']:
            print 'ERROR, wrong mode of calling FeatureVector class! '

        
        #get handles to all phi functions
        self.methods = inspect.getmembers(self, predicate=inspect.ismethod)  
        self.mode = mode    
        if self.mode == 'argument' or self.mode == 'trigger':                   
            self.phi_list = [method[1] for method in self.methods if 'phi_'+mode in method[0]]
        elif mode == 'joint':
            self.phi_list_arg = [method[1] for method in self.methods if 'phi_argument' in method[0]]
            self.phi_list_trig = [method[1] for method in self.methods if 'phi_trigger' in method[0]]
            
        
        #load relevant other data from presaved files.
        self.listOfAllFiles = utils.list_files()
        self.all_grammar_tags = utils.get_grammar_tag_list()
        self.trigger_list = utils.get_trigger_list()
        self.stem_list = utils.create_stem_list()
        self.arguments_list = [u'None', u'Theme', u'Cause']


    #Feature matrix for trigger prediction
    def get_feature_matrix(self, token_index, sentence):
        col_indices = []
        values = []
        n_classes = 10  #length of list of all occurring triggers in dataset.
        d=0
        if self.mode == 'trigger':
            phi_list = self.phi_list
        elif self.mode == 'joint':
            phi_list = self.phi_list_trig
        else:
            print 'ERROR: WRONG USE OF FUNCTION get_feature_matrix()'
            
        for phi in phi_list:
            phi_vector = phi(token_index, sentence)
            index = list(np.nonzero(np.array(phi_vector))[0])
            col_indices += [i+d for i in index]    # offset d in matrix       
            values += list(np.array(phi_vector)[index])            
            d += len(phi_vector)

        all_col_indices = []
        all_row_indices = []
        all_values = []
        for c in range(n_classes):
            all_row_indices += [c]*len(values)       
            all_col_indices += col_indices
            all_values += values        
         
        
        sparse_feature_matrix = coo_matrix((np.array(all_values), 
                                           (np.asarray(all_row_indices),
                                            np.array(all_col_indices) ) ),
                                            shape=(n_classes,d))
            
        return sparse_feature_matrix
        
        
    #Get feature matrix for argument prediction: for pairs of tokens and 
    #argument candidates. Otherwise same skeleton as "get_feature_matrix()"
    def get_feature_matrix_argument_prediction(self, token_index, arg_index, sentence):
        col_indices = []
        values = []
        d=0
        n_classes = 3  #possible predictions: [None, Theme, Cause]
        
        if self.mode == 'argument':
            phi_list = self.phi_list
        elif self.mode == 'joint':
            phi_list = self.phi_list_arg
        else:
            print 'ERROR: WRONG USE OF FUNCTION get_feature_matrix_argument_prediction()'
         
            
        
        for phi in phi_list:
                phi_vector = phi(token_index, arg_index, sentence)
                index = list(np.nonzero(np.array(phi_vector))[0])
                col_indices += [i+d for i in index]    # offset d in matrix                
                values += list(np.array(phi_vector)[index])
                d += len(phi_vector)

        
        all_col_indices = []
        all_row_indices = []
        all_values = []                
        for c in range(n_classes):
            all_col_indices += col_indices            
            all_row_indices += [c]*len(values)
            all_values += values        
        
        sparse_feature_matrix = coo_matrix((np.array(all_values), 
                                           (np.asarray(all_row_indices),
                                            np.array(all_col_indices) ) ),
                                            shape=(n_classes,d))
            
        return sparse_feature_matrix
    
    
    
    # feature templates take as input a token_index and sentence (which is
    # a sentence from the json dictionary, containing all information about grammar
    # tags, links and relations to other tokens, their positions, and finally
    # also the gold labels for both triggers and arguments.) Note that the token
    # is not a string, but the index at which this token appears in sentence.
    """TRIGGER FEATURES"""
    def phi_trigger_0(self, token_index, sentence):
        #This is merely an example for computing features across a comparison list.
        token = sentence['tokens'][token_index]['word']
        symbols_list = string.printable
        return_vec = [ np.uint8(character in token)  for character in symbols_list]
        return return_vec      
    
    # check for each grammar tag (e.g. NN) if token is this grammatical pos tag.
    def phi_trigger_1(self, token_index, sentence):
        observed_grammar_tag = sentence['tokens'][token_index]['pos'] #e.g. 'NN'
        index = self.all_grammar_tags.index(observed_grammar_tag)
        
        unit_vec = np.zeros(len(self.all_grammar_tags), dtype = np.uint8)
        unit_vec[index] = 1.0
        return list(unit_vec)
    
    def phi_trigger_2(self, token_index, sentence):
        #evaluate stem of token.
        observed_stem = sentence['tokens'][token_index]['stem'] 
        unit_vec = np.zeros(len(self.stem_list), dtype = np.uint8)

        if observed_stem in self.stem_list:
            index = self.stem_list.index(observed_stem)
            unit_vec[index] = 1.0
        return list(unit_vec) 
    
    """ARGUMENT FEATURES"""
    def phi_argument_0(self, token_index, arg_index, sentence):
        #extract if argument is a protein   (Mentions)
        protein = [0]
        for mention in sentence['mentions']:
            if arg_index >= mention['begin'] and arg_index < mention['end']:
                protein = [1]
        return protein    
    
    def phi_argument_1(self, token_index, arg_index, sentence):
        #evaluate grammar pos tag of argument
        observed_grammar_tag = sentence['tokens'][arg_index]['pos']    
        index = self.all_grammar_tags.index(observed_grammar_tag)
        
        unit_vec = np.zeros(len(self.all_grammar_tags), dtype = np.uint8)
        unit_vec[index] = 1.0
        return list(unit_vec) 
    
    def phi_argument_2(self, token_index, arg_index, sentence):
        #evaluate grammar pos tag of token
        observed_grammar_tag = sentence['tokens'][token_index]['pos']
        index = self.all_grammar_tags.index(observed_grammar_tag)
        
        unit_vec = np.zeros(len(self.all_grammar_tags), dtype = np.uint8)
        unit_vec[index] = 1.0
        return list(unit_vec)  
    
    def phi_argument_3(self, token_index, arg_index, sentence):
        #evaluate stem of token.
        observed_stem = sentence['tokens'][token_index]['stem'] 
        unit_vec = np.zeros(len(self.stem_list), dtype = np.uint8)

        if observed_stem in self.stem_list:
            index = self.stem_list.index(observed_stem)
            unit_vec[index] = 1.0
        return list(unit_vec) 
    



""" OLD feature functions. Not thrown away yet.


# alternative function by Johannes (obsolete)
# takes as input a word + the sentence it occurs in (dict-structure from 
# json file). 
def get_vector_alternative(self, token_index, sentence, all_grammar_tags):
    all_col_indices = []
    values = []
    n_samples = 1
    d=0
    for phi in self:
        phi_vector = self[phi](token_index,sentence, all_grammar_tags)

        index = list(np.nonzero(np.array(phi_vector))[0])
        all_col_indices += [i+d for i in index] # offset d in matrix
        d += len(phi_vector)

        values += list(np.array(phi_vector)[index])

    sparse_feature_matrix = coo_matrix((np.array(values), (np.zeros(np.shape(all_col_indices)) ,np.array(all_col_indices))), shape=(n_samples,d))
    
    return sparse_feature_matrix


#New version: Compute feature vec for whole batch of inputs!
#Return a sparse matrix, rows: samples. cols: feature dimensions.
def get_feature_batch(self, token_index_list, sentence_list, all_grammar_tags):
    n_samples = len(token_index_list)
    d=0
    all_col_indices = []
    all_row_indices = []
    values = []
    for (s, (sentence, token_index)) in enumerate(zip(sentence_list, token_index_list)):
        print s
        for phi in self:
            phi_vector = self[phi](token_index,sentence, all_grammar_tags)

            index = list(np.nonzero(np.array(phi_vector))[0])
            all_col_indices += [i+d for i in index]    # offset d in matrix                
            all_row_indices += [s]*len(index)
            
            values += list(np.array(phi_vector)[index])
            
            d += len(phi_vector)
     
    
    sparse_feature_matrix = coo_matrix((np.array(values), 
                                        (np.asarray(all_row_indices),
                                        np.array(all_col_indices) ) ),
                                        shape=(n_samples,d))
        
    return sparse_feature_matrix
"""


