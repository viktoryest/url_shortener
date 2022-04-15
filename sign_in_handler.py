from flask import flash, request, redirect, url_for
from flask_login import login_user
from werkzeug.security import check_password_hash
from user_class import UserLogin


def check_sign_in(conn):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username:
            flash('Please enter username', category='info')
        elif not password:
            flash('Please enter password', category='info')

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
