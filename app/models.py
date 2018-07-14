from datetime import datetime
from . import db

""" 
    @Task:任务表
"""


class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    time_create = db.Column(db.DateTime(), default=datetime.now)
    src_url = db.Column(db.String(128), nullable=False)
    tag_url = db.Column(db.String(128), nullable=False)
    res_url = db.Column(db.String(128))
    done = db.Column(db.Boolean, default=False)
