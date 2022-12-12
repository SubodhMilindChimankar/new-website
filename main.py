from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
import os
import math
from flask_mail import Mail
from datetime import datetime

with open("config.json","r") as c:
    params=json.load(c)["params"]

local_server = True

app = Flask(__name__)
app.secret_key = 'ItShouldBeAnythingButSecret'
app.config['UPLOAD_FOLDER']=params['upload_location']

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = params['gmail-user']
app.config['MAIL_PASSWORD'] = params['gmail-password']
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)
db.init_app(app)

class Contacts(db.Model):
    """srno	name	email	phone_num	msg	date"""
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)

class Posts(db.Model):

    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    tagline = db.Column(db.String(20), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=False)



@app.route("/")
def home():
    post = Posts.query.filter_by().all()
    last=math.ceil(len(post)/int(params['no_of_posts']))
    page = request.args.get('page')

    if not (str(page).isnumeric()):
        page=1
    page=int(page)
    post = post[(page - 1) * int(params['no_of_posts']):(page - 1) * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page ==1:
        prev="#"
        next="/?page=" + str(page+1)
    if page == last:
        prev= "/?page=" + str(page-1)
        next= "#"
    else:
        prev= "/?page=" + str(page-1)
        next= "/?page=" + str(page+1)

    return render_template('index.html',params=params,post=post,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/dashboard",methods=['GET', 'POST'])
def dashboard():
    if "user" in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params,posts=posts)



    if request.method == 'POST':
        username=request.form.get("username")
        password=request.form.get("password")
        if username == params['admin_user'] and password == params['admin_password']:
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html",params=params,posts=posts)

    else:
        return render_template("login.html", params=params)

@app.route("/edit/<string:srno>" , methods=['GET', 'POST'])
def edit(srno):
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            box_title=request.form.get('title')
            slug=request.form.get('slug')
            tagline=request.form.get('tline')
            image=request.form.get('image')
            content=request.form.get('content')
            date=datetime.now()
            if srno =='0':
                post=Posts(title=box_title,slug=slug,tagline=tagline,img_file=image,content=content,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(srno=srno).first()
                post.title=box_title
                post.slug=slug
                post.tagline=tagline
                post.img_file=image
                post.content=content
                post.date=date
                db.session.commit()
                return redirect('/edit/'+ post)
        post=Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html',params=params,post=post,srno=srno)


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "uploaded successfully"


@app.route('/logout')
def logout():
    session.pop("user")
    return redirect('/dashboard')

@app.route('/delete/<string:srno>',methods=['GET','POST'])
def delete(srno):
    if('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """srno	name	email	phone_num	msg	date"""
    if request.method == "POST":
        name=request.form.get("name")
        email=request.form.get("email")
        phone=request.form.get("phone")
        message=request.form.get("message")
        entry=Contacts(name=name,email=email,phone_num=phone,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()



        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone
                          )


    return render_template('contact.html',params=params)

if __name__ == '__main__':

    app.run(debug=True)