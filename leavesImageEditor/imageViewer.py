from tkinter import Frame, Canvas, CENTER, ROUND
from PIL import Image, ImageTk
import cv2


class ImageViewer(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master=master, bg="gray", width=800, height=500)

        self.shown_image0 = None
        self.shown_image1 = None
        self.x = 0
        self.y = 0
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.end_x0 = 0
        self.crop_end_y = 0
        self.draw_ids = list()  # this is for drawing
        self.rectangle_id = 0  # this is for crop
        self.ratio = 0
        self.canvas = Canvas(self, bg="gray", width=500, height=400)
        self.canvas.place(relx=0.5, rely=0.5, anchor=CENTER)

    def show_image(self, img=None):
        self.clear_canvas()

        if img is None:
            image = self.master.processed_image.copy()
        else:
            image = img

        height, width, channels = image.shape
        new_height, new_width = self.get_img_new_width_height_for_display(height, width)
        self.shown_image0 = cv2.resize(image, (new_width, new_height))
        self.shown_image0 = ImageTk.PhotoImage(Image.fromarray(self.shown_image0))
        self.ratio = height / new_height
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(new_width / 2, new_height / 2, anchor=CENTER, image=self.shown_image0)

    def show_two_images(self, img_original, img=None):
        self.clear_canvas()
        if img is None:
            image = self.master.processed_image.copy()
        else:
            image = img

        if img_original is None:
            image_original = self.master.original_image.copy()
        else:
            image_original = img_original
        height, width, channels = image.shape
        new_height, new_width = self.get_img_new_width_height_for_display(height, width)
        new_height, new_width = int(new_height / 1.05), int(new_width / 1.05)
        self.shown_image0 = cv2.resize(image, (new_width, new_height))
        self.shown_image0 = ImageTk.PhotoImage(Image.fromarray(self.shown_image0))

        self.shown_image1 = cv2.resize(image_original, (new_width, new_height))
        self.shown_image1 = ImageTk.PhotoImage(Image.fromarray(self.shown_image1))

        self.ratio = height / new_height
        self.canvas.config(width=new_width * 2, height=new_height)
        self.canvas.create_image(new_width / 2, new_height / 2, anchor=CENTER, image=self.shown_image1)
        self.canvas.create_image(new_width * 1.5, new_height / 2, anchor=CENTER, image=self.shown_image0)

    def activate_draw(self):
        self.canvas.bind("<ButtonPress>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.master.is_draw_state = True

    def activate_crop(self):
        self.canvas.bind("<ButtonPress>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.crop)
        self.canvas.bind("<ButtonRelease>", self.end_crop)

        self.master.is_crop_state = True

    def activate_remove(self):
        self.canvas.bind("<ButtonPress>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.crop)
        self.canvas.bind("<ButtonRelease>", lambda event, action='remove': self.end_crop(event=event, type_=action))
        self.master.is_crop_state = True

    def deactivate_draw(self):
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")

        self.master.is_draw_state = False

    def deactivate_crop(self):
        self.canvas.unbind("<ButtonPress>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease>")

        self.master.is_crop_state = False

    def start_draw(self, event):
        self.x = event.x
        self.y = event.y

    def draw(self, event):
        self.draw_ids.append(self.canvas.create_line(self.x, self.y, event.x, event.y, width=2,
                                                     fill="red", capstyle=ROUND, smooth=True))

        cv2.line(self.master.processed_image, (int(self.x * self.ratio), int(self.y * self.ratio)),
                 (int(event.x * self.ratio), int(event.y * self.ratio)),
                 (0, 0, 255), thickness=int(self.ratio * 2),
                 lineType=8)

        self.x = event.x
        self.y = event.y

    def start_crop(self, event):
        self.crop_start_x = event.x
        self.crop_start_y = event.y

    def crop(self, event):
        if self.rectangle_id:
            self.canvas.delete(self.rectangle_id)
        self.crop_end_x = event.x
        self.crop_end_y = event.y

        self.rectangle_id = self.canvas.create_rectangle(self.crop_start_x, self.crop_start_y,
                                                         self.crop_end_x, self.crop_end_y,
                                                         width=2, dash=(1, 10, 1), outline='red')

    def end_crop(self, event, type_='keep'):
        start_x, end_x, start_y, end_y = self.adapt_coordinates(self.crop_start_x, self.crop_end_x,
                                                                self.crop_start_y, self.crop_end_y, self.ratio)
        x = slice(start_x, end_x, 1)
        y = slice(start_y, end_y, 1)
        original_binary_label_2d = self.master.original_data_label_2d != 0
        processed_binary_label_2d = self.master.processed_data_label_2d != 0
        if type_ == 'keep':
            # Those checking are to make sure that any types of crop will not destroy any positive pixels
            if original_binary_label_2d.sum() == processed_binary_label_2d[y, x].sum():
                self.master.processed_image = self.master.processed_image[y, x]
                self.master.processed_data_label_2d = self.master.processed_data_label_2d[y, x]
                self.save_crop_process_info(type_, start_x, end_x, start_y, end_y)
        elif type_ == 'remove':
            if processed_binary_label_2d[y, x].sum() == 0:
                self.master.processed_image[y, x] = [255, 255, 255]
                self.save_crop_process_info(type_, start_x, end_x, start_y, end_y)
        else:
            self.master.processed_image = self.master.processed_image
        self.show_image()

    def save_crop_process_info(self, type_, start_x, end_x, start_y, end_y):
        act_id = str(len(self.master.process_info['actions']))
        self.master.process_info['actions'][act_id] = {}
        self.master.process_info['actions'][act_id]['crop'] = {
            'type': type_,
            'r_start': start_y, 'r_stop': end_y,
            'c_start': start_x, 'c_stop': end_x}

    def clear_canvas(self):
        self.canvas.delete("all")

    # def clear_draw(self):
    #     self.canvas.delete(self.draw_ids)

    # This function maps the crop coordinates into correct order for cropping
    def adapt_coordinates(self, crop_start_x, crop_end_x, crop_start_y, crop_end_y, ratio):
        if crop_start_x <= crop_end_x and crop_start_y <= crop_end_y:
            start_x = int(crop_start_x * ratio)
            start_y = int(crop_start_y * ratio)
            end_x = int(crop_end_x * ratio)
            end_y = int(crop_end_y * ratio)
        elif crop_start_x > crop_end_x and crop_start_y <= crop_end_y:
            start_x = int(crop_end_x * ratio)
            start_y = int(crop_start_y * ratio)
            end_x = int(crop_start_x * ratio)
            end_y = int(crop_end_y * ratio)
        elif crop_start_x <= crop_end_x and crop_start_y > crop_end_y:
            start_x = int(crop_start_x * ratio)
            start_y = int(crop_end_y * ratio)
            end_x = int(crop_end_x * ratio)
            end_y = int(crop_start_y * ratio)
        else:
            start_x = int(crop_end_x * ratio)
            start_y = int(crop_end_y * ratio)
            end_x = int(crop_start_x * ratio)
            end_y = int(crop_start_y * ratio)

        max_y, max_x = self.master.processed_image.shape[0], self.master.processed_image.shape[1]
        start_x = 0 if start_x < 0 else start_x
        start_y = 0 if start_y < 0 else start_y
        end_x = max_x if end_x > max_x else end_x
        end_y = max_y if end_y > max_y else end_y

        return start_x, end_x, start_y, end_y

    # This function helps to get new width and height of image for showing image
    def get_img_new_width_height_for_display(self, height, width):
        ratio = height / self.winfo_height() if height >= width else width / self.winfo_width()
        ratio = ratio if abs(ratio - 1.0) > 2.5 else 2.5
        new_width = width
        new_height = height
        if height > self.winfo_height() or width > self.winfo_width():
            if ratio < 1:
                new_width = self.winfo_width()
                new_height = int(new_width * ratio)
            else:
                new_height = self.winfo_height()
                new_width = int(new_height * (width / height))
        return new_height, new_width
