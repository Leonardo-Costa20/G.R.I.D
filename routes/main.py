import os
import requests
from flask import render_template, redirect, url_for, request, session, jsonify


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

def api_flash():
    if not session.get('logged_in'):
        return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
    CAMERA_URL = os.getenv('CAMERA_URL', 'https://camera.gridos.space')
    try:
        r = requests.get(f'{CAMERA_URL}/flash', timeout=5)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 502
