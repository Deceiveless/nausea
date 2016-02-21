# -*- coding: utf-8 -*-
from multiprocessing import Pool
import argparse
import os
import sys

path = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(path), "../"))
from nausea.model import save
from nausea.bl import get_text_stats

__author__ = 'anna'

parser = argparse.ArgumentParser(usage='run.py --samples-folder /etc/samples')


def get_texts(file_path):
    """
    :param file_path:
    :return: [(file_name, content)]
    """

    texts_ = []
    for file_name in os.listdir(file_path):
        if not os.path.isfile(os.path.join(file_path, file_name)) or file_name.startswith('.'):
            continue

        with open(os.path.join(file_path, file_name), 'r') as f:
            text = f.read().decode('utf-8')
        texts_.append((file_name, text))
    return texts_


if __name__ == '__main__':
    parser.add_argument('--samples-folder', dest='folder', required=True,
                        help="Folder with texts samples")
    options = parser.parse_args()

    texts = get_texts(options.folder)

    texts_stats = Pool().map(get_text_stats, texts)
    save(texts_stats)
