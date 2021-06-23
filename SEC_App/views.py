from ast import dump
from django.http.response import HttpResponseRedirect
from SEC_App.forms import RequestForm
from django.shortcuts import render
from django.http import HttpResponse
from .models import Request, Tweet
from django.utils import timezone
import pandas as pd
import datetime
import random
from json import dumps

import twint
import nest_asyncio
nest_asyncio.apply()
from .wordCloud import *

# Create your views here.

def searchView(request):
    # if request.method == 'POST':
    #     # create a form instance and populate it with data from the request:
    #     form = RequestForm(request.POST)
    #     form.save()
    #     return HttpResponseRedirect(request, "done")
    
    # form = RequestForm()
    # return render(request,'SEC_App/requestform.html', {'form': form})
    return render(request,'SEC_App/search.html')

def analysis(request):
    print('limit:', request.POST.get('limit',''))
    #create request model opject
    req = create_request(request)
    
    #Search for tweets
    tweets_df = search(req.keyword, limit=request.POST.get('limit',''), Since = req.period_start, Until = req.period_end)
    
    # create and save tweets model objects
    print(tweets_df.shape[0])
    for i, tweet in enumerate(tweets_df):
        req.tweet_set.create(tweet_id=tweets_df.iloc[i].tweet_id, date=tweets_df.iloc[i].date, place=tweets_df.iloc[i].place, tweet_text=tweets_df.iloc[i].tweet_text, hashtags=tweets_df.iloc[i].hashtags, urls=tweets_df.iloc[i].urls, nlike=tweets_df.iloc[i].nlikes, nretweet=tweets_df.iloc[i].nretweets, nreply=tweets_df.iloc[i].nreplies, username=tweets_df.iloc[i].username, name=tweets_df.iloc[i].name)
    req.save()

    # prepare tweet list to appear in result.html
    tweet_list = tweets_df.head(50)['tweet_text'].to_list()

    # actual from and to dates
    from_date = tweets_df.iloc[tweets_df.shape[0]-1].date[:10]
    to_date = tweets_df.iloc[0].date[:10]

    #create word cloud
    #Clean dataframe
    # tweets_df_cleaned = cleanDataframe(tweets_df)
    # #Clean text
    # tweets_df_cleaned['tweet_text'] =  tweets_df_cleaned['tweet_text'].apply(lambda text : cleanTxt(text,Emoji_Dict(),stopwords_set()))
    # #Preprocessing text: create document term matrix 
    # dtm = dtm_df(tweets_df_cleaned['tweet_text'])
    #(create+show,save:optional) arabic word cloud 
    #word_cloud(dtm, path='SEC_App/static/SEC_App/wordcloud.png')

    #tweets_df = predict_sentiments(tweets_df, dtm)

    reactions = get_reactions_dic(tweets_df)
    period_data = get_period_dic(tweets_df)
    sentiment_data = get_sentiment_dic(tweets_df)

    
    print('limit:', request.POST.get('limit',''))

    return render(request, 'SEC_App/results.html',{'tweets_list': tweet_list, 'reactions': reactions, 'req': req, 'from_date':from_date, 'to_date':to_date, 'period_data':period_data, 'sentiment_data':sentiment_data, 'num_tweets':tweets_df.shape[0]})

def get_reactions_dic(tweets_df):
    # raection bar chart data set
    tweets_df_reactions = pd.DataFrame()
    tweets_df_reactions['nlikes']= tweets_df['nlikes']
    tweets_df_reactions['nretweets'] = tweets_df['nretweets']
    tweets_df_reactions['nreplies'] = tweets_df['nreplies']
    tweets_df_reactions['sentiment'] = [random.randint(-1, 1) for i in range(tweets_df_reactions.shape[0])]
    tweets_df_reactions_negative = pd.DataFrame(tweets_df_reactions[tweets_df_reactions['sentiment']==-1])
    tweets_df_reactions_neutral = pd.DataFrame(tweets_df_reactions[tweets_df_reactions['sentiment']==0])
    tweets_df_reactions_positive = pd.DataFrame(tweets_df_reactions[tweets_df_reactions['sentiment']==1])

    likes_list = [int(np.sum(tweets_df_reactions_negative['nlikes'])), int(np.sum(tweets_df_reactions_neutral['nlikes'])), int(np.sum(tweets_df_reactions_positive['nlikes'])) ]
    replies_list = [int(np.sum(tweets_df_reactions_negative['nreplies'])), int(np.sum(tweets_df_reactions_neutral['nreplies'])), int(np.sum(tweets_df_reactions_positive['nreplies'])) ]
    retweets_list = [int(np.sum(tweets_df_reactions_negative['nretweets'])), int(np.sum(tweets_df_reactions_neutral['nretweets'])), int(np.sum(tweets_df_reactions_positive['nretweets'])) ]

    reactions_dic = {
        'likes': likes_list,
        'replies': replies_list,
        'retweets': retweets_list
    }

    reactions = dumps(reactions_dic)

    return reactions

