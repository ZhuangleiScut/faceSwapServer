# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import StringField
from wtforms.validators import DataRequired, Regexp


class ImgForm_src(FlaskForm):
    fileimg = FileField(validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg'])
    ])


class URLForm_src(FlaskForm):
    txturl = StringField(validators=[
        DataRequired(),
        Regexp(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg|jpeg)$',
               message="Invalid image url.")
    ])


class ImgForm_usr(FlaskForm):
    fileimg = FileField(validators=[
        FileRequired(),
        FileAllowed(['png', 'jpg', 'jpeg'])
    ])


class URLForm_usr(FlaskForm):
    txturl = StringField(validators=[
        DataRequired(),
        Regexp(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg|jpeg)$',
               message="Invalid image url.")
    ])
