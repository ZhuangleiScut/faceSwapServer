from flask import request
import os

from .FaceSwap import FaceSwap
from . import video


basedir = os.path.abspath(os.path.dirname(__file__))


@video.route('/video/', methods=['POST'])
def get_video():
    path1 = request.json['url1']
    path2 = request.json['url2']
    face1 = request.json['face1']
    face2 = request.json['face2']
    print(path1, path2)
    # 传过来的文件名字
    if path1 is not None and path2 is not None:
        if os.path.exists(path1) and os.path.exists(path2):
            face_swap = FaceSwap()
            out_url = face_swap.deal_video(path1, face1, path2, face2, True)
            return out_url
        else:
            return "file is not exist!"
    else:
        return 'path is None!'
