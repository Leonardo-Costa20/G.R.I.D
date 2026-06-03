from flask import render_template, redirect, url_for, request, session


def landing_apresentacao():
    if session.get('logged_in'):
        return redirect(url_for('index'))

    referer = request.headers.get('Referer', '')
    sec_fetch_site = request.headers.get('Sec-Fetch-Site', '')
    if not referer and sec_fetch_site == 'none':
        return redirect(url_for('welcome'))
    return render_template('landing_apresentacao.html')


def welcome():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('welcome.html')


def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'), role=session.get('role'))
