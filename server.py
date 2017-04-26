# coding: utf-8

from flask import Flask, render_template, request
import os
import pandas as pd
import datetime as dt

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

#### ALL ERROR HANDLING ######
@app.errorhandler(500)
def error500(error):
    options = dict(opts = [])
    return render_template("error.html",**options)
@app.errorhandler(404)
def error404(error):
    options = dict(opts = [])
    return render_template("error.html", **options)
@app.errorhandler(405)
def error405(error):
    options = dict(opts = [])
    return render_template("error.html", **options)

##### HOME PAGE ##############
industries = ['All','Books','Electronics','Movies and TV','CDs and Vinyl',\
              'Clothing, Shoes and Jewelry','Home and Kitchen',\
              'Kindle Store','Sports and Outdoors','Cell Phones and Accessories',\
              'Health and Personal Care','Toys and Games' ,'Video Games',\
              'Tools and Home Improvement','Beauty','Apps for Android',\
              'Office Products','Pet Supplies','Automotive',\
              'Grocery and Gourmet Food','Patio, Lawn and Garden',\
              'Baby','Digital Music','Musical Instruments','Amazon Instant Video']

@app.route('/', methods = ['GET','POST'])
def index():
    options = dict(opts = industries)
    return render_template('index.html', **options)


#### MAKE A LIST OF POS AND NEG WORDS
neg_file = open("negative_words.txt")
negatives = list()
for word in neg_file:
    negatives.append(word.strip('\n'))
neg_file.close()

pos_file = open("positive_words.txt")
positives = list()
for word in pos_file:
    positives.append(word.strip('\n'))
pos_file.close()

#### FILES/DATAFRAMES #
def parse(path):
    import gzip
    g = gzip.open(path, 'rb')
    for l in g:
        yield eval(l)

# CONVERT TO DATE OBJECT
def str_dt(s):
    #import datetime as dt
    # s_format = ‘06 2, 2013’
    s = s.split(' ') # [m,d,y]
    s[1] = s[1].strip(',')
    s = dt.date(int(s[2]),int(s[0]),int(s[1]))
    return s

def getDF(path):
    i = 0
    df = {}
    for d in parse(path):
        df[i] = d
        i += 1
    df = pd.DataFrame.from_dict(df, orient='index')
    df['reviewTime'] = df['reviewTime'].apply(lambda x: str_dt(x))
    del df['unixReviewTime']
    return df

# DICT OF DF FOR ALL DEPT
review_dict = dict()
for dept in industries[1:]:
        review_dict[dept] = getDF('reviews_'+dept.replace(' ','_').replace(',','')+'_5.json.gz')

#### CLEANING TEXT ###########
def clean_txt(text):
    text = text.split()
    text = map(lambda x: clean_word(x), text)
    return ' '.join(text)

def clean_word(word):
    word = word.lower()
    for i in range(len(word)):
        if not (word[i].isalpha()) and word[i] != '-' and word[i] != "'":
            word = word[0:i]
            break
    return word

#### GENERATE A WORDCLOUD ####
def generate_wordcloud(df,star):
    from wordcloud import WordCloud, STOPWORDS
    text = ''
    data = df[df['overall']==star]
    data = data[['reviewText']]
    data['reviewText'] = data['reviewText'].apply(lambda x: clean_txt(x))
    for review in data.iteritems():
            words = str(review).split()
            for word in words:
                if word in negatives or word in positives:
                    text = text + " " + word
    wordcloud = WordCloud(stopwords=STOPWORDS, background_color='white',width=1200,
                          height=1000,max_words=20).generate(text)
    return wordcloud

#### Vader compound score, input is a single review, to be applied as lambda
def vader_compound(review):
    from nltk import sent_tokenize
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    sentences = sent_tokenize(review)
    compound = 0
    for sentence in sentences:
        vs = analyzer.polarity_scores(sentence)
        compound+=vs['compound']/(len(sentences))
    return compound

##### EMOTION ANALYSIS ########
def get_nrc_data():
    nrc = "NRC-emotion-lexicon-wordlevel-alphabetized-v0.92.txt"
    count=0
    emotion_dict=dict()
    with open(nrc,'r') as f:
        for line in f:
            if count < 46:
                count+=1
                continue
            line = line.strip().split('\t')
            if int(line[2]) == 1:
                if emotion_dict.get(line[0]):
                    emotion_dict[line[0]].append(line[1])
                else:
                    emotion_dict[line[0]] = [line[1]]
    return emotion_dict

emotion_dict = get_nrc_data()
#where text is a single Amazon review
def emotion_analyzer(text,emotion_dict=emotion_dict):
    #Set up the result dictionary
    emotions = {x for y in emotion_dict.values() for x in y}
    emotion_count = dict()
    for emotion in emotions:
        emotion_count[emotion] = 0
    #Analyze the text and normalize by total number of words
    for word in text.split():
        if emotion_dict.get(word):
            for emotion in emotion_dict.get(word):
                emotion_count[emotion] += 1/len(text.split())
    return emotion_count

