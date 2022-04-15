from flask import flash, redirect, url_for, request
from flask_login import current_user


def get_short_url(conn, hashids):
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

        return short_url
