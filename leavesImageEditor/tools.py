import json
import os
import yaml
from PIL import Image
import numpy as np

from data_generator_imageEditor import check_arguments, gen_common_ids
from yaml_io import dict_to_namespace


def get_input_path_for_new_type(input_path, new_dir_type_='', new_file_type_=''):
    dir_, file_name = os.path.split(input_path)
    if len(new_file_type_) != 0:
        name, suffix = file_name.split('.')
        file_name = name + new_file_type_
    return os.path.join(dir_ + new_dir_type_, file_name)


def gen_all_data_ids(config='../../configs/config_all.yml'):
    '''
    Returns:
        common_ids: ids of images we can use
        file_ids: the path of images
    '''
    configuration, destination_file = check_arguments(config, None, None)
    config = configuration
    dir_names, common_ids, file_ids = gen_common_ids(config)
    return common_ids, file_ids


def read_from_yaml(filename, to_namespace=True):
    with open(filename, 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    if to_namespace:
        return dict_to_namespace(data)
    else:
        return data

def create_dir(directory, verbose=True):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except:
            if verbose:
                print('create_dir: cannot makedirs for {}'.format(directory))
    else:
        pass
        # print("Dir already exsits {}".format(directory))


def is_path_exist(new_path):
    return os.path.isfile(new_path)


def write_data_to_json_file(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def is_dir_exist(dir):
    return os.path.exists(dir)


def save_an_image(path, img):
    im = Image.fromarray(img)
    im.save(path)


def read_image_to_raw_array(path, resize_shape=None):
    if type(path) == str:
        try:
            with Image.open(path) as img:
                if resize_shape is not None:
                    img = img.resize(resize_shape)
                img, _ = get_raw_arrays(img)
                return img
        except:
            print("**** read_image: cannot find {}".format(path))
    elif type(path) == np.ndarray:
        return path
    else:
        print("**** read_image: invalid path {}".format(path))
    return None


def get_raw_arrays(image):
    """Extract index array and color map"""
    idx = np.array(image)
    palette = image.getpalette()
    if palette is None:
        lut = None
    else:
        #         lut = np.array(palette, dtype='uint8')
        lut = np.array(palette, dtype='uint8')
        lut = np.reshape(lut, (len(lut) // 3, 3))
    return idx, lut


def read_image_with_palette(path, resize_shape=None):
    try:
        with Image.open(path) as img:
            palette = img.getpalette()
            if resize_shape is not None:
                img = img.resize(resize_shape)
            idx = np.array(img)
            return idx, palette
    except:
        return None, None


def save_image_with_palette(path, img, palette):
    im = Image.fromarray(img)
    im.putpalette(palette)
    im.save(path)


def get_img_id(img_path):
    img_path = os.path.normpath(img_path)
    list_names = img_path.split(os.sep)
    if len(list_names) > 3:
        return os.path.join(list_names[-3], base_name(list_names[-1]))
    return None


def base_name(file_name):
    tail = os.path.split(file_name)[1]
    return os.path.splitext(tail)[0]


def get_dir_for_data_clean(img_path):
    """

    Args:
        img_path: if this is path like  ../../xxx/images/image,
        it will generate a directory like ../../xxx/images_clean
    Returns:

    """
    img_path = os.path.normpath(img_path)
    list_names = img_path.split(os.sep)
    assert len(list_names) >= 3, 'get_image_id: invalid path for image_id'
    list_names[-2] += '_clean'
    return os.path.join(*list_names[:-1])


def check_no_pos_losing(label_path, img_path, tolerance=100):
    original_label = read_image_to_raw_array(label_path) != 0
    original_img = read_image_to_raw_array(img_path)
    path_clean_label = get_input_path_for_new_type(label_path, new_dir_type_='_clean',
                                new_file_type_='.png')
    # path_clean_img = get_input_path_for_new_type(img_path, new_dir_type_='_clean',
    #                             new_file_type_='.jpeg')

    clean_label = read_image_to_raw_array(path_clean_label) != 0
    # clean_img = read_image_to_raw_array(path_clean_img)
    n_diff = abs(np.count_nonzero(clean_label) - np.count_nonzero(original_label))
    # if  n_diff > tolerance:
    #     print(n_diff)
    return n_diff > tolerance


def get_input_path_for_new_type(input_path, new_dir_type_='', new_file_type_=''):
    dir_, file_name = os.path.split(input_path)
    if len(new_file_type_) != 0:
        name, suffix = file_name.split('.')
        file_name = name + new_file_type_
    return os.path.join(dir_ + new_dir_type_, file_name)
