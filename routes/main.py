from flask import render_template, redirect, url_for, request, session


def landing_apresentacao():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('landing_apresentacao.html')


def welcome():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('welcome.html')


def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'), role=session.get('role'))
