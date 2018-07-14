import cv2
import os
import dlib
import numpy as np
import time
import ffmpy


class TooManyFaces(Exception):
    pass


class NoFaces(Exception):
    pass


class FaceSwap(object):
    def __init__(self):
        self.SCALE_FACTOR = 1
        self.FEATHER_AMOUNT = 11

        self.FACE_POINTS = list(range(17, 68))
        self.MOUTH_POINTS = list(range(48, 61))
        self.RIGHT_BROW_POINTS = list(range(17, 22))
        self.LEFT_BROW_POINTS = list(range(22, 27))
        self.RIGHT_EYE_POINTS = list(range(36, 42))
        self.LEFT_EYE_POINTS = list(range(42, 48))
        self.NOSE_POINTS = list(range(27, 35))
        self.JAW_POINTS = list(range(0, 17))

        # Points used to line up the images.
        self.ALIGN_POINTS = (self.LEFT_BROW_POINTS + self.RIGHT_EYE_POINTS + self.LEFT_EYE_POINTS +
                             self.RIGHT_BROW_POINTS + self.NOSE_POINTS + self.MOUTH_POINTS + self.JAW_POINTS)

        # Points from the second image to overlay on the first. The convex hull of each
        # element will be overlaid.
        self.OVERLAY_POINTS = [self.LEFT_EYE_POINTS + self.RIGHT_EYE_POINTS + self.NOSE_POINTS + self.MOUTH_POINTS]

        # Amount of blur to use during colour correction, as a fraction of the
        # pupillary distance.
        self.COLOUR_CORRECT_BLUR_FRAC = 0.6

        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.dlib_model_path = self.basedir + '/models/shape_predictor_68_face_landmarks.dat'
        self.shape_predictor = dlib.shape_predictor(self.dlib_model_path)
        self.detector = dlib.get_frontal_face_detector()

    def get_landmarks(self, im):
        face_rect = self.detector(im, 1)

        if len(face_rect) > 1:
            print('Too many faces.We only need no more than one face.')
            raise TooManyFaces
        elif len(face_rect) == 0:
            print('No face.We need at least one face.')
            raise NoFaces
        else:
            print('---left {0}; top {1}; right {2}; bottom {3}'.format(face_rect[0].left(), face_rect[0].top(),
                                                                       face_rect[0].right(), face_rect[0].bottom()))

            return np.matrix([[p.x, p.y] for p in self.shape_predictor(im, face_rect[0]).parts()])

    def get_landmarks2(self, im, rects):
        if len(rects) > 2:
            raise TooManyFaces
        if len(rects) == 0:
            raise NoFaces
        landmarks = []
        landmarks.append(np.matrix([[p.x, p.y] for p in self.shape_predictor(im, rects[0]).parts()]))
        landmarks.append(np.matrix([[p.x, p.y] for p in self.shape_predictor(im, rects[1]).parts()]))

        return landmarks

    def annotate_landmarks(self, im, landmarks):
        im = im.copy()
        for idx, point in enumerate(landmarks):
            pos = (point[0, 0], point[0, 1])
            cv2.putText(im, str(idx), pos,
                        fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                        fontScale=0.4,
                        color=(0, 0, 255))
            cv2.circle(im, pos, 3, color=(0, 255, 255))
        return im

    def draw_convex_hull(self, im, points, color):
        points = cv2.convexHull(points)
        cv2.fillConvexPoly(im, points, color=color)

    def get_face_mask(self, im, landmarks):
        im = np.zeros(im.shape[:2], dtype=np.float64)

        for group in self.OVERLAY_POINTS:
            self.draw_convex_hull(im,
                             landmarks[group],
                             color=1)

        im = np.array([im, im, im]).transpose((1, 2, 0))

        im = (cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0) > 0) * 1.0
        im = cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0)

        return im

    def transformation_from_points(self, points1, points2):
        """
        Return an affine transformation [s * R | T] such that:

            sum ||s*R*p1,i + T - p2,i||^2

        is minimized.

        """
        # Solve the procrustes problem by subtracting centroids, scaling by the
        # standard deviation, and then using the SVD to calculate the rotation. See
        # the following for more details:
        #   https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem

        points1 = points1.astype(np.float64)
        points2 = points2.astype(np.float64)

        c1 = np.mean(points1, axis=0)
        c2 = np.mean(points2, axis=0)
        points1 -= c1

        points2 -= c2

        s1 = np.std(points1)
        s2 = np.std(points2)
        points1 /= s1
        points2 /= s2

        U, S, Vt = np.linalg.svd(points1.T * points2)

        # The R we seek is in fact the transpose of the one given by U * Vt. This
        # is because the above formulation assumes the matrix goes on the right
        # (with row vectors) where as our solution requires the matrix to be on the
        # left (with column vectors).
        R = (U * Vt).T

        return np.vstack([np.hstack(((s2 / s1) * R,
                                     c2.T - (s2 / s1) * R * c1.T)),
                          np.matrix([0., 0., 1.])])

    def read_im_and_landmarks(self, fname):
        im = cv2.imread(fname)
        im = cv2.resize(im, (im.shape[1] * self.SCALE_FACTOR,
                             im.shape[0] * self.SCALE_FACTOR))
        rects = self.detector(im, 1)
        s = self.get_landmarks2(im, rects)

        return im, s

    def warp_im(self, im, M, dshape):
        output_im = np.zeros(dshape, dtype=im.dtype)
        cv2.warpAffine(im,
                       M[:2],
                       (dshape[1], dshape[0]),
                       dst=output_im,
                       borderMode=cv2.BORDER_TRANSPARENT,
                       flags=cv2.WARP_INVERSE_MAP)
        return output_im

    def correct_colors(self, im1, im2, landmarks1):
        blur_amount = self.COLOUR_CORRECT_BLUR_FRAC * np.linalg.norm(
            np.mean(landmarks1[self.LEFT_EYE_POINTS], axis=0) -
            np.mean(landmarks1[self.RIGHT_EYE_POINTS], axis=0))
        blur_amount = int(blur_amount)
        if blur_amount % 2 == 0:
            blur_amount += 1
        im1_blur = cv2.GaussianBlur(im1, (blur_amount, blur_amount), 0)
        im2_blur = cv2.GaussianBlur(im2, (blur_amount, blur_amount), 0)

        # Avoid divide-by-zero errors.
        im2_blur += (128 * (im2_blur <= 1.0)).astype(im2_blur.dtype)

        return (im2.astype(np.float64) * im1_blur.astype(np.float64) /
                im2_blur.astype(np.float64))

    """
        srcImg：原视频图片
        trgImg：用户录制视频图片
    """

    def deal_image(self, srcImg, trgImg):
        srcImg = cv2.resize(srcImg, (srcImg.shape[1] * self.SCALE_FACTOR,
                                     srcImg.shape[0] * self.SCALE_FACTOR))

        trgImg = cv2.resize(trgImg, (trgImg.shape[1] * self.SCALE_FACTOR,
                                     trgImg.shape[0] * self.SCALE_FACTOR))

        landmark1 = self.get_landmarks(srcImg)
        landmark2 = self.get_landmarks(trgImg)

        transformation_matrix = self.transformation_from_points(landmark1[self.ALIGN_POINTS], landmark2[self.ALIGN_POINTS])

        mask = self.get_face_mask(trgImg, landmark2)

        warped_mask = self.warp_im(mask, transformation_matrix, srcImg.shape)

        combined_mask = np.max([self.get_face_mask(srcImg, landmark1), warped_mask], axis=0)

        warped_img2 = self.warp_im(trgImg, transformation_matrix, srcImg.shape)

        warped_corrected_img2 = self.correct_colors(srcImg, warped_img2, landmark1)
        warped_corrected_img2_temp = np.zeros(warped_corrected_img2.shape, dtype=warped_corrected_img2.dtype)
        cv2.normalize(warped_corrected_img2, warped_corrected_img2_temp, 0, 1, cv2.NORM_MINMAX)

        output = srcImg * (1.0 - combined_mask) + warped_corrected_img2 * combined_mask
        return output

    def deal_video(self, path_src, path_user, flip=False):
        print(path_src, path_user)
        video1 = cv2.VideoCapture(path_src)
        video2 = cv2.VideoCapture(path_user)
        fps1 = video1.get(cv2.CAP_PROP_FPS)
        fps2 = video2.get(cv2.CAP_PROP_FPS)
        print(fps1, fps2)
        # 输出视频路径
        video_out = self.basedir+'/out_without_audio.mp4'

        # 图片尺寸
        img_size = (640, 480)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        video_writer = cv2.VideoWriter(video_out, fourcc, fps1, img_size)

        if video1.isOpened() and video2.isOpened():  # 判断是否正常打开
            val1, frame1 = video1.read()
            val2, frame2 = video2.read()
        else:
            val1 = False
            val2 = False
        # i = 0
        # while val1 and val2:
        for i in range(130):
            start = time.time()
            val1, frame1 = video1.read()
            val2, frame2 = video2.read()

            if flip:
                # 左右翻转
                frame2 = cv2.flip(frame2, 1)

            out_image = self.deal_image(frame1, frame2)
            im = cv2.resize(out_image, img_size)
            print(self.basedir)

            cv2.imwrite(self.basedir+'/result/{i}.jpg'.format(i=i), im)

            im = cv2.imread(self.basedir+'/result/{i}.jpg'.format(i=i))

            video_writer.write(im)
            os.remove(self.basedir+'/result/{i}.jpg'.format(i=i))

            end = time.time()
            print(i, end - start)
            i += 1
        video_writer.release()

        path_out = self.basedir+'/out.mp4'
        self.add_audio_to_video(path_src, video_out, path_out)

        os.remove(video_out)
        print(path_out)
        return path_out

    def add_audio_to_video(self, path_audio_provider, path_video_provider, path_out):
        audio_path = path_audio_provider.split('.')[0] + '.mp3'

        # 验证文件夹是否存在
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(path_out):
            os.remove(path_out)

        # 从原片提取音频
        ff = ffmpy.FFmpeg(
            inputs={path_audio_provider: None},
            outputs={audio_path: '-map 0:a'}
        )
        ff.run()

        # 视频音频合成
        ff = ffmpy.FFmpeg(
            inputs={path_video_provider: None, audio_path: None},
            outputs={path_out: None}
        )
        ff.run()
        os.remove(audio_path)

