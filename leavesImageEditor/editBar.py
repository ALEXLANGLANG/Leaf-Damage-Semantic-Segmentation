import os
from tkinter import Frame, Button
from tkinter import filedialog
from tkinter.ttk import Label


from tools import is_path_exist, read_image_to_raw_array, is_dir_exist, create_dir, write_data_to_json_file, \
    save_an_image, \
    read_image_with_palette, save_image_with_palette, get_img_id, get_dir_for_data_clean, check_no_pos_losing, \
    get_input_path_for_new_type
from adjustFrame import AdjustFrame


class EditBar(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master=master)

        self.new_button = Button(self, text="Select")
        self.start_button = Button(self, text='Select All')
        self.text = Label(self, text=None)
        self.save_button = Button(self, text="Save & Next")
        self.crop_button = Button(self, text="Crop")
        self.adjust_button = Button(self, text="Adjust")
        self.remove_button = Button(self, text="Remove")
        self.clear_button = Button(self, text="Clear All")
        self.skip = []
        self.new_button.bind("<ButtonRelease>", self.new_button_released)
        self.start_button.bind("<ButtonRelease>", self.start_button_released)
        self.save_button.bind("<ButtonRelease>", self.save_button_released)

        self.crop_button.bind("<ButtonRelease>", self.crop_button_released)
        self.adjust_button.bind("<ButtonRelease>", self.adjust_button_released)
        self.remove_button.bind("<ButtonRelease>", self.remove_button_released)
        self.clear_button.bind("<ButtonRelease>", self.clear_button_released)

        self.new_button.grid(row=0, column=1, padx=0, pady=0)
        self.start_button.grid(row=0, column=2, padx=0, pady=0)
        self.save_button.grid(row=0, column=3, padx=0, pady=0)
        self.text.grid(row=0, column=4, padx=(0, 0), pady=0)
        self.crop_button.grid(row=0, column=5, padx=(0, 0), pady=0)
        self.adjust_button.grid(row=0, column=6, padx=0, pady=0)
        self.remove_button.grid(row=0, column=7, padx=0, pady=0)
        self.clear_button.grid(row=0, column=8, padx=0, pady=0)

    def new_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.new_button:
            if self.master.is_draw_state:
                self.master.image_viewer.deactivate_draw()
            if self.master.is_crop_state:
                self.master.image_viewer.deactivate_crop()

            filename = filedialog.askopenfilename()
            if filename is not None:
                img_id = get_img_id(filename)
                self.start_process_one_image(img_id)

    def start_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.start_button:
            if self.master.is_crop_state:
                self.master.image_viewer.deactivate_crop()
            self.start_all()

    @staticmethod
    def get_path_process_info(img_id, dir_process_info):
        dir_process_info = get_dir_process_info_for_one_image(img_id, dir_process_info)
        species, base_name = os.path.split(img_id)
        path_info = os.path.join(dir_process_info, base_name + '.json')
        return path_info

    def save_button_released(self, event):
        # 1. save image to corresponding directory
        # 2. save crop coordinates
        # 3. save threshold
        if self.winfo_containing(event.x_root, event.y_root) == self.save_button:
            if self.master.is_image_selected:
                if self.master.is_crop_state:
                    self.master.image_viewer.deactivate_crop()

                save_an_image(self.master.path_processed_image, self.master.processed_image)
                save_image_with_palette(self.master.path_processed_data_label, self.master.processed_data_label_2d,
                                        self.master.original_data_label_palette)
                # save_an_image(self.master.path_processed_data_label, self.master.processed_data_label_2d)

                dir_process_info = get_dir_process_info_for_one_image(self.master.img_id, self.master.dir_process_info)
                if not is_dir_exist(dir_process_info):
                    create_dir(dir_process_info)
                species, base_name = os.path.split(self.master.img_id)
                path_info = os.path.join(dir_process_info, base_name + '.json')
                msg = f'Save process info to {path_info}'
                print(msg)
                write_data_to_json_file(self.master.process_info, path_info)
                self.start_all()

    def crop_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.crop_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.image_viewer.deactivate_draw()
                else:
                    self.master.image_viewer.deactivate_crop()
                    self.master.image_viewer.activate_crop()

    def remove_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.remove_button:
            if self.master.is_image_selected:
                self.master.image_viewer.deactivate_crop()
                self.master.image_viewer.activate_remove()

    def adjust_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.adjust_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.image_viewer.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.image_viewer.deactivate_crop()

                self.master.adjust_frame = AdjustFrame(master=self.master)
                x = self.master.winfo_x()
                y = self.master.winfo_y()
                self.master.adjust_frame.geometry("+%d+%d" % (x, y))
                self.master.adjust_frame.grab_set()

    def clear_button_released(self, event):
        if self.winfo_containing(event.x_root, event.y_root) == self.clear_button:
            if self.master.is_image_selected:
                if self.master.is_draw_state:
                    self.master.image_viewer.deactivate_draw()
                if self.master.is_crop_state:
                    self.master.image_viewer.deactivate_crop()

                self.master.processed_image = self.master.original_image.copy()
                self.master.processed_data_label_2d = self.master.original_data_label_2d.copy()
                self.master.processed_data_label_2d = self.master.original_data_label_2d.copy()
                self.master.process_info['actions'] = {}
                self.master.image_viewer.show_image()

    def show_text(self, msg):
        self.text.configure(text=msg)

    def start_all(self):
        #    1) If it is processed. skip;
        #    2) otherwise. start processing

        for img_id in self.master.common_ids:
            species, name = os.path.split(img_id)
            path_original_image = self.master.file_ids['input'][img_id]
            path_processed_image = os.path.join(get_dir_for_data_clean(path_original_image), name + '.jpeg')
            path_process_info = EditBar.get_path_process_info(img_id, self.master.dir_process_info)
            path_data_label = self.master.file_ids['label'][img_id]
            dir_data_label = get_dir_for_data_clean(path_data_label)
            path_processed_data_label = os.path.join(dir_data_label, name + '.png')
            # print(path_process_info)
            # is_recheck = False
            # if img_id not in self.skip:
            #     self.skip.append(img_id)
            #     label_img_path = get_input_path_for_new_type(self.master.file_ids['label'][img_id], new_dir_type_='_clean',
            #                                                  new_file_type_='.png')
            #     is_recheck = check_no_pos_losing(self.master.file_ids['label'][img_id],
            #                                      label_img_path, tolerance=900)

            if not is_path_exist(path_processed_image) or not is_path_exist(path_process_info) or not is_path_exist(path_processed_data_label):
                self.start_process_one_image(img_id)
                return


        self.master.image_viewer.clear_canvas()

    def start_process_one_image(self, img_id):
        if img_id is None:
            return
        species, name = os.path.split(img_id)
        path_original_image = self.master.file_ids['input'][img_id]
        dir_processed_image = get_dir_for_data_clean(path_original_image)
        path_processed_image = os.path.join(dir_processed_image, name + '.jpeg')

        path_data_label = self.master.file_ids['label'][img_id]
        dir_data_label = get_dir_for_data_clean(path_data_label)
        path_processed_data_label = os.path.join(dir_data_label, name + '.png')

        if not is_dir_exist(dir_processed_image):
            create_dir(dir_processed_image)
        if not is_dir_exist(dir_data_label):
            create_dir(dir_data_label)

        image = read_image_to_raw_array(path_original_image)
        label_2d, palette = read_image_with_palette(path_data_label)
        # label_2d = read_image(path_data_label)
        # label_3d_bgr = cv2.imread(path_data_label)
        # label_3d = np.array(cv2.cvtColor(label_3d_bgr, cv2.COLOR_BGR2RGB))

        if image is not None and label_2d is not None:
            self.master.img_id = img_id
            self.master.path_original_image = path_original_image
            self.master.path_data_label = path_data_label
            self.master.path_processed_image = path_processed_image
            self.master.path_processed_data_label = path_processed_data_label

            self.master.original_image = image.copy()
            self.master.processed_image = image.copy()
            self.master.original_data_label_2d = label_2d.copy()  # This label is after mapping 3 to 2 dimension
            self.master.processed_data_label_2d = label_2d.copy()
            self.master.original_data_label_palette = palette
            self.master.process_info = {
                'img_id': img_id,
                'actions': {}
            }
            self.master.is_image_selected = True
            self.master.is_draw_state = False
            self.master.is_crop_state = False
            self.show_text(species + '/' + name)
            self.master.image_viewer.show_image()
            return True
        return False


def get_dir_process_info_for_one_image(img_id, dir_process_info):
    """

    Args:
        img_id:  (species, base_name)
        dir_process_info: the direcotry where the process info is

    Returns:
        the
    """
    assert type(img_id) == str, 'type of img_id should be str but'.format(type(img_id))

    species, base_name = os.path.split(img_id)
    dir = os.path.join(dir_process_info, species)
    return dir

