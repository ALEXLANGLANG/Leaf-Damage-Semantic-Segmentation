import sys

sys.path.append('../')

from skimage.transform import pyramid_gaussian
import os
import shutil

from yaml_io import read_from_yaml, write_to_yaml
import csv
import json
import numpy as np
from random import sample
from PIL import Image

_image_extensions = frozenset({'jpeg', 'jpg', 'png', 'tiff', 'tif'})


def absolute_path(path):
    return os.path.abspath(os.path.expanduser(path))


# Every name starting with a single '_' in name_list is expected
# to match a key of dictionary data_config without the initial '_'.
# If the first two characters of the name are both '_', then data_config must have
# an entry with key equal to the name without the two underscores, and the value of
# # that entry is a list. This will generate a list of names.
# For instance, if __species appears in the configuration file, then there must be
# a list data_config['species'] .
def dir_cat(name_list, config, data_config_field='data'):
    data_config = config[data_config_field]
    dir_list = ['']
    for name in name_list:
        if name[0] == '_':
            if name[1] == '_':
                names = data_config[name[2:]]
                dir_list = [os.path.join(d, n) for n in names for d in dir_list]
            else:
                dir_list = [os.path.join(d, data_config[name[1:]]) for d in dir_list]
        else:
            dir_list = [os.path.join(d, name) for d in dir_list]
    return dir_list


def data_roots(config):
    data_config = config['data']
    roots = dir_cat(data_config['files']['root'], config)
    species = data_config['species']
    assert len(roots) == len(species), 'root lists and species list have different lengths'
    return {species[k]: roots[k] for k in range(len(species))}


def experiment_root(config):
    return dir_cat(config['experiment']['files']['root'], config,
                   data_config_field='experiment')[0]


def labels_from_file(file_name):
    ids = {}
    with open(file_name, newline='') as file:
        reader = csv.DictReader(file, delimiter=',')
        for number, row in enumerate(reader):
            ids[row['class_name']] = {'number': number, 'color': row['class_color']}
    return ids


def string_to_rgb(string):
    return np.array([np.uint8(n) for n in string.split()])


def label_maps_original(config):
    suffix = dir_cat(config['data']['files']['label_ids_file'], config)
    assert len(suffix) == 1, 'One suffix expected, found {}'.format(len(suffix))
    suffix = suffix[0]
    maps_original = {species: labels_from_file(os.path.join(root, suffix))
                     for species, root in data_roots(config).items()}
    return maps_original



def data_directory_names(config):
    data_config = config['data']
    files = data_config['files']
    roots = data_roots(config)
    names = {}
    for file_type in ('input', 'label', 'info'):
        suffix = dir_cat(files['_'.join((file_type, 'subdir'))], config)[0]
        names[file_type] = {species: os.path.join(root, suffix) for species, root in roots.items()}
    return names


# create a directory if this dir does not exist
def try_create_dir(directory, verbose=True):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except:
            if verbose:
                print('create_dir: cannot makedirs for {}'.format(directory))
    else:
        pass


def experiment_root_to_store_weights(config):
    experiment_id = os.path.split(experiment_root(config))[1]
    root_to_store_weights = config['experiment']['files']['root_store_weights']
    new_root = os.path.join(root_to_store_weights, experiment_id)

    try_create_dir(new_root)
    return new_root


def experiment_directory_names(config, is_stored_in_other_disk=False):
    exp_config = config['experiment']
    files = exp_config['files']
    if is_stored_in_other_disk:
        root = experiment_root_to_store_weights(config)
    else:
        root = experiment_root(config)
    names = {}
    for file_type in ('training', 'validation', 'testing', 'info', 'weights', 'logs'):
        suffix = dir_cat(files['_'.join((file_type, 'subdir'))], config)[0]
        names[file_type] = os.path.join(root, suffix)
    return names


def ensure_directories(config, erase):
    dir_names = data_directory_names(config)
    for file_type, file_dict in dir_names.items():
        for path in file_dict.values():
            assert os.path.isdir(path), 'Did not find required data directory\n{}'.format(path)

    exp_path = experiment_root(config)
    exp_path_found = os.path.isdir(exp_path)

    if erase:
        if exp_path_found:
            print('Clearing experiment directory tree rooted at\n{}'.format(exp_path))
            shutil.rmtree(exp_path)
            exp_path_found = False
    else:
        if exp_path_found:
            print('Working in existing experiment root directory {}'.format(exp_path))

    if not exp_path_found:
        print('Making new experiment directory tree rooted at\n{}'.format(exp_path))
        dir_names = experiment_directory_names(config)
        for file_type, file_name in dir_names.items():
            if file_type in {'info', 'weights', 'logs'}:
                os.makedirs(file_name)
            else:
                label_subdirs = config['experiment']['files']['label_subdirs']
                for subdir in label_subdirs:
                    os.makedirs(os.path.join(file_name, subdir))


def is_path_file(path):
    try:
        return os.path.isfile(path)
    except:
        return False


def data_partition(ids, fractions):
    n_data = len(ids)
    n_train = np.uint(np.ceil(n_data * fractions['training']))
    n_validate = np.uint(np.floor(n_data * fractions['validation']))
    n_test = np.uint(n_data - n_train - n_validate)
    assert n_test > 0, 'Not enough data left for testing'

    # Random shuffle
    ids = sample(list(ids), n_data)

    n_split = n_train + n_validate
    splits = {'training': (0, n_train),
              'validation': (n_train, n_split),
              'testing': (n_split, n_data)}
    partition = {subset: ids[span[0]:span[1]] for subset, span in splits.items()}

    return partition


