import os
import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_required, logout_user
import init_db
from user_class import UserLogin
from make_url_list import make_url_list
from url_shorting_handler import get_short_url
from url_redirect_handler import get_redirect_url
from sign_up_handler import check_sign_up
from sign_in_handler import check_sign_in

development = os.environ.get('HEROKU') is None


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager(app)
login_manager.login_view = 'unauthorized_user'

hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().get_from_db(user_id, get_db_connection())


@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()
    if conn.execute('SELECT id FROM users WHERE id = 1').fetchone() is None:
        logout_user()

    if request.method == 'POST':
        url = request.form['url']
        short_url_name = request.form['short_url_name']

        short_url = get_short_url(get_db_connection(), hashids, url, short_url_name)
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/<id>')
def url_redirect(id):
    return get_redirect_url(get_db_connection(), hashids, id)


@app.route('/stats')
@login_required
def stats():
    conn = get_db_connection()
    db_urls = conn.execute('SELECT id, created, original_url, clicks, short_url_name FROM urls').fetchall()
    conn.close()

    urls = make_url_list(db_urls, hashids)

    return render_template('stats.html', urls=urls)


@app.route('/my_profile', methods=['GET', 'POST'])
@login_required
def my_profile():
    conn = get_db_connection()
    db_urls = conn.execute(f'SELECT id, created, original_url, short_url_name,'
                           f'clicks FROM urls WHERE user_id = "{current_user.get_id()}"').fetchall()
    conn.close()

    my_urls = make_url_list(db_urls, hashids)

    if request.method == 'POST':
        logout_user()
        flash('You have successfully logged out', category='success')
        return redirect(url_for('sign_in'))

    return render_template('my_profile.html', my_urls=my_urls)


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    check_sign_up(get_db_connection())
    return render_template('sign_up.html')


@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    check_sign_in(get_db_connection())
    return render_template('sign_in.html')


@app.route('/unauthorized_user')
def unauthorized_user():
    return render_template('unauthorized_user.html')


if development:
    app.run(debug=True)
