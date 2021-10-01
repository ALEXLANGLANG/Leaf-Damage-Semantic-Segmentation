from tkinter import Toplevel, Label, Scale, Button, HORIZONTAL, RIGHT
import numpy as np
from skimage import morphology
from skimage.filters import threshold_otsu


class AdjustFrame(Toplevel):

    def __init__(self, master=None):
        Toplevel.__init__(self, master=master)
        self.title("Adjust")
        # self.brightness_value = 0
        # self.previous_brightness_value = 0
        self.threshold_otsu = 0
        self.original_image = self.master.processed_image.copy()
        self.processing_image = self.master.processed_image.copy()
        self.processing_label = self.master.processed_data_label_2d.copy()
        self.original_label = self.master.processed_data_label_2d.copy()
        self.threshold = Label(self, text='threshold_otsu')
        self.threshold_scale = Scale(self, from_=0, to_=256, length=250, resolution=1, orient=HORIZONTAL)
        self.object_size = Label(self, text='remove_object_size')
        self.object_size_scale = Scale(self, from_=0, to_=10000, length=250, resolution=1, orient=HORIZONTAL)
        self.outline_width = Label(self, text='remove_outline_width')
        self.outline_width_scale = Scale(self, from_=0, to_=250, length=250, resolution=1, orient=HORIZONTAL)
        self.apply_button = Button(self, text="Apply")
        self.preview_button = Button(self, text="Preview")
        self.cancel_button = Button(self, text="Cancel")

        # self.brightness_scale.set(1)
        self.threshold_scale.set(0)
        self.object_size_scale.set(0)
        self.outline_width_scale.set(30)

        self.apply_button.bind("<ButtonRelease>", self.apply_button_released)
        self.preview_button.bind("<ButtonRelease>", self.show_button_release)
        self.cancel_button.bind("<ButtonRelease>", self.cancel_button_released)

        self.threshold.pack()
        self.threshold_scale.pack()
        self.object_size.pack()
        self.object_size_scale.pack()
        self.outline_width.pack()
        self.outline_width_scale.pack()
        self.cancel_button.pack(side=RIGHT)
        self.preview_button.pack(side=RIGHT)
        self.apply_button.pack()

        self.show_button_release(self.processing_image)

    def apply_button_released(self, event):
        self.master.processed_image = self.processing_image.copy()
        self.master.processed_data_label_2d = self.processing_label.copy()
        self.save_adjust_process_info(self.threshold_otsu, self.object_size, self.outline_width)
        self.close()

    def show_button_release(self, event):
        self.processing_image, self.threshold_otsu, self.object_size, self.outline_width = self.preprocess_a_image(
            self.original_image,
            self.threshold_scale.get(),
            self.object_size_scale.get(),
            self.outline_width_scale.get())
        self.processing_label = self.recolor_outline(self.original_label, self.outline_width_scale.get(), 0)

        n_diff = abs(np.count_nonzero(self.processing_label) - np.count_nonzero(self.original_label))
        print(n_diff)
        if n_diff > 10:
            print(n_diff)
            self.processing_image, self.threshold_otsu, self.object_size, self.outline_width = self.preprocess_a_image(
                self.original_image, 0, self.object_size_scale.get(), 1)
            self.processing_label = self.recolor_outline(self.original_label, 0, 0)

        self.threshold_scale.set(self.threshold_otsu)
        self.object_size_scale.set(self.object_size)
        self.outline_width_scale.set(self.outline_width)
        self.show_two_images()

    def save_adjust_process_info(self, threshold, object_size, outline_width):
        act_id = str(len(self.master.process_info['actions']))
        self.master.process_info['actions'][act_id] = {}
        self.master.process_info['actions'][act_id]['adjust'] = {
            'threshold': threshold, 'object size': object_size, 'outline_width': outline_width}

    def cancel_button_released(self, event):
        self.close()

    def show_image(self, img=None):
        self.master.image_viewer.show_image(img=img)

    def show_two_images(self):
        self.master.image_viewer.show_two_images(self.original_image, self.processing_image)

    def close(self):
        self.show_image()
        self.destroy()

    @staticmethod
    def preprocess_a_image(img_rgb, thresh=0, object_size=4000, width=50):
        '''
        Args:
            img_rgb: original image 3d
            object_size: hyper parameter for orphology.remove_small_objects and holes
            ratio: hyper parameter for remove_redundant_bars
        Returns:
            img_clean
        '''
        img_gray = img_rgb.mean(axis=2)
        if thresh == 0:
            thresh = threshold_otsu(img_gray)
            tolerance = 10 * np.mean(img_gray) / 200
            thresh = int(thresh + tolerance)
        if object_size == 0:
            object_size = 3000
        bw = img_gray > thresh
        # This is to remove texts, bar code, sings in the leaves images
        bw = morphology.remove_small_objects(bw, object_size)
        bw = morphology.remove_small_holes(bw, object_size)
        index = 1 * (bw == False) == 0
        img_rm = img_rgb.copy()
        img_rm[index, :] = [255, 255, 255]
        img_rm = AdjustFrame.recolor_outline(img_rm, width, [255, 255, 255])

        return img_rm, thresh, object_size, width

    @staticmethod
    def recolor_one_line(img, rs, cs, re, ce, value_):
        img[rs:re, cs:ce] = value_
        return img

    @staticmethod
    def recolor_outline(img_, width, value_):
        img = img_.copy()
        if img.ndim == 3:
            m, n, _ = img.shape
        elif img.ndim < 3:
            m, n = img.shape
        else:
            print(f'img ndim should be <= 3 but {img.ndim}')

        #  left column
        img = AdjustFrame.recolor_one_line(img, 0, 0, m, min(width, n), value_)
        #  right column
        img = AdjustFrame.recolor_one_line(img, 0, max(n - width, 0), m, n, value_)
        #  top row
        img = AdjustFrame.recolor_one_line(img, 0, 0, min(width, m), n, value_)
        #  bottom row
        img = AdjustFrame.recolor_one_line(img, max(m - width, 0), 0, m, n, value_)

        return img
