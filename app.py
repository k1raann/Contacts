from cmath import inf
from flask import Flask, redirect, render_template, request, jsonify, url_for
import redis
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
import datetime
import ast

app = Flask(__name__)
cur = redis.Redis(host = '127.0.0.1', port = 6379, db = 0, password = '')
dataset = 'FormData'

app.config['SECRET_KEY'] = 'abc12'

class userForm(Form):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    place = StringField("Place", validators=[DataRequired()])
    submit = SubmitField("Submit")

@app.route('/')
def index():
   return render_template("index.html")
   
@app.route('/write', methods = ['GET','POST'])
def write():
   form = userForm()
   if request.method == 'POST' :
      score = cur.zcount(dataset, '-inf', 'inf') + 1
      formdata = {"id" : str(score), "first_name" : request.form["first_name"], "last_name" : request.form["last_name"], "place" : request.form["place"], "timestamp" : str(datetime.datetime.now())}
      data = str(formdata)
      cur.zadd(dataset, {data : score})
   return render_template('userform.html', form = form)

@app.route('/display_all', methods = ['GET'])
def display_all():
   curData = cur.zrange(dataset, 0, -1)
   data = []
   if len(curData) == 0:
      return render_template('display.html', errmsg = 1, data = data)
   else:
      for sample in curData:
         str = sample.decode("UTF-8")
         dict = ast.literal_eval(str)
         data.append(dict)
      return render_template('display.html', data = data)

@app.route('/delete_all')
def delete_all():
   cur.zremrangebyrank(dataset, 0, -1)
   return 'Successfully deleted all the data!'

@app.route('/update/<int:score>', methods = ['GET','POST'])
def updateByScore(score):
   setToUpdate = cur.zrangebyscore(dataset, score, score)
   listString = setToUpdate[0].decode("UTF-8")
   dictToUpdate = ast.literal_eval(listString)
   form = userForm()
   form.first_name.data = dictToUpdate["first_name"]
   form.last_name.data = dictToUpdate["last_name"]
   form.place.data = dictToUpdate["place"]
   if request.method == 'POST' :
      cur.zremrangebyscore(dataset, score, score)
      formdata = {'id' : score, 'first_name' : request.form["first_name"], "last_name" : request.form["last_name"], "place" : request.form["place"], "timestamp" : str(datetime.datetime.now())}
      data = str(formdata)
      cur.zadd(dataset, {data : score})
      form = userForm()
      return redirect(url_for('display_all'))
   return render_template('userform.html', form = form)

@app.route('/delete/<int:score>')
def deleteByScore(score):
   cur.zremrangebyscore(dataset, score, score)
   i = score+1
   updateScore = cur.zrangebyscore(dataset, i, inf)
   for sample in updateScore:
      strList = sample.decode("UTF-8")
      dict = ast.literal_eval(strList)
      formdata = {'id' : i-1, 'first_name' : dict["first_name"], "last_name" : dict["last_name"], "place" : dict["place"], "timestamp" : dict["timestamp"]}
      data = str(formdata)
      cur.zremrangebyscore(dataset, i, i)
      cur.zadd(dataset, {data : i-1})
      i=i+1
   return redirect(url_for('display_all'))

if __name__ == '__main__':
   app.run(debug = True)