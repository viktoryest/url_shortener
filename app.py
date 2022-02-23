import os
import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user
from werkzeug.security import generate_password_hash, check_password_hash
import init_db
from user_class import UserLogin

development = os.environ.get('HEROKU') is None


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager(app)

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().get_from_db(user_id, get_db_connection())


@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()

    if request.method == 'POST':
        url = request.form['url']

        if not url:
            flash('The URL is required!', category='danger')
            return redirect(url_for('index'))

        url_data = conn.execute('INSERT INTO urls (original_url) VALUES (?)',
                                (url,))
        conn.commit()
        conn.close()

        url_id = url_data.lastrowid
        hash_id = hashids.encode(url_id)
        short_url = request.host_url + hash_id

        return render_template('index.html', short_url=short_url)

    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/<id>')
def url_redirect(id):
    conn = get_db_connection()

    original_id = hashids.decode(id)
    if original_id:
        original_id = original_id[0]
        url_data = conn.execute('SELECT original_url, clicks FROM urls'
                                ' WHERE id = (?)', (original_id,)
                                ).fetchone()
        original_url = url_data['original_url']
        clicks = url_data['clicks']

        conn.execute('UPDATE urls SET clicks = ? WHERE id = ?',
                     (clicks + 1, original_id))

        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        flash('Invalid URL', category='danger')
        return redirect(url_for('index'))


@app.route('/stats')
def stats():
    conn = get_db_connection()
    db_urls = conn.execute('SELECT id, created, original_url, clicks FROM urls').fetchall()
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        url['short_url'] = request.host_url + hashids.encode(url['id'])
        urls.append(url)

    return render_template('stats.html', urls=urls)


@app.route('/sign_up', methods=('GET', 'POST'))
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        psw_hash = generate_password_hash(password)

        if not username:
            flash('Please enter username', category='info')
        elif not password:
            flash('Please enter password', category='info')
        else:
            try:
                conn = get_db_connection()

                unique_users_count = conn.execute(f"SELECT COUNT() as `count` FROM users WHERE "
                                                  f"username LIKE '{username}'").fetchone()['count']
                if unique_users_count > 0:
                    flash('Sorry, a user with this name already exists', category='danger')
                else:
                    conn.execute('INSERT INTO users (username, psw_hash) VALUES (?, ?)', (username, psw_hash))
                    user = conn.execute(f"SELECT * FROM users WHERE username = '{username}' LIMIT 1").fetchone()
                    userlogin = UserLogin().create(user)
                    rm = True if request.form.get('remember-me') else False
                    login_user(userlogin, remember=rm)
                    conn.commit()
                    conn.close()
                    flash('You have successfully signed up', category='success')
            except Exception:
                flash('Database read error', category='danger')

    return render_template('sign_up.html')


@app.route('/sign_in', methods=('GET', 'POST'))
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username:
            flash('Please enter username', category='info')
        elif not password:
            flash('Please enter password', category='info')

        conn = get_db_connection()

        active_user = conn.execute('SELECT username, psw_hash FROM users '
                                   'WHERE username = ?', (username,)).fetchone()

        if active_user is not None:
            true_psw_hash = active_user['psw_hash']

            if check_password_hash(true_psw_hash, password):
                flash('You have successfully signed in', category='success')
            else:
                flash('Wrong password. Please check the data', category='danger')
        else:
            flash('This user was not found. Please sign up', category='danger')

    return render_template('sign_in.html')


if development:
    app.run(debug=True)