def number_of_tiles(image_size, tile_size, tile_margin):
    assert image_size >= tile_size, 'the tile is bigger than the image'
    tile_overlap = 2 * tile_margin
    tile_pitch = tile_size - tile_overlap
    assert tile_pitch > 0, 'too much overlap for this tile size'
    n_tiles = np.ceil((image_size - tile_overlap) / tile_pitch).astype(int)
    return n_tiles, tile_pitch


def image_tiles(image_file_name, species, name, t_columns, t_rows, t_margin):
    image = Image.open(image_file_name)
    i_columns, i_rows = image.width, image.height
    image.close()

    n_c, c_pitch = number_of_tiles(i_columns, t_columns, t_margin)
    n_r, r_pitch = number_of_tiles(i_rows, t_rows, t_margin)
    tiles = []
    r_start = (i_rows - t_rows) // 2 if n_r == 1 else 0
    for row in range(n_r):
        if n_r > 1 and row == n_r - 1:
            r_start = i_rows - t_rows
        r_stop = r_start + t_rows
        c_start = (i_columns - t_columns) // 2 if n_c == 1 else 0
        for column in range(n_c):
            if n_c > 1 and column == n_c - 1:
                c_start = i_columns - t_columns
            c_stop = c_start + t_columns
            tiles.append({'base name': name,
                          'species': species,
                          'ratio': None,
                          'row start': r_start, 'row stop': r_stop,
                          'column start': c_start, 'column stop': c_stop})
            c_start += c_pitch
        r_start += r_pitch
    return tiles, i_columns, i_rows


def list_image_files(directory):
    with os.scandir(directory) as entry_list:
        return [entry.name for entry in entry_list if entry.is_file() and entry.name[:2] != '._']


def base_name(file_name):
    tail = os.path.split(file_name)[1]
    return os.path.splitext(tail)[0]


def gen_common_ids(config):
    dir_names = data_directory_names(config)
    species_list = dir_names['input'].keys()
    common_ids, counts = None, {}
    file_ids = {}
    for file_type in dir_names.keys():
        file_ids[file_type] = {}
        for species in species_list:
            directory = dir_names[file_type][species]
            for file_name in list_image_files(directory):
                file_ids[file_type][os.path.join(species, base_name(file_name))] = os.path.join(directory, file_name)
        type_ids = set(file_ids[file_type].keys())
        common_ids = type_ids if common_ids is None else common_ids & type_ids
        counts[file_type] = len(type_ids)
    if len(common_ids) < max(counts.values()):
        print('WARNING: found {} unique (species, base name) pairs in common to'.format(len(common_ids)))
        print(', '.join(['{} ({} items)'.format(name, count) for name, count in counts.items()]))
        print('Using only common items')
    return dir_names, common_ids, file_ids


def make_full_partitions(config, dir_names, common_ids, file_ids, partition_ids=None):
    if partition_ids is None:
        partition_ids = data_partition(common_ids, config['experiment']['partition'])
    model_config = config['model']
    tile_width, tile_height = model_config['tile_width'], model_config['tile_height']
    tile_margin = model_config['tile_margin']
    data_lists = {}
    for phase, ids in partition_ids.items():
        data_lists[phase] = {'images': {}, 'tiles': []}
        for i in ids:
            species, name = os.path.split(i)
            entry = {'species': species}
            for file_type in dir_names.keys():
                entry[file_type] = file_ids[file_type][i]
            tiles, width, height = image_tiles(entry['input'], species, name, tile_width, tile_height, tile_margin)
            entry['width'], entry['height'] = width, height
            data_lists[phase]['images'][name] = entry
            data_lists[phase]['tiles'].extend(tiles)
    return data_lists


def get_partition_ids(partition):
    partition_ids = {}
    for phase in partition.keys():
        images_info = partition[phase]['images']
        partition_ids[phase] = [os.path.join(images_info[name]["species"], name) for name in images_info.keys()]
    return partition_ids


def make_data_lists(config, partition_ids=None):
    dir_names, common_ids, file_ids = gen_common_ids(config)
    data_lists = make_full_partitions(config, dir_names, common_ids, file_ids, partition_ids)
    return data_lists


def config_file_name(config):
    root = experiment_root(config)
    files = config['experiment']['files']
    return os.path.join(root, files['info_subdir'][0], files['config_file'])


def check_arguments(config_source, time, erase):
    config_source = absolute_path(config_source)
    if os.path.isfile(config_source):
        config = read_from_yaml(config_source, to_namespace=False)
        if time is None:
            config_destination = None
        else:
            base = os.path.splitext(os.path.split(config_source)[1])[0]
            #             if config['experiment']['id'] is None:
            config['experiment']['id'] = '_'.join((base, time))
            config_destination = config_file_name(config)
        msg = """a configuration file already exists in the experiment directory,
a different configuration file is specified, and overwrite is set to False.
Either specify the overwrite flag or change the experiment id in the
configuration file to create a new experiment directory"""
        assert (not is_path_file(config_destination)) or erase, msg
        return config, config_destination
    elif os.path.isdir(config_source):
        config_dir = os.path.join(config_source, 'info')
        config_file = os.path.join(config_dir, 'config.yml')
        condition = os.path.isdir(config_dir) and os.path.isfile(config_file)
        assert condition, 'Could not find configuration file {}'.format(config_file)
        config = read_from_yaml(config_file, to_namespace=False)
        config_destination = config_file_name(config)
        condition = absolute_path(config_file) == absolute_path(config_destination)
        msg = """The paths of the configuration file
{}
and of the configuration file specified in it,
{},
are different"""
        assert condition, msg.format(config_file, config_destination)
        return config, None
    else:
        raise OSError('Could not find file or directory {}'.format(config_source))


def main():
    pass


if __name__ == '__main__':
    main()
