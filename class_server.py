# coding: utf-8

from flask import Flask, render_template, request
import os

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

#### Results Pages ###########
@app.route('/results/sent/', methods = ['POST'])
def sentiment():
    dept = request.form["dept"]
    rating = request.form["rating"]
    fnames = list()
    if dept != "All":
        fnames = ["static/"+dept+str(rating)+".png"]
    else: # dept==All
        for d in industries:
            fnames.append("static/"+d+rating+".png")

    options = dict(opts = fnames)
    return render_template('results.html', **options)

@app.route('/results/emot/', methods = ['POST'])
def emot():
    rating = request.form["rating"]
    dept = request.form["dept"]
    options = dict(opts = ["static/"+dept+str(rating)+"_vader.png"])
    return render_template('results.html', **options)

@app.route('/results/quart/', methods = ['POST'])
def quarters():
    time_span = request.form["time_span"]
    dept = request.form["dept"]
    if time_span == "count":
        options = dict(opts = ["static/"+dept+"_review_count.png"])
    else: # time_span == "avg"
        options = dict(opts = ["static/"+dept+"_avg_review.png"])
    return render_template('results.html', **options)

#### RUN CODE ################
if __name__ == "__main__":
    app.run()