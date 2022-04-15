from flask import flash, request, redirect, url_for
from flask_login import login_user
from user_class import UserLogin
from werkzeug.security import generate_password_hash


def check_sign_up(conn):
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
