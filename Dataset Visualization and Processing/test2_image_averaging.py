import glob
import math
import cv2
import numpy as np
import matplotlib.pyplot as plt


class ImageProcessor:

    def __init__(self, name):
        self.data = []
        self.video_name = name

    def plotting3D(self, imx, imy, imz):
        fig = plt.figure()
        ax = plt.axes(projection="3d")
        ax.scatter3D(imx, imy, imz, 'gray')
        plt.show()




    def compand(self, img, mu):
        img = 2 * img.astype(float) / 255.0 - 1
        companded = np.multiply(np.sign(img), np.log(1+mu*np.abs(img))) / np.log(1+mu)
        companded = (companded + 1)/2*255
        return np.uint8(companded)

    def process_frame_2(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        laplacian = cv2.Laplacian(img, cv2.CV_8U)
        # blurred = cv2.GaussianBlur(img, (5, 5), 0)
        # blurred = cv2.bilateralFilter(img, 9, 75, 75)
        # companded = self.compand(blurred, 255)
        '''
        img_inv = 255 - blood_vessel_map
        # blurred = cv2.bilateralFilter(img_inv, 9, 75, 75)
        blurred = cv2.GaussianBlur(img_inv, (5, 5), 0)
        th = 255 - cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
        erosion = cv2.erode(th, kernel, iterations=1)
        dilation = cv2.dilate(erosion, kernel, iterations=1)
        '''

        return laplacian

    def normalize_wrt_percentile(self, img, percent_val):
        overbright_pixel_val = np.percentile(img, percent_val)
        img[img > overbright_pixel_val] = overbright_pixel_val
        return np.uint8(img / overbright_pixel_val * 255)

    def extract_video_frames(self, video):
        no_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video.get(3))
        height = int(video.get(4))
        layers = 3

        image_collection = np.zeros((no_frames, height, width, layers), dtype=np.uint8)
        for frame_no in range(no_frames):
            ret, frame = video.read()
            if ret == False:
                break
            image_collection[frame_no, :, :, :] = frame

        return image_collection

    def create_vessel_map(self, image_collection):
        no_frames = image_collection.shape[0]
        height = image_collection.shape[1]
        width = image_collection.shape[2]
        layers = 3

        vessel_map = np.zeros((height, width, layers), dtype=np.uint32)
        for frame_no in range(no_frames):
            vessel_map = vessel_map + np.uint32(image_collection[frame_no, :, :, :])

        return np.uint8(vessel_map/no_frames)

    def create_time_chunks(self, image_collection, frame_overlap, chunk_size):
        no_frames = image_collection.shape[0]
        height = image_collection.shape[1]
        width = image_collection.shape[2]
        layers = 3
        num_chunks = 1 + math.floor((no_frames - chunk_size) / frame_overlap)

        image_collection_averaged = np.zeros((num_chunks, height, width, layers), dtype=np.uint8)

        for chunk_no in range(num_chunks):
            start_frame = chunk_no * frame_overlap
            averaged_frame = np.zeros((height, width, layers), dtype=np.uint8)
            for frame_no in range(start_frame, start_frame + chunk_size):
                averaged_frame = averaged_frame + np.uint32(image_collection[frame_no, :, :, :])

            averaged_frame = np.uint8(averaged_frame/chunk_size)
            image_collection_averaged[chunk_no, :, :, :] = averaged_frame

        return image_collection_averaged

    def tester3(self):
        video = cv2.VideoCapture(self.video_name)
        image_collection = self.extract_video_frames(video)
        video.release()

        blood_vessel_map = self.create_vessel_map(image_collection)
        blood_vessel_map = cv2.cvtColor(blood_vessel_map, cv2.COLOR_BGR2GRAY)
        image_collection_averaged = self.create_time_chunks(image_collection, frame_overlap=5, chunk_size=10)

        image = image_collection_averaged[0, :, :, :]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        plt.subplot(2, 2, 1)
        plt.imshow(blood_vessel_map, cmap='gray')
        plt.subplot(2, 2, 2)
        plt.imshow(image, cmap='gray')
        plt.subplot(2, 2, 3)
        plt.hist(blood_vessel_map.ravel(), bins=256, range=(0, 255), fc='k', ec='k')
        plt.subplot(2, 2, 4)
        plt.hist(image.ravel(), bins=256, range=(0, 255), fc='k', ec='k')
        plt.show()

    def equalize_histogram(self, img):
        # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_histograms/py_histogram_equalization/py_histogram_equalization.html
        equ = cv2.equalizeHist(img)
        res = np.hstack((img, equ))  # stacking images side-by-side
        return res

    def adjust_gamma(self, image, gamma=1.0):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")
        # apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    def extract_ROI(self, image_collection):
        no_frames = image_collection.shape[0]
        frame = image_collection[0, :, :, :]
        mask, boundingbox = self.find_ROI(frame)

        ROI_collection = np.zeros((no_frames, boundingbox[3], boundingbox[2], 3), dtype=np.uint8)

        for idx in range(no_frames):
            img = image_collection[idx, :, :, :]
            ROI_collection[idx, :, :, :] = self.extract_bounded_region(img, mask, boundingbox)

        return ROI_collection

    def find_ROI(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Threshold of blue in HSV space
        lower_orange = np.array([5, 195, 205])
        upper_orange = np.array([20, 255, 255])
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.inRange(hsv, lower_orange, upper_orange)
        mask = cv2.dilate(mask, kernel, iterations=1)

        im_floodfill = mask
        h, w = mask.shape[:2]
        masked = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(im_floodfill, masked, (0, 0), 255)
        im_floodfill_inv = cv2.bitwise_not(im_floodfill)

        cnts = cv2.findContours(im_floodfill_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

        x, y, w, h = cv2.boundingRect(cnts[0])
        boundingbox = np.zeros(4).astype(int)
        boundingbox[0] = x
        boundingbox[1] = y
        boundingbox[2] = w
        boundingbox[3] = h

        return im_floodfill_inv, boundingbox

    def extract_bounded_region(self, frame, im_floodfill_inv, boundingbox):
        im_out = frame.copy()
        im_out[:, :, 0] = frame[:, :, 0] & im_floodfill_inv
        im_out[:, :, 1] = frame[:, :, 1] & im_floodfill_inv
        im_out[:, :, 2] = frame[:, :, 2] & im_floodfill_inv

        x = boundingbox[0]
        y = boundingbox[1]
        w = boundingbox[2]
        h = boundingbox[3]
        ROI = im_out[y:y + h, x:x + w, :]

        return ROI

    def tester3_1(self):
        video = cv2.VideoCapture(self.video_name)
        image_collection = self.extract_video_frames(video)
        image_collection = self.extract_ROI(image_collection)
        video.release()

        blood_vessel_map = self.create_vessel_map(image_collection)
        blood_vessel_map = cv2.cvtColor(blood_vessel_map, cv2.COLOR_BGR2GRAY)
        image_collection_averaged = self.create_time_chunks(image_collection, frame_overlap=5, chunk_size=10)

        # prev_img = image_collection_averaged[0, :, :, :]
        # prev_img = cv2.cvtColor(prev_img, cv2.COLOR_BGR2GRAY)

        # for frame_no in range(image_collection_averaged.shape[0]):
        img = image_collection_averaged[0, :, :, :]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gamma_corrected = self.adjust_gamma(img, 0.5)
        # processed_img = self.process_frame_1(img)
        # diff = prev_img.astype(int) - img.astype(int)

        # res = np.hstack((img_original, img, processed_img))
        # plt.imshow(res, cmap='gray')

        plt.subplot(2, 3, 1)
        plt.imshow(img, cmap='gray')
        plt.subplot(2, 3, 2)
        plt.imshow(gamma_corrected, cmap='gray')
        plt.subplot(2, 3, 3)
        plt.imshow(blood_vessel_map, cmap='gray')
        '''
        plt.subplot(2, 3, 4)
        plt.hist(img.ravel(), bins=256, range=(0, 255), fc='k', ec='k')
        plt.subplot(2, 3, 5)
        plt.hist(gamma_corrected.ravel(), bins=256, range=(0, 255), fc='k', ec='k')
        plt.subplot(2, 3, 6)
        plt.hist(blood_vessel_map.ravel(), bins=256, range=(0, 255), fc='k', ec='k')
        '''

        # mng = plt.get_current_fig_manager()
        # mng.full_screen_toggle()
        plt.show()




path = '../../micro'
files = [f for f in glob.glob(path + "/*.mp4", recursive=True)]
for f in files:
    testObject = ImageProcessor(f)
    testObject.tester3_1()

# https://github.com/conscienceli/IterNet