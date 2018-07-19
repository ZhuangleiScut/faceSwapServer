from flask import request, current_app, redirect, url_for, flash, render_template
import os

from werkzeug.utils import secure_filename

from app.utils import download
from .FaceSwap import FaceSwap
from . import video
import requests
from .forms import ImgForm_src, URLForm_src, ImgForm_usr, URLForm_usr


basedir = os.path.abspath(os.path.dirname(__file__))


@video.route('/', methods=['GET', 'POST'])
def index():
    imgform_src = ImgForm_src()
    urlform_src = URLForm_src()

    imgform_usr = ImgForm_usr()
    urlform_usr = URLForm_usr()

    if imgform_src.validate_on_submit():
        file = imgform_src.fileimg.data
        filename = secure_filename(file.filename)
        image_type = filename.split(".")[-1]
        filepath = os.path.join(current_app.config['IMAGE_PATH'], "src.", image_type)
        if not os.path.exists(filepath):
            file.save(filepath)
        return redirect(url_for('.user'))
    elif urlform_src.validate_on_submit():
        url = urlform_src.txturl.data
        filename = secure_filename(url.split('/')[-1])
        image_type = filename.split(".")[-1]
        filepath = os.path.join(current_app.config['IMAGE_PATH'], "src.", image_type)
        download(url, current_app.config['UPLOAD_DIR'], filename)
        if not os.path.exists(filepath):
            flash('无法取回指定URL的图片')
            return redirect(url_for('.index'))
        else:
            return redirect(url_for('.user'))
    return render_template('index.html')


@video.route('/user', methods=['GET', 'POST'])
def user():
    imgform = ImgForm()
    urlform = URLForm()

    if imgform.validate_on_submit():
        file = imgform.fileimg.data
        filename = secure_filename(file.filename)
        image_type = filename.split(".")[-1]
        filepath = os.path.join(current_app.config['IMAGE_PATH'], "user.", image_type)
        if not os.path.exists(filepath):
            file.save(filepath)
        return redirect(url_for('.result'))
    elif urlform.validate_on_submit():
        url = urlform.txturl.data
        filename = secure_filename(url.split('/')[-1])
        image_type = filename.split(".")[-1]
        filepath = os.path.join(current_app.config['IMAGE_PATH'], "user.", image_type)
        download(url, current_app.config['UPLOAD_DIR'], filename)
        if not os.path.exists(filepath):
            flash('无法取回指定URL的图片')
            return redirect(url_for('.user'))
        else:
            return redirect(url_for('.result'))
    return render_template('user_image.html')


@video.route('/result', methods=['GET'])
def result():
    filepath = os.path.join(current_app.config['IMAGE_PATH'], "user.", image_type)
    filepath = os.path.join(current_app.config['IMAGE_PATH'], "user.", image_type)
    if path1 is not None and path2 is not None:
        if os.path.exists(path1) and os.path.exists(path2):
            face_swap = FaceSwap()
            out = face_swap.deal_video(path1, face1, path2, face2, face_id, True)
            if out:
                finish_id = {'videoId': face_id}
                requests.get('127.0.0.1:8001/video/make/finish', params=finish_id)
            else:
                return "video process error!"
            # return "done!"
        else:
            return "file is not exist!"
    else:
        return 'path is None!'
