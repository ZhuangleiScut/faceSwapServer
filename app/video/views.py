from flask import request, current_app, abort
import os

from .FaceSwap import FaceSwap
from . import video
from ..models import Task
from .. import db
import threading


basedir = os.path.abspath(os.path.dirname(__file__))


@video.route('/video/', methods=['POST'])
def get_video():
    path1 = request.json['url1']
    path2 = request.json['url2']
    print(path1, path2)
    # 传过来的文件名字
    if path1 is not None and path2 is not None:
        if os.path.exists(path1) and os.path.exists(path2):
            face_swap = FaceSwap()
            task = Task(src_url=str(path1), tag_url=str(path2))
            db.session.add(task)
            db.session.commit()

            # 异步处理视频
            # return_value = str(task.id)
            # thr = threading.Thread(target=deal_video, args=(app, path1, path2))
            # thr.start()

            out_url = face_swap.deal_video(path1, path2)

            return out_url
        else:
            return "file is not exist!"
    else:
        return 'path is None!'
