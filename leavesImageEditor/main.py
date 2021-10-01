import os
import tkinter as tk
from tkinter import ttk


from editBar import EditBar
from imageViewer import ImageViewer
from tools import read_from_yaml, gen_all_data_ids


def get_dir_process_info(config_file='../../configs/config_all.yml'):
    if os.path.isfile(config_file):
        config = read_from_yaml(config_file, to_namespace=False)
    return config['data']['dir_process_info']

class Main(tk.Tk):

    def __init__(self, configuration='./config_image_editor.yml'):
        tk.Tk.__init__(self)
        self.config = configuration

        self.common_ids, self.file_ids = gen_all_data_ids(configuration)
        self.dir_process_info = get_dir_process_info(configuration)

        self.filename = ""
        self.img_id = None

        self.original_image = None
        self.processed_image = None
        self.path_original_image = None
        self.path_processed_image = None

        self.original_data_label_2d = None  # This 2d image is to calculate if cropping or removing any areas including positive pixels
        self.processed_data_label_2d = None
        self.original_data_label_palette = None
        self.original_data_label_3d = None  # Will save 3d data_augmentation to our device.
        self.processed_data_label_3d = None
        self.path_data_label = None
        self.path_processed_data_label = None

        self.process_info = {'img_id': None,
                             'actions': {}
                             }

        self.is_image_selected = False
        self.is_draw_state = False
        self.is_crop_state = False
        self.adjust_frame = None

        self.title("Leaves Image Editor")
        self.editbar = EditBar(master=self)
        separator1 = ttk.Separator(master=self, orient=tk.HORIZONTAL)
        self.image_viewer = ImageViewer(master=self)

        self.editbar.pack(pady=10)
        separator1.pack(fill=tk.X, padx=10, pady=5)
        self.image_viewer.pack(fill=tk.BOTH, padx=10, pady=10, expand=1)



