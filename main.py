import os
import pathlib

import requests
from flask import Flask, session, abort, redirect, request, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

import numpy as np
import sqlite3 as sql
from flask_session import Session
from tempfile import mkdtemp
import json
import time

#RUN THIS CODE ONCE WHEN INITIALIZING THE WEB APP FOR DATABASE CREATION
#If it doesn't work clear everything from the database.db file and try again
#======================================================================
#conn = sql.connect('database.db')
#print("Opened database successfully");

#conn.execute('CREATE TABLE users (username TEXT, email TEXT, password TEXT, distance TEXT)')
#print("Table created successfully");
#conn.close()
#======================================================================

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "645826919583-lsvpsf9rjr09mo59cf4ji90d58i7328k.apps.googleusercontent.com"
client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email", "openid"
    ],
    redirect_uri=
    "https://Competitive-Cycling-Website.arnavkumar13.repl.co/callback")


def findPercentile(myRank, total):
  myRank += 1
  percentile = (total-myRank)/total*100
  percentile = round(percentile,0)
  percentile = int(percentile)
  return percentile

@app.route('/stall')
def stall():
  time.sleep(1.5)
  return redirect('/')

@app.route('/')
def index():
  if session.get('user') is None:
    return redirect('/loginn')

  with sql.connect("database.db") as con:
    cur = con.cursor()
    username = session.get('user')
    rows = cur.execute("SELECT * FROM users WHERE username=?",(username,) )
    rows = rows.fetchall()
    name = rows[0][0]
    distance = rows[0][3]

    bests = cur.execute("SELECT username, distance FROM users ORDER BY distance DESC")
    bests = bests.fetchall()
    print(bests)
    lengthList = len(bests)
    print(lengthList)
    #select column_name from table_name order by column_name desc limit 
    con.commit()

    myRank = 0

    for i in range(len(bests)):
      print(".")
      print(bests[i][0])
      print(".")
      if bests[i][0] == username:
        break
      else:
        myRank += 1

    my_name_distance = bests[myRank]

    percentile = findPercentile(myRank, lengthList)
    
  return render_template('index.html', name=name, distance=distance, bests=bests, lengthList=lengthList, myRank = myRank, my_name_distance=my_name_distance, percentile=percentile)

  
@app.route('/tracking', methods=["POST", "GET"])
def tracking():
  if session.get('user') is None:
    return redirect('/loginn')
  return render_template('tracking.html')


@app.route("/loginn", methods=["POST", "GET"])
def loginn():

  session.clear()
  
  if request.method == "POST":
    username = request.form['username']
    password = request.form['password']

    with sql.connect("database.db") as con:
      cur = con.cursor()
      
      rows = cur.execute("SELECT * FROM users WHERE username=?",(username,))
      rows = rows.fetchall()
      if len(rows) != 1:
        return redirect('/loginn')
      if password != rows[0][2]:
        return redirect('loginn')
        
      session["user"] = username
      return redirect("/")
      con.commit()
    
  return render_template('login.html')


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
  
    if not session["state"] == request.args["state"]:
      abort(500)  # State does not match!
    
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
      id_token=credentials._id_token,
      request=token_request,
      audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")   
    session["user"] = id_info.get("name")   
  
    username = id_info.get("name") 
    print("HERE")
    print("HERE")
    print(username)
    print("HERE")
    print("HERE")
    password = id_info.get("sub")
  
    with sql.connect("database.db") as con:
      cur = con.cursor()
      
      rows = cur.execute("SELECT * FROM users WHERE username=?",(username,))
      rows = rows.fetchall()
      if len(rows) != 1:
        with sql.connect("database.db") as con:
              cur = con.cursor()
              #makes sure no same emails are registered
              rows = cur.execute("SELECT * FROM users WHERE password=?",(password,))
              if len(rows.fetchall()) != 0:        
                return redirect("/register")
              distance = 0.00
              cur.execute("INSERT INTO users (username,email,password,distance) VALUES (?,?,?,?)",(username,"placeholder",password,distance))
              con.commit()
              return redirect("/")
      else:
        return redirect("/")
        


      
        
      session["user"] = username
      return redirect("/")
      con.commit()
    
    return redirect("/protected_area")
  



@app.route("/register", methods=["POST", "GET"])
def register():

  session.clear()
  
  if request.method == "POST":
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    distance = 0.00

    with sql.connect("database.db") as con:
      cur = con.cursor()

      #makes sure no same usernames are registed
      rows = cur.execute("SELECT * FROM users WHERE username=?",(username,) )
      if len(rows.fetchall()) != 0:        
        return redirect("/register")
      #makes sure no same emails are registered
      rows = cur.execute("SELECT * FROM users WHERE email=?",(email,) )
      if len(rows.fetchall()) != 0:        
        return redirect("/register")
        
      cur.execute("INSERT INTO users (username,email,password,distance) VALUES (?,?,?,?)",(username,email,password,distance))
      con.commit()
    session["user"] = username
    return redirect("/")
    
  return render_template("register.html")





@app.route('/processUserInfo/<string:userInfo>', methods=['POST'])
def processUserInfo(userInfo):
  userInfo = json.loads(userInfo)
  print("")
  print('USER INFO RECIEVED')
  print(f"User Distance: {userInfo['distance']}")

  with sql.connect("database.db") as con:
    cur = con.cursor()
    username = session.get('user')
    currentDistance = cur.execute("SELECT * FROM users WHERE username=?",(username,))
    currentDistance = currentDistance.fetchall()
    currentDistance = currentDistance[0][3]
    
    finalDistance = float(userInfo['distance']) + float(currentDistance)
    cur.execute("UPDATE users SET distance=? WHERE username=?",(finalDistance,username,) )
    print("HEREEE")
    print("HEREEE")
    print("HEREEE")
    print("HEREEE")
    print("ok here now")
    return redirect("/")
    print("ok here now")
    con.commit()
  return redirect("/")


@app.route("/protected_area")
def protected_area():
    return redirect("/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8080', debug=True)