#Imports 
import pandas as pd
import numpy as np
import pickle
    #For tweet Gathring
import twint
import nest_asyncio
nest_asyncio.apply()
    #For tweet cleaning 
import re
from nltk.tokenize import word_tokenize
from string import punctuation 
import nltk
nltk.download('stop_words')
from nltk.corpus import stopwords 
import string
from pyarabic.araby import *
from pyarabic import trans
    #For tweet Preprocessing 
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
    #For word cloud
from ar_wordcloud import ArabicWordCloud
    #object saving
import joblib

    #For arabert
# from arabert.preprocess import ArabertPreprocessor
# import numpy as np

# from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer, BertTokenizer
# from transformers.data.processors import SingleSentenceClassificationProcessor
# from transformers import Trainer , TrainingArguments
# from transformers.trainer_utils import EvaluationStrategy
# from transformers.data.processors.utils import InputFeatures
# from torch.utils.data import Dataset
# from torch.utils.data import DataLoader
# from sklearn.utils import resample
# import logging
# import torch

# DATA_COLUMN = "text"
# model_name = 'aubmindlab/bert-base-arabertv02'
# max_len = 280


'''___________________________________ STEP1: Data Gathring ____________________________________ '''

def search(keywords , limit, Since = None, Until = None ):
    '''
    [PARAMETERS] 
        Since: 'yyyy-mm-dd' (string)
        Until: 'yyyy-mm-dd' (string)
        keywords: 'word1 OR word2 AND word3' (String)
    [RETURN]
        Tweets_df: (pandas data frame) ['id','date','place','tweet','hashtags','urls','nlikes',
                                        'nretweets','nreplies','username','name','language']]
    '''
    c = twint.Config()
    c.Hide_output = True
    
    #c.Limit = 5 if not (Since or Until) else None
    c.Limit = int(limit) if (limit != "" and limit != None) else 1
    #PANDAS
    c.Pandas = True
    c.Pandas_au = True
    c.Pandas_clean = True
    #SEARCH
    c.Search = keywords
    c.Since = Since
    c.Until = Until
    twint.run.Search(c)
    Tweets_df = twint.storage.panda.Tweets_df[['id','date','place','tweet','hashtags','urls',
                                               'nlikes','nretweets','nreplies','username','name','language']]
    Tweets_df.rename({'id': 'tweet_id', 'tweet': 'tweet_text'}, axis=1, inplace=True)
    return Tweets_df

'''___________________________________ STEP2: Clean dataframe  ____________________________________ '''

def cleanDataframe(Tweets_df):
    '''
    [PARAMETER] 
        Tweets_df: (pandas data frame) ['id','date','place','tweet','hashtags','urls','nlikes',
                                        'nretweets','nreplies','username','name','language'] (pandas.core.frame.DataFrame)

    [RETURN]
        Tweets_df: (pandas data frame) ['id','date','place','tweet','hashtags','urls','nlikes',
                                        'nretweets','nreplies','username','name'] (pandas.core.frame.DataFrame)

    '''
    #convert hashtags and urls data type into list
    df_clean = Tweets_df.copy()
    df_clean.hashtags = df_clean.hashtags.apply(lambda x: " ".join(x))
    df_clean.urls = df_clean.urls.apply(lambda x: " ".join(x))
    #drop duplicates 
    df_clean = df_clean.drop_duplicates(subset=["tweet_text"],keep='first')
    #drop @alkahraba and @alkahrabacare tweets
    df_clean.drop(df_clean[df_clean['username'] == "AlkahrabaCare"].index, inplace = True)
    df_clean.drop(df_clean[df_clean['username'] == "ALKAHRABA"].index, inplace = True) 
    df_clean.drop(df_clean[df_clean['username'] == "alKahrabaFriend"].index, inplace = True)
    print('df_clean[username]', df_clean['username'].value_counts())
    #only keep arabic tweets and then drop language column
    df_clean = df_clean.loc[df_clean['language'] == 'ar']
    df_clean = df_clean.drop(['language'], axis=1)
    
    return df_clean


'''___________________________________ STEP3: Clean text  ____________________________________ '''
def Emoji_Dict():
    '''
    [PARAMETERS]:

    [RETURN]:
        Emoji_Dict: {'😞': ':disappointed_face:','😵': ':dizzy_face:',...} (dictionary)
    '''
    with open('SEC_App/static/SEC_App/Emoji_Dict.p', 'rb') as fp:
        Emoji_Dict = pickle.load(fp)
    Emoji_Dict = {v: k for k, v in Emoji_Dict.items()}
    return Emoji_Dict