def sentiment_analysis(rating, df, fname):
    import matplotlib.pyplot as plt
    data = df[df['overall']==rating]
    rows = data['reviewTime'].count()
    data['year'] = data['reviewTime'].apply(lambda x: x.year)
    if rows < 5000:
        data['sentiment'] = data['reviewText'].apply(lambda x: vader_compound(x))
        data.groupby('year')['sentiment'].mean().plot(kind='bar')
        plt.savefig(fname)
    else:
        years = data['year'].unique()
        frame = list()
        for year in years:
            init = dt.date(year, 1, 1)
            end = dt.date(year, 12,31)
            mask = (df['reviewTime'] > init) & (df['reviewTime'] <= end)
            new = df[mask]
            if (new['reviewTime'].count() < 5000/len(years)):
                frame.append(new.iloc[0:100])
            else:
                 frame.append(new.iloc[0:int(5000/len(years))])
        result = pd.concat(frame)

        result['sentiment'] = result['reviewText'].apply(lambda x: vader_compound(x))
        result['year'] = result['reviewTime'].apply(lambda x: x.year)
        result.groupby('year')['sentiment'].mean().plot(kind='bar')
        plt.savefig(fname)

# returns dictionary with keys as (year,quarter) tuples and values as
# count of reviews in that quarter
def review_count(df):
    result_dict = {}
    quarter_dict = {1:1, 2:1, 3:1, 4:2, 5:2, 6:2, 7:3, 8:3, 9:3, 10:4, 11:4, 12:4}
    for i in range(len(df)):
        quarter = quarter_dict[df['reviewTime'].iloc[i].month]
        year = df['reviewTime'].iloc[i].year
        if (year,quarter) in result_dict:
            result_dict[(year,quarter)] += 1
        else:
            result_dict[(year,quarter)] = 1
    return result_dict

##### plots review counts per quarter using result count above
def plot_review_count(review_counts, fname):
    import matplotlib.pyplot as plt
    x = list()
    labels = list()
    y = list()
    i = 1
    for key in review_counts:
        x.append(i)
        labels.append(key)
        i += 1
    labels.sort()
    for label in labels:
        y.append(review_counts[label])
    plt.clf()
    plt.plot(x, y)
    plt.xticks(x, labels, rotation='vertical')
    plt.savefig(fname)

# returns dictionary with keys as (year,quarter) tuples and values as
# average of review ratings in that quarter - needs the review_count result to work
def review_average(df, review_counts):
    result_dict = {}
    quarter_dict = {1:1, 2:1, 3:1, 4:2, 5:2, 6:2, 7:3, 8:3, 9:3, 10:4, 11:4, 12:4}
    for i in range(len(df)):
        quarter = quarter_dict[df['reviewTime'].iloc[i].month]
        year = df['reviewTime'].iloc[i].year
        if (year,quarter) in result_dict:
            result_dict[(year,quarter)] += int(df['overall'].iloc[i])
        else:
            result_dict[(year,quarter)] = int(df['overall'].iloc[i])
    for key in result_dict:
        result_dict[key] = result_dict[key]/review_counts[key]
    return result_dict

#### plots review averages over quarters
def plot_review_avg(review_avg,fname):
    import matplotlib.pyplot as plt
    x = list()
    labels = list()
    y = list()
    i = 1
    for key in review_avg:
        x.append(i)
        labels.append(key)
        i += 1
    labels.sort()
    for label in labels:
        y.append(review_avg[label])
    plt.clf()
    plt.plot(x, y)
    plt.xticks(x, labels, rotation='vertical')
    plt.savefig(fname)


#### Results Pages ###########
@app.route('/results/sent/', methods = ['POST'])
def sentiment():
    from wordcloud import WordCloud
    dept = request.form["dept"]
    rating = request.form["rating"]
    fnames = list()
    if dept != "All":
        if not os.path.exists("static/"+dept+rating+".png"):
            generate_wordcloud(review_dict[dept],float(rating)).to_file("static/"+dept+rating+".png")
        fnames.append("static/"+dept+rating+".png")
    else: # dept==All
        for d in review_dict:
            if not os.path.exists("static/"+d+rating+".png"):
                generate_wordcloud(review_dict[d],float(rating)).to_file("static/"+d+rating+".png")
            fnames.append("static/"+d+rating+".png")

    options = dict(opts = fnames)
    return render_template('results.html', **options)

@app.route('/results/emot/', methods = ['POST'])
def emot():
    rating = request.form["rating"]
    dept = request.form["dept"]
    if not os.path.exists("static/"+dept+str(rating)+"_vader.png"):
        sentiment_analysis(float(rating), review_dict[dept],"static/"+dept+str(rating)+"_vader.png")
    options = dict(opts = ["static/"+dept+str(rating)+"_vader.png"])
    return render_template('results.html', **options)

@app.route('/results/quart/', methods = ['POST'])
def quarters():
    time_span = request.form["time_span"]
    dept = request.form["dept"]
    df = review_dict[dept]
    if time_span == "count":
        if not os.path.exists("static/"+dept+"_review_count.png"):
            plot_review_count(review_count(df),"static/"+dept+"review_count.png")
        options = dict(opts = ["static/"+dept+"_review_count.png"])
    else: # time_span == "avg"
        if not os.path.exists("static/"+dept+"_avg_review.png"):
            plot_review_avg(review_average(df,review_count(df)),"static/"+dept+"review_count.png")
        options = dict(opts = ["static/"+dept+"_avg_review.png"])
    return render_template('results.html', **options)

#### RUN CODE ################
if __name__ == "__main__":
    app.run()