# -*- coding: utf-8 -*-

from flask import render_template
from flask_wtf.csrf import CSRFError

from . import video


@video.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400


@video.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@video.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@video.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
