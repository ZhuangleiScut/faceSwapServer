import cv2
import os
import dlib
import numpy as np
import ffmpy


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

        self.ALIGN_POINTS = (self.LEFT_BROW_POINTS + self.RIGHT_EYE_POINTS + self.LEFT_EYE_POINTS +
                             self.RIGHT_BROW_POINTS + self.NOSE_POINTS + self.MOUTH_POINTS + self.JAW_POINTS)

        self.OVERLAY_POINTS = [self.LEFT_EYE_POINTS + self.RIGHT_EYE_POINTS + self.NOSE_POINTS + self.MOUTH_POINTS]

        self.COLOUR_CORRECT_BLUR_FRAC = 0.6

        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.dlib_model_path = self.basedir + '/models/shape_predictor_68_face_landmarks.dat'
        self.shape_predictor = dlib.shape_predictor(self.dlib_model_path)
        self.detector = dlib.get_frontal_face_detector()

    def get_landmarks(self, im, face_flag):
        face_rect = self.detector(im, 1)

        if len(face_rect) > 1:
            return np.matrix([[p.x, p.y] for p in self.shape_predictor(im, face_rect[face_flag]).parts()])
        elif len(face_rect) == 0:
            return None
        else:
            return np.matrix([[p.x, p.y] for p in self.shape_predictor(im, face_rect[0]).parts()])

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
        R = (U * Vt).T

        return np.vstack([np.hstack(((s2 / s1) * R,
                                     c2.T - (s2 / s1) * R * c1.T)),
                          np.matrix([0., 0., 1.])])

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

    def deal_image(self, srcImg, face_src, trgImg, face_user):
        srcImg = cv2.resize(srcImg, (srcImg.shape[1] * self.SCALE_FACTOR,
                                     srcImg.shape[0] * self.SCALE_FACTOR))

        trgImg = cv2.resize(trgImg, (trgImg.shape[1] * self.SCALE_FACTOR,
                                     trgImg.shape[0] * self.SCALE_FACTOR))
        # trgImg = trgImg.rotate(90)
        landmark1 = self.get_landmarks(srcImg, face_src)
        landmark2 = self.get_landmarks(trgImg, face_user)

        if landmark1 is not None and landmark2 is not None:
            transformation_matrix = self.transformation_from_points(landmark1[self.ALIGN_POINTS],
                                                                    landmark2[self.ALIGN_POINTS])

            mask = self.get_face_mask(trgImg, landmark2)

            warped_mask = self.warp_im(mask, transformation_matrix, srcImg.shape)

            combined_mask = np.max([self.get_face_mask(srcImg, landmark1), warped_mask], axis=0)

            warped_img2 = self.warp_im(trgImg, transformation_matrix, srcImg.shape)

            warped_corrected_img2 = self.correct_colors(srcImg, warped_img2, landmark1)
            warped_corrected_img2_temp = np.zeros(warped_corrected_img2.shape, dtype=warped_corrected_img2.dtype)
            cv2.normalize(warped_corrected_img2, warped_corrected_img2_temp, 0, 1, cv2.NORM_MINMAX)

            output = srcImg * (1.0 - combined_mask) + warped_corrected_img2 * combined_mask
            return output
        else:
            return None

    def deal_image(self, srcImg, face_src, trgImg, face_user):
        srcImg = cv2.resize(srcImg, (srcImg.shape[1] * self.SCALE_FACTOR,
                                     srcImg.shape[0] * self.SCALE_FACTOR))

        trgImg = cv2.resize(trgImg, (trgImg.shape[1] * self.SCALE_FACTOR,
                                     trgImg.shape[0] * self.SCALE_FACTOR))
        # trgImg = trgImg.rotate(90)
        landmark1 = self.get_landmarks(srcImg, face_src)
        landmark2 = self.get_landmarks(trgImg, face_user)

        if landmark1 is not None and landmark2 is not None:
            transformation_matrix = self.transformation_from_points(landmark1[self.ALIGN_POINTS],
                                                                    landmark2[self.ALIGN_POINTS])

            mask = self.get_face_mask(trgImg, landmark2)

            warped_mask = self.warp_im(mask, transformation_matrix, srcImg.shape)

            combined_mask = np.max([self.get_face_mask(srcImg, landmark1), warped_mask], axis=0)

            warped_img2 = self.warp_im(trgImg, transformation_matrix, srcImg.shape)

            warped_corrected_img2 = self.correct_colors(srcImg, warped_img2, landmark1)
            warped_corrected_img2_temp = np.zeros(warped_corrected_img2.shape, dtype=warped_corrected_img2.dtype)
            cv2.normalize(warped_corrected_img2, warped_corrected_img2_temp, 0, 1, cv2.NORM_MINMAX)

            output = srcImg * (1.0 - combined_mask) + warped_corrected_img2 * combined_mask
            return output
        else:
            return None

    def deal_video(self, path_src, face_src, path_user, face_user, out_id, flip=False):
        video1 = cv2.VideoCapture(path_src)
        video2 = cv2.VideoCapture(path_user)
        fps1 = video1.get(cv2.CAP_PROP_FPS)
        fps2 = video2.get(cv2.CAP_PROP_FPS)
        video_out = self.basedir+'/out_without_audio.mp4'

        img_size = (1280, 720)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        video_writer = cv2.VideoWriter(video_out, fourcc, fps1, img_size)

        if video1.isOpened() and video2.isOpened():
            val1, frame1 = video1.read()
            val2, frame2 = video2.read()
        i = 0
        index1 = 1
        index2 = 1
        while frame1 is not None and frame2 is not None:
            val1, frame1 = video1.read()
            index1 += 1
            while index2 < index1 * fps2 / fps1:
                val2, frame2 = video2.read()
                index2 += 1

            if flip:
                frame2 = cv2.flip(frame2, 1)
            frame2 = cv2.transpose(frame2)
            if frame1 is not None and frame2 is not None:
                out_image = self.deal_image(frame1, face_src, frame2, face_user)
                if out_image is not None:
                    im = cv2.resize(out_image, img_size)

                    cv2.imwrite(self.basedir + '/result/{i}.jpg'.format(i=i), im)

                    im = cv2.imread(self.basedir + '/result/{i}.jpg'.format(i=i))

                    video_writer.write(im)
                    os.remove(self.basedir + '/result/{i}.jpg'.format(i=i))
                else:
                    continue

            i += 1
        video_writer.release()

        # path_out = self.basedir+'/output/{out}.mp4'.format(out=out_id)
        path_out = "/root/miniproj/data/videos/{out}.mp4".format(out_id)
        self.add_audio_to_video(path_src, video_out, path_out)

        os.remove(video_out)
        return True

    def add_audio_to_video(self, path_audio_provider, path_video_provider, path_out):
        audio_path = path_audio_provider.split('.')[0] + '.mp3'

        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(path_out):
            os.remove(path_out)

        ff = ffmpy.FFmpeg(
            inputs={path_audio_provider: None},
            outputs={audio_path: '-map 0:a'}
        )
        ff.run()

        ff = ffmpy.FFmpeg(
            inputs={path_video_provider: None, audio_path: None},
            outputs={path_out: None}
        )
        ff.run()
        os.remove(audio_path)
