from flask import request


def make_url_list(db_urls, hashids):
    urls = []
    for url in db_urls:
        url = dict(url)
        short_url_name = url['short_url_name']

        if short_url_name == '0':
            url['short_url'] = request.host_url + hashids.encode(url['id'])
        else:
            url['short_url'] = request.host_url + short_url_name
        urls.append(url)

    return urls
