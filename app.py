from msilib.schema import File
from flask import Flask, render_template,flash,redirect,url_for,session,logging,request
from datetime import date
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, FileField,SelectField,validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
# import mysql.connector
from twilio.rest import Client

app=Flask(__name__)

# Connect to the database
# conn = mysql.connector.connect(
#     host='localhost',
#     user='root',
#     password='',
#     database='chat_app'
# )

#config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='chat_app'
app.config['MYSQL_CURSORCLASS']='DictCursor'

#init MySQL
mysql=MySQL(app)

@app.route('/index')
def index():
    return render_template('index.html')

class Login(Form):
    email=StringField('email',[validators.Length(min=5)])
    password=PasswordField('password',[validators.Length(min=5)])

#user login
@app.route('/',methods=['POST','GET'])
def login():    
    form=Login(request.form)
    if request.method=='POST':
        email=request.form['email']
        password_input=request.form['password'] 
        cur=mysql.connection.cursor()
        result=cur.execute("SELECT * FROM messages WHERE username='{emailid}'".format(emailid=email))
        print(result)
        if result>0:
            #get stored hash
            data=cur.fetchone()
            password=data['password']
            #compare passwords
            #if sha256_crypt.verify(password_input,password):
            if password_input==password:
                session['logged_in']=True
                cur.execute("SELECT * FROM messages WHERE username='{emailid}'".format(emailid=email))
                data=cur.fetchone()
                session['username']=data['name']
                session['role']=data['role']
                # if(role=='investor' and data['status']=='no'):
                #     error="Registration not confirmed"
                return redirect(url_for('chat'))
            # else:
            #     error="Invalid Login"
            #     return render_template('login.html',error=error)
            else:
                #app.logger.info('no user')   
                error="Username not found"
                return render_template('login.html',error=error)
    return render_template('login.html')


# Index endpoint (the chat room)
@app.route('/chat')
def chat():
    session['username']='hi'
    # Check if a user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    # Get the messages from the database
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM messages')
    messages = cursor.fetchall()
    print(messages)
    return render_template('chat.html', messages=messages)

# Send message endpoint
@app.route('/send_message', methods=['POST'])
def send_message():
    # Check if a user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))
    # Get the message from the form
    message = request.form['message']
    # Insert the message into the database
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (username, message) VALUES (%s, %s)', (session['username'], message))
    conn.commit()
    return redirect(url_for('chat'))

def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            return redirect(url_for('login')) 
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for('index'))



UPLOAD_FOLDER = 'C:/Users/Admin/Desktop/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/fileupload', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['uploadedfile']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        path=str(app.config['UPLOAD_FOLDER'])+'/'+str(f.filename)
        print(path)
        cur=mysql.connection.cursor()
        res=cur.execute("UPDATE ps SET solution='{path}' WHERE stmt='{name}' ".format(path=path,name=session['psname']))
        res=cur.execute("INSERT INTO solutions(stmt,author,solution,org) VALUES(%s,%s,%s,%s)",(session['psname'],session['name'],path,session['company']))
        res=cur.execute("SELECT * FROM ps")
        projects=cur.fetchall()
        mysql.connection.commit() 
        msg='Solution submitted successfully!'
        return render_template('viewps.html',msg=msg,projects=projects)

        
if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.run(debug=True)