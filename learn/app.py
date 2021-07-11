from flask import Flask,render_template,request,session,redirect,url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import KNeighborsClassifier
app=Flask(__name__)
local_server=True

model = pickle.load(open(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\locationpluscrop.pkl', 'rb'))
modelnew = pickle.load(open(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\finalmodelnewcolumn.pkl', 'rb'))
cityfile = pd.read_csv(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\Ploted_600.csv')
mapper = pd.read_csv(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\Mapping_code_crop.csv')
mappernew = pd.read_csv(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\mapping_code_crop_predict.csv')
data = pd.read_csv(r'C:\Users\PUTUL SIDDHARTH\Desktop\learn\Crop.csv')

with open(r"C:\Users\PUTUL SIDDHARTH\Desktop\learn\first.json","r") as c:
    params=json.load(c)['params']



if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']=r'C:\Users\PUTUL SIDDHARTH\Desktop\learn'
app.secret_key='super-secret-key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'putul'
app.config['MYSQL_DB'] = 'codingthunder'


mysql = MySQL(app)


@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = None
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = % s AND password = % s', (email, password, ))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['email'] = account['email']
            msg = 'Logged in successfully !'
            posts=Posts.query.filter_by().all()
            return render_template('index.html', params=params, posts=posts, msg = msg)
        else:
            msg = 'Incorrect email / password !'
    return render_template('login.html', msg = msg, params=params)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)




@app.route("/dashboard", methods =['GET', 'POST'])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method=="POST":
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username==params['admin_user'] and userpass==params['admin_password']:
            # set the session variable
            session['user']=username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    else:
        return render_template("adminLogin.html", params=params)

@app.route("/plotDash", methods =['GET', 'POST'])
def plotDash():
    if "user" in session and session['user']==params['admin_user']:
        plots = Plots.query.all()
        return render_template("plotDash.html", params=params, plots=plots)
    plots = Plots.query.all()
    return render_template("plotDash.html", params=params, plots=plots)

@app.route('/adminlogout')
def adminlogout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    if "user" in session and session['user']==params['admin_user']:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/plotDelete/<string:sno>" , methods=['GET', 'POST'])
def plotDelete(sno):
    if "user" in session and session['user']==params['admin_user']:
        plot=Plots.query.filter_by(sno=sno).first()
        db.session.delete(plot)
        db.session.commit()
    return redirect('/plotDash')

@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session and session['user']==params['admin_user']:
        if request.method=="POST":
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
        
            if sno=='0':
                post = Posts(title=box_title, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+sno)

    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)





db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    phone_num = db.Column(db.String(120), unique=True)
    msg = db.Column(db.String(120), unique=True)
    date = db.Column(db.String(120), unique=True, nullable=True)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True)
    content = db.Column(db.String(120), unique=True)
    date = db.Column(db.String(120), unique=True, nullable=True)
    slug = db.Column(db.String(120), unique=True)
    img_file=db.Column(db.String(120), unique=True)
    
class Plots(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(80), unique=True)
    owner = db.Column(db.String(120), unique=True)
    address = db.Column(db.String(120), unique=True)
    description = db.Column(db.String(120), unique=True)
    mobile=db.Column(db.String(120), unique=True)
    date = db.Column(db.String(120), unique=True, nullable=True)

@app.route("/")
def home():
    posts=Posts.query.filter_by().all()
    return render_template("index.html",params=params,posts=posts)

@app.route("/more")
def more():
    plots=Plots.query.filter_by().all()
    return render_template("information.html", params=params,plots=plots)

@app.route("/loan")
def loan():
    return render_template("loan.html", params=params)

@app.route("/info" , methods=['GET', 'POST'])
def info():
    if request.method=="POST":
        crop = request.form.get("crop_name")
        if crop.lower()=="pistachio nuts":
            return render_template("pista.html", params=params)
        if crop.lower()=="coffee":
            return render_template("coffee.html", params=params)
    return render_template("cropinfo.html", params=params)

@app.route('/predictnow')
def predictnow():
    return render_template('index1.html',params=params)

@app.route('/recommendnow')
def recommendnow():
    return render_template('crop_prediction1.html',params=params)

@app.route("/predict",methods=['GET','POST'])
def predict():
    int_features = [float(x) for x in request.form.values()]
    final_features = [np.array(int_features)]
    print(final_features)
    prediction = modelnew.predict(final_features)
    #cropvalue=mappernew['Crop'][int(prediction)]
    return render_template('index1.html', params=params,prediction_text='Predicted crop is  : {}'.format(prediction))

@app.route("/recommend",methods=['GET','POST'])
def recommend():

    y = data.loc[:,'Crop']
    labelEncoder_y = LabelEncoder()
    y = labelEncoder_y.fit_transform(y)

    data['crop_num'] = y
    X = data.loc[:,['N','P','K','pH']].astype(float)
    y = data.loc[:,'crop_num']

    clf = KNeighborsClassifier(n_jobs=10, n_neighbors=10,weights='distance')
    clf.fit(X,y)

    if request.method == 'POST':
        city_name = request.form['city']
        N = request.form['Nitrogen']
        P = request.form['Phosphorous']
        K = request.form['Potassium']
        pH = request.form['pH']



        if len(city_name) != 0:
            print(city_name)

            npk = cityfile[cityfile['Location'] == city_name]

            val = []
            for index, row in npk.iterrows():
                val = [row['N'],row['P'],row['K'],row['pH']]
            print(val)
            columns = ['N','P','K','pH']
            values = np.array([val[0],val[1],val[2],val[3]])
            pred = pd.DataFrame(values.reshape(-1, len(values)),columns=columns)

            prediction = clf.predict(pred)
            # distances, indices = clf.kneighbors(pred,  n_neighbors=10)
            # prediction
            real_pred = clf.predict_proba(pred)
            print(real_pred)

            lst = []
            for i in range(101):
                if real_pred[0][i] != 0.0:
                    lst.append(i)

            lt= []
            for i in range(10):

                load_data = data[data.index == lst[i]]
                for index, row in load_data.iterrows():
                    lt.append(row['Crop'])

        else:
            print(N,P,K,pH)
            columns = ['N','P','K','pH']
            values = np.array([N,P,K,pH])
            pred = pd.DataFrame(values.reshape(-1, len(values)),columns=columns)
            print("hello")


            prediction = clf.predict(pred)
            print(prediction)
            # distances, indices = clf.kneighbors(pred,  n_neighbors=10)
            # prediction
            real_pred = clf.predict_proba(pred)
            print(real_pred)

            lst = []
            for i in range(101):
                if real_pred[0][i] != 0.0:
                    lst.append(i)

            lt= []
            print(lst)
            for i in range(len(lst)):
                load_data = data[data.index == lst[i]]
                for index, row in load_data.iterrows():
                    lt.append(row['Crop'])

    return render_template('crop_prediction1.html',crops=lt,crop_num = len(lt),display=True,params=params)


@app.route("/about")
def about():
    return render_template("about.html",params=params)



@app.route("/post")
def post12():
    return render_template("post1.html",params=params)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html",params=params,post=post)


@app.route("/contact",methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        name=request.form.get('name1')
        email=request.form.get('email1')
        phone=request.form.get('phone1')
        message=request.form.get('message1')

        entry=Contacts(name=name,email=email,phone_num=phone,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        
        
    return render_template("contact.html", params=params)

@app.route("/plot",methods=['GET','POST'])
def plot():
    if(request.method=='POST'):
        topic=request.form.get('topic1')
        owner=request.form.get('owner1')
        address=request.form.get('address1')
        description=request.form.get('description1')
        mobile=request.form.get('mobile1')

        entry=Plots(topic=topic,owner=owner,address=address,description=description,mobile=mobile,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        
        
    return render_template("plot.html", params=params)

if __name__ == "__main__":
    app.run(port=9023,debug=True)