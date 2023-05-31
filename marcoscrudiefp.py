from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import requests
from bs4 import BeautifulSoup
import string
import feedparser
import json

app = Flask(__name__)
app.secret_key = 'tauriloca'

app.config["MYSQL_USER"] = "silvanoo_3025"
app.config["MYSQL_PASSWORD"] = "WY8K002!WY2j"
app.config["MYSQL_DB"] = "silvanoo_teste"
app.config["MYSQL_HOST"] = "pt-mysql.fastsync.link"

mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        # Create variables for easy access
        email = request.form['email']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT * FROM user WHERE email = '{email}' AND password = '{password}'")
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['userid']
            session['username'] = account['name']
            session['is_admin'] = account['is_user_admin']
            print(account['is_user_admin'])
            return redirect(url_for('admin' if account['is_user_admin'] else 'user'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Credenciais incorretas!'
    # Show the login form with message (if any)
    return render_template('login.html',  msg=msg)


@app.route('/admin')
def admin():
    if 'id' in session and session['is_admin']:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user")
        data = cur.fetchall()
        cur.close()
        return render_template('admin.html', accounts=data )
    else:
        return redirect(url_for('login'))


@app.route('/user')
def user():
    if 'id' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user")
        data = cur.fetchall()
        cur.close()
        return render_template('user.html', users=data)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))


@app.route('/insert', methods = ['POST'])
def insert():
    if request.method == "POST":
        flash("Data Inserted Successfully")
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        is_admin = True
        try:
            is_admin = request.form['is_admin']
        except:
            is_admin = False
        cur = mysql.connection.cursor()
        cur.execute(f"INSERT INTO user (name, password, email, is_user_admin) VALUES ('{username}', '{password}', '{email}', {is_admin})")
        mysql.connection.commit()
        return redirect(url_for('admin'))


@app.route('/register', methods = ['GET','POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'nome' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['nome']
        password = request.form['password']
        email = request.form['email']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute(f"SELECT * FROM user WHERE email = '{email}'")
        account = cur.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Email já registado!'
        elif not username or not password or not email:
            msg = 'Preencha todos os dados!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cur.execute(f"INSERT INTO user (name, password, email) VALUES ('{username}', '{password}', '{email}')")
            mysql.connection.commit()
            msg = 'Conta criada com sucesso!!'
            return render_template('login.html', msg=msg )
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Preencha todos os campos!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)


@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Registo apagado com sucesso!")
    cur = mysql.connection.cursor()
    cur.execute(f"DELETE FROM user WHERE userid = '{id_data}'")
    mysql.connection.commit()
    return redirect(url_for('admin'))


@app.route('/update',methods=['POST','GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        is_admin = True
        try:
            is_admin = request.form['is_admin']
        except:
            is_admin = False
        cur = mysql.connection.cursor()
        cur.execute(f"""
                    UPDATE user
                    SET name = '{username}', password = '{password}', email = '{email}', is_user_admin = {is_admin}
                    WHERE userid = '{id_data}'
                    """)
        flash("Dados actualizados com sucesso!")
        mysql.connection.commit()
        return redirect(url_for('admin'))


# API key openweathermap
API_KEY =  '02ce3117223858290ecc99b227f0577d'
# Coordinates
LANG = 'pt'
weather_data = []
@app.route('/temperatura', methods=['GET', 'POST'])
def temperatura():
    if request.method == 'POST':
        err_msg = ''
        new_city = request.form.get('city')
        new_city = new_city.lower()
        new_city = string.capwords(new_city)

        link = f"https://api.openweathermap.org/data/2.5/weather?q={new_city}&lang={LANG}&appid={API_KEY}&units=metric"
        r = requests.get(link).json()
        if r['cod'] == 200:
            weather = {
                'city' : r["name"],
                'temperature' : r['main']['temp'],
                'description' : r['weather'][0]['description'],
                'icon' : r['weather'][0]['icon'],
            }
            weather_data.append(weather)
        else:
            err_msg = 'Esta cidade não é válida!'
        
        if err_msg:
            flash(err_msg, 'error')
        else:
            flash('Cidade adicionada com sucesso!', 'successo')

    return render_template('temperatura.html', weather_data=weather_data)


@app.route('/deletecity/<name>')
def delete_city( name ):
    #Apagar do arraylist
    for i in range(len(weather_data)):
        if weather_data[i]['city'] == name:
            del weather_data[i]
            break

    flash(f'Removido dados de {name}!', 'success')
    return redirect(url_for('temperatura'))


@app.route('/news', methods=['POST','GET'])
def news_rss():
    not_ao_min = "https://www.noticiasaominuto.com/rss/ultima-hora"
    feed = feedparser.parse(not_ao_min)
    noticias = feed.entries

    return render_template('news.html', noticias=noticias)


@app.route('/chuck', methods=['POST','GET'])
def chuck():
    api_url = 'https://api.api-ninjas.com/v1/chucknorris?'
    response = requests.get(api_url, headers={'X-Api-Key': 'KDkDKcI5irXxwcgsFSvtpA==w6f7bhlmW4ZhQqfc'}).json()
    return render_template('chuck.html', chuck=response)



if __name__ == "__main__":
    app.run(debug=True)
