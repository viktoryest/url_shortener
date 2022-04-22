from flask import flash, request, redirect, url_for
from flask_login import login_user
from werkzeug.security import check_password_hash
from user_class import UserLogin
from exceptions import DatabaseException


def check_sign_in(conn):
    username = request.form['username']
    password = request.form['password']

    try:
        active_user = conn.execute('SELECT username, psw_hash FROM users '
                                   'WHERE username = ?', (username,)).fetchone()

        if active_user is not None:
            true_psw_hash = active_user['psw_hash']

            if check_password_hash(true_psw_hash, password):
                user = conn.execute(f"SELECT * FROM users WHERE username = '{username}' LIMIT 1").fetchone()
                userlogin = UserLogin().create(user)
                rm = True if request.form.get('remember-me') else False
                login_user(userlogin, remember=rm)
                flash('You have successfully signed in', category='success')
                return redirect(url_for('my_profile'))
            else:
                flash('Wrong password. Please check the data', category='danger')
        else:
            flash('This user was not found. Please sign up', category='danger')
    except DatabaseException:
        flash('Database read error', category='danger')
