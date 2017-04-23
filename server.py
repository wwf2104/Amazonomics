from flask import Flask, render_template
from jinja2 import Template
import os

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


@app.errorhandler(404)
def error404(error):
  opts = [404]
  options_dict = dict(results = opts)
  return render_template("error.html", **options_dict)
@app.errorhandler(405)
def error405(error):
  opts = [405]
  options_dict = dict(results = opts)
  return render_template("error.html", **options_dict)

industries = ['All','Books','Electronics','Movies and TV','CDs and Vinyl',\
              'Clothing, Shoes and Jewelry','Home and Kitchen',\
              'Kindle Store','Sports and Outdoors','Cell Phones and Accessories',\
              'Health and Personal Care','Toys and Games' ,'Video Games',\
              'Tools and Home Improvement','Beauty','Apps for Android',\
              'Office Products','Pet Supplies','Automotive',\
              'Grocery and Gourmet Food','Patio, Lawn and Garden',\
              'Baby','Digital Music','Musical Instruments','Amazon Instant Video']

@app.route('/', methods = ['GET', 'POST'])
@app.route('/index/', methods = ['GET', 'POST'])
def index():
    options = dict(opts = industries)
    return render_template('index.html', **options)

@app.route('/sentiment/', methods = ['GET', 'POST'])
def sentiment():

    options = dict(opts = [industries])
    return render_template('index.html', **options)



if __name__ == "__main__":
    app.run()