def convert_emojis_to_word(text,Emoji_Dict):
    '''
    [PARAMETERS]:
        text: text that might have Emojis in it "whay😞??" (string)
        Emoji_Dict: {'😞': ':disappointed_face:','😵': ':dizzy_face:',...} (dictionary)
    [RETURN]:
        text: text with Emojis converted to it corresponding string "whay disappointed_face ??" (string)
    '''
    for emot in Emoji_Dict:
        text = re.sub(r'('+emot+')', ' '+("_".join(Emoji_Dict[emot].replace(",","").replace(":"," ").split()))+' ', text)
    return text

def stopwords_set():
    stopwords_file = open("SEC_App/static/SEC_App/stop_words.txt", "r")
    extra_stopwords = stopwords_file.read()
    extra_stopwords = extra_stopwords.split("\n")
    stopwords_set = set(stopwords.words('arabic')+ extra_stopwords)
    return stopwords_set


def cleanTxt(text,Emoji_Dict,stopwords_set):
    '''
    [PARAMETERS]:
        text: tweet text to be cleaned  (string)
        Emoji_Dict: {'😞': ':disappointed_face:','😵': ':dizzy_face:',...} (dictionary)
        stopwords_set: set of stopwords to be reomved from the text (set)
    [RETURN]:
        text: word tokenized list after text cleaning  ['لمذا','disappointed_face','الكذب'](list of strings)
    '''

    text = text.lower()
    
    text = strip_tatweel(text) #Removing tatweel 
    text = strip_tashkeel(text) #Removing tashkeel
    
    text = re.sub(r'\bال(\w\w+)', r'\1', text)  # Removing al ta3reef
    text = re.sub("[إأآءاٱ]+", "ا", text) # normalize_hamza and unified repeated hamza
    
    text = re.sub('@[A-Za-z0–9]+[\_]*[A-Za-z0–9]*', '', text)  #Removing @mentions
    text = re.sub('[#‘’“”…]', '', text) # Removing '#' hash tag
    text = re.sub('RT[\s]+', '', text) # Removing RT
    text = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', '', text) # Removing URLs
    
    text = re.sub('\[.*&\-]', '', text) #Removing .,*,&,-

    text = re.sub('[%s]' % re.escape(string.punctuation), '', text) #Removing english punctuations
    arabic_punctuations = '''`÷×؛<>_()*&^%][ـ،/:"؟.,'{}~¦+|!”…“–ـ'''
    text = text.translate(str.maketrans('', '', arabic_punctuations))#Removing arabic punctuations
    
    text = normalize_hamza(text) #normlize hamza آائئء  ---> ءءءءءء
    
    text = trans.normalize_digits(text, source='all', out='west') #arabic (١٢٣٤٥) digits into west(12345)
    text = re.sub('\w*\d\w*', '', text)#Removing digits
    
    text = re.sub(r"\b[a-zA-Z0–9]\b", "", text) #Removing single charcter word
    
    text = convert_emojis_to_word(text,Emoji_Dict)
    text1 = tokenize(text)

    return [word for word in text if word not in stopwords_set and len(word)>3 ]


'''___________________________________ STEP4: Preprocessing text  ____________________________________ '''

def dtm_df(text_column):
    '''
    [PARAMETERS]:
        text_column: dataframe column containing list of word string (pandas.core.series.Series)
    [RETURN]:
        dtm_df: document term matric  (pandas.core.frame.DataFrame)
    '''

    max_df = int(text_column.shape[0]*0.3)
    min_df = int(text_column.shape[0]*0.01)
    
    filename = 'vectorizer1.sav'
    vectorizer = pickle.load(open(filename, 'rb'))
    #vectorizer = joblib.load("vectorizer2.sav")
    
    text_column = text_column.apply(lambda x : " ".join(x)) # convert column values into string 
    vectorizer_df = vectorizer.transform(text_column)
    dtm_df = pd.DataFrame(vectorizer_df.toarray(), columns=vectorizer.get_feature_names())
    dtm_df.index = text_column.index
    return dtm_df


'''___________________________________  Word Cloud   ____________________________________ '''