def get_period_dic(tweets_df):
    #read tweets_df
    
    periods_df = tweets_df
    periods_df['sentiment'] = [random.randint(-1, 1) for i in range(periods_df.shape[0])]
    tweets_df_negative = pd.DataFrame(periods_df[periods_df['sentiment']==-1])
    tweets_df_neutral = pd.DataFrame(periods_df[periods_df['sentiment']==0])
    tweets_df_positive = pd.DataFrame(periods_df[periods_df['sentiment']==1])
    ########
    tweets_df_negative_Day_List = getListDays(tweets_df_negative)
    tweets_df_neutral_Day_List = getListDays(tweets_df_neutral)
    tweets_df_positive_Day_List = getListDays(tweets_df_positive)
    tweets_df_negative_Months_List = getListMonths(tweets_df_negative)
    tweets_df_neutral_Months_List = getListMonths(tweets_df_neutral)
    tweets_df_positive_Months_List = getListMonths(tweets_df_positive)
    #######
    print(tweets_df_negative_Day_List)
    print(tweets_df_neutral_Day_List)
    print(tweets_df_positive_Day_List)
    print("-------------------------------")
    print(tweets_df_negative_Months_List)
    print(tweets_df_neutral_Months_List)
    print(tweets_df_positive_Months_List)
    ######
    periods_dic = {
        'negativeDays': tweets_df_negative_Day_List,
        'neutralDays': tweets_df_neutral_Day_List,
        'positiveDays': tweets_df_positive_Day_List,
        'negativeMonths': tweets_df_negative_Months_List,
        'neutralMonths': tweets_df_neutral_Months_List,
        'positiveMonths': tweets_df_positive_Months_List
    }

    periods = dumps(periods_dic)

    return periods

def getListDays(tweets_df_sen):
    Full_Date = tweets_df_sen['date'].values.tolist()
    z=0
    newDay = []
    for i in Full_Date:
          e = Full_Date[z]
          date= e[0:10]
          day_name= ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
          day = datetime.datetime.strptime(date,'%Y-%m-%d').weekday()
          newDay.append(day_name[day])
          z=z+1
   
    days = [newDay.count("Saturday"),newDay.count("Friday"),newDay.count("Thursday"),newDay.count("Wednesday"),newDay.count("Tuesday"),newDay.count("Monday"),newDay.count("Sunday")]
    return days
    
def getListMonths(tweets_df_sen):
    Full_Date = tweets_df_sen['date'].values.tolist()
    z=0
    newMon = []
    for i in Full_Date:
          e = Full_Date[z]
          mon= e[5:7]
          newMon.append(mon)
          z=z+1
    print('month', mon)
    months= [newMon.count("12"),newMon.count("11"),newMon.count("10"),newMon.count("09"),newMon.count("08"),newMon.count("07"),newMon.count("06"),newMon.count("05"),newMon.count("04"),newMon.count("03"),newMon.count("02"),newMon.count("01")]      
    return months

def get_sentiment_dic(tweets_df):
    sentiment_df = pd.DataFrame()
    sentiment_df['sentiment'] = [random.randint(-1, 1) for i in range(tweets_df.shape[0])]
    sentiment_count = sentiment_df['sentiment'].value_counts()
    sentiment_dic = {
        'sentiment': [int(sentiment_count[1]), int(sentiment_count[-1]), int(sentiment_count[0])]
    }
    print(sentiment_count)
    return dumps(sentiment_dic)

def create_request(request):
    #takes request and return (Request model) opject
    includeAll = request.POST['or_and']
    rangeOfsearch = request.POST.get('domain', 0)
    keyword = request.POST['keyword']
    time_start = request.POST.get('start_time', None) if request.POST.get('start_time', None) != "" else None
    time_end = request.POST.get('end_time', None) if request.POST.get('end_time', None) != "" else None
    rangeOfsearch = request.POST.get('domain', 0)
    date_time =  timezone.now()

    # Generate a complete keyword
    if len(keyword)==0:
        keyword = "@ALKAHRABA OR @AlkahrabaCare"
    else:
        keywords_list = keyword.split(' ')
        if rangeOfsearch == "0":
            print("i am inside rangeOfsearch == 0")
            if len(keywords_list)<=1:
                keyword = "@ALKAHRABA OR @AlkahrabaCare OR " + keyword
                print("i am inside len(keywords_list)<=1", keywords_list)
            elif includeAll == '1':
                print("i am inside and and", keywords_list)
                keyword = "(@ALKAHRABA OR @AlkahrabaCare) AND "+' AND '.join(keywords_list)
            else:
                print("i am inside or or", keywords_list)
                keyword = "@ALKAHRABA OR @AlkahrabaCare OR "+' OR '.join(keywords_list)
        elif len(keywords_list)==1:
            keyword = keyword
        elif includeAll == '1':
            keyword = ' AND '.join(keywords_list)
        else:
            keyword = ' OR '.join(keywords_list) 
    
    # Verify and automatically correct dates
    period_start = request.POST.get('period_start', None) if request.POST.get('period_start', None) != "" else None #"{{placement.date|date:'Y-m-d' }}"
    if period_start != None: 
        period_start = period_start[6:] + "-" + period_start[:2] + "-" + period_start[3:5]
        period_start_date = datetime.date(int(period_start[0:4]),int(period_start[5:7]),int(period_start[8:]))
        if period_start_date > timezone.now().date():
            period_start = None  

    period_end = request.POST.get('end_period', None)  if request.POST.get('end_period', None) != "" else None
    if period_end != None:
        period_end = period_end[6:] + "-" + period_end[:2] + "-" + period_end[3:5]
        period_end_date = datetime.date(int(period_end[0:4]),int(period_end[5:7]),int(period_end[8:]))
        if (period_start != None and period_end_date  < period_start_date) or period_end_date > timezone.now().date():
            period_end = str(timezone.now().date())
            
    
    print(period_start)
    print(period_end)
    print(rangeOfsearch)
    print(keyword)
    print(includeAll)

    #creat request opject
    req = Request(keyword=keyword, period_start=period_start, period_end=period_end, time_start=time_start, time_end=time_end, rangeOfsearch=rangeOfsearch, date_time=date_time, includeAll=includeAll)

    #Save request opject
    req.save()

    return req