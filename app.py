import os
import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import init_db
from user_class import UserLogin
from make_url_list import make_url_list

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

        if not url:
            flash('The URL is required!', category='danger')
            return redirect(url_for('index'))

        if short_url_name:
            used_name = conn.execute(f'SELECT short_url_name FROM urls WHERE short_url_name = (?)',
                                     (short_url_name,)).fetchone()
            if used_name is None:
                if current_user.is_authenticated:
                    conn.execute('INSERT INTO urls (original_url, user_id, short_url_name) VALUES (?, ?, ?)',
                                 (url, current_user.get_id(), short_url_name))
                else:
                    conn.execute('INSERT INTO urls (original_url, user_id, short_url_name) VALUES (?, ?, ?)',
                                 (url, 0, short_url_name))
            else:
                flash('This short URL name is already in use. Please, choose another one', category='info')

            conn.commit()
            conn.close()

            short_url = request.host_url + short_url_name

        else:
            if current_user.is_authenticated:
                url_data = conn.execute('INSERT INTO urls (original_url, user_id, short_url_name) VALUES (?, ?, ?)',
                                        (url, current_user.get_id(), 0))
            else:
                url_data = conn.execute('INSERT INTO urls (original_url, user_id, short_url_name) VALUES (?, ?, ?)',
                                        (url, 0, 0))

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

    short_url_name = conn.execute('SELECT original_url, short_url_name FROM urls'
                                  ' WHERE short_url_name = (?)', (id,)).fetchone()

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

    elif short_url_name:
        short_url_name = short_url_name['short_url_name']
        url_data = conn.execute('SELECT short_url_name, original_url, clicks FROM urls'
                                ' WHERE short_url_name = (?)', (short_url_name,)
                                ).fetchone()
        original_url = url_data['original_url']
        clicks = url_data['clicks']

        conn.execute('UPDATE urls SET clicks = ? WHERE short_url_name = ?',
                     (clicks + 1, short_url_name))

        conn.commit()
        conn.close()
        return redirect(original_url)

    else:
        flash('Invalid URL', category='danger')
        return redirect(url_for('index'))


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
                    return redirect(url_for('my_profile'))
            except Exception:
                flash('Database read error', category='danger')

    return render_template('sign_up.html')


@app.route('/sign_in', methods=['GET', 'POST'])
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
                try:
                    user = conn.execute(f"SELECT * FROM users WHERE username = '{username}' LIMIT 1").fetchone()
                    userlogin = UserLogin().create(user)
                    rm = True if request.form.get('remember-me') else False
                    login_user(userlogin, remember=rm)
                    flash('You have successfully signed in', category='success')
                    return redirect(url_for('my_profile'))
                except Exception:
                    flash('Database read error', category='danger')
            else:
                flash('Wrong password. Please check the data', category='danger')
        else:
            flash('This user was not found. Please sign up', category='danger')

    return render_template('sign_in.html')


@app.route('/unauthorized_user')
def unauthorized_user():
    return render_template('unauthorized_user.html')


if development:
    app.run(debug=True)
