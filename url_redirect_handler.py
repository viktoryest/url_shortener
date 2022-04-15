from flask import flash, redirect, url_for


def get_redirect_url(conn, hashids, id):
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