def word_cloud(dtm_df,path = None):
    '''
    [PARAMETERS]:
        dtm_df: document term matric dataframe  (pandas.core.frame.DataFrame)
        path: path where the word cloud to be saved (string)
    [RETURN]:
        awc: arabic word cloud object  (ar_wordcloud.ar_wordcloud.ArabicWordCloud)
    '''   
    awc = ArabicWordCloud(background_color="black",font='NotoSansArabic-ExtraBold.ttf')
    dic_df = {}
    #create dictionary of arabic word with its acurance count
    counter = 0
    for column in dtm_df.columns:
        if not re.search('[a-zA-Z]+',column):
            dic_df[column]= dtm_df[column].sum()
            counter += 1
            if counter >= 50:
                break
    #create word cloud         
    dic_df = awc.from_dict(dic_df, ignore_stopwords=True)
    #show word cloud
    #awc.plot(dic_df, title="سحابة الكلمات ", width=8, height=7)
    #save word cloud 
    if path:
        awc.to_file(path)

'''___________________________________  Predict Sentiments  ____________________________________ '''
# class Dataset:
#     def __init__(
#         self,
#         name,
#         test,
#         label_list,
#     ):
#         self.name = name
#         self.test = test
#         self.label_list = label_list

# class BERTDataset(Dataset):
#     def __init__(self, text, model_name, max_len):
#       super(BERTDataset).__init__()
#       self.text = text
#       self.tokenizer_name = model_name
#       self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#       self.max_len = max_len

#     def __len__(self):
#       return len(self.text)

#     def __getitem__(self,item):
#       text = str(self.text[item])
#       text = " ".join(text.split())

#       input_ids = self.tokenizer.encode(
#           text,
#           add_special_tokens=True,
#           max_length=self.max_len,
#           truncation='longest_first'
#       )     
    
#       attention_mask = [1] * len(input_ids)

#       # Zero-pad up to the sequence length.
#       padding_length = self.max_len - len(input_ids)
#       input_ids = input_ids + ([self.tokenizer.pad_token_id] * padding_length)
#       attention_mask = attention_mask + ([0] * padding_length)

#       return InputFeatures(input_ids=input_ids, attention_mask=attention_mask)

# def create_dataset(tweets_text):
#     tweets_text = tweets_text[["Text"]]  
#     tweets_text.columns = [DATA_COLUMN]
#     label_list_KAUST = ['NEG', 'NEUTRAL', 'POS']
#     tweets = Dataset("tweets_text", tweets_text, label_list_KAUST)

#     arabert_prep = ArabertPreprocessor(model_name.split("/")[-1])
#     tweets.test[DATA_COLUMN] = tweets.test[DATA_COLUMN].apply(lambda x:   arabert_prep.preprocess(x))  
#     tweets_dataset = BERTDataset(tweets.test[DATA_COLUMN].to_list(),model_name,max_len)
     
#     return tweets_dataset

     
# def load_arabert_model():
#     PATH = '/Users/sarahalhabib/Downloads/kaust_arabert'
#     model = AutoModelForSequenceClassification.from_pretrained(PATH, return_dict=True, num_labels=3)
    
#     trainer = Trainer(
#         model = model,
#     )

#     return trainer

# def predict_sentiments(tweets_text):
#     #load model 
#     model = load_arabert_model()
#     predictions = model.predict(create_dataset(tweets_text))
#     sentiments = np.argmax(predictions.predictions, axis=1)-1
    
#     return sentiments

def predict_sentiments(tweets_df, dtm):
    
    # save the model to disk
    filename = 'model1.sav'
    # some time later...
    # load the model from disk
    loaded_model = joblib.load(filename)
    result = loaded_model.predict(dtm)
    print('result:', result)
    tweets_df['sentiment']=result
    return tweets_df

'''___________________________________ Main  ____________________________________ '''

'''
STEPS:
    1- Search for tweets
    2- Clean dataframe 
    3- Clean text
    3- Preprocessing text
'''

if __name__ == "__main__":
    #Search for tweets
    df = search("@ALKAHRABA OR @AlkahrabaCare")

    #Clean dataframe 
    df = cleanDataframe(df)

    #Clean text
    df['tweet_text'] =  df['tweet_text'].apply(lambda text : cleanTxt(text,Emoji_Dict(),stopwords_set()) )

    #Preprocessing text: create document term matrix 
    dtm_df = dtm_df(df['tweet_text'])

    #(create+show,save:optional) arabic word cloud 
    word_cloud(dtm_df)

    