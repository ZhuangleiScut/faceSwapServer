from flask import request
import os

from .FaceSwap import FaceSwap
from . import video
import requests


basedir = os.path.abspath(os.path.dirname(__file__))


@video.route('/video/', methods=['POST'])
def get_video():
    path1 = request.json['url1']
    path2 = request.json['url2']
    face1 = request.json['face1']
    face2 = request.json['face2']
    id = request.json['id']
    print(path1, path2)
    # 传过来的文件名字
    if path1 is not None and path2 is not None:
        if os.path.exists(path1) and os.path.exists(path2):
            face_swap = FaceSwap()
            out = face_swap.deal_video(path1, face1, path2, face2, id, True)
            if out:
                finish_id = {'videoId': id}
                requests.get('127.0.0.1:8001/video/make/finish', params=finish_id)
            else:
                return "video process error!"
        else:
            return "file is not exist!"
    else:
        return 'path is None!'
