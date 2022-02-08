import os
import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for
import init_db

development = os.environ.get('HEROKU') is None


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config['SECRET_KEY'] = "flyingcircus"

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])


@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()

    if request.method == 'POST':
        url = request.form['url']

        if not url:
            flash('The URL is required!')
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
        flash('Invalid URL')
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

        if not username:
            flash('Please enter username')
        elif not password:
            flash('Please enter password')
        else:
            sign_up_message = 'You have successfully signed up'

            conn = get_db_connection()

            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return render_template('sign_up.html', message=sign_up_message)

    return render_template('sign_up.html')


@app.route('/sign_in', methods=('GET', 'POST'))
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username:
            flash('Please enter username')
        elif not password:
            flash('Please enter password')

        conn = get_db_connection()

        active_user = conn.execute('SELECT username, password FROM users '
                                   'WHERE username = ?', (username,)).fetchone()
        if active_user is not None:
            true_password = active_user['password']
            sign_in_message = 'You have successfully signed in'
            wrong_password_message = 'Wrong password. Please check the data'

            if password == true_password:
                return render_template('sign_in.html', message=sign_in_message)
            else:
                return render_template('sign_in.html', message=wrong_password_message)
        else:
            flash('This user was not found. Please sign up')

    return render_template('sign_in.html')


if development:
    app.run(debug=True)
