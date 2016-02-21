# -*- coding: utf-8 -*-
from __future__ import division
import re
from nltk.corpus import stopwords
from nltk.stem.snowball import RussianStemmer
from collections import Counter
from pytils import translit

__author__ = 'anna'


def cleanup_words(text):
    """
    Get words from text (exclude all punctuation and other symbols)
    Ignore if it is stop-word or len of word <= 2

    :param text:
    :return: list of words
    """

    words = []
    stopwords_ = set(stopwords.words('russian'))
    r_words = re.compile(u'[A-za-zА-Яа-яёЁ\-]+')
    for word in [w.lower() for w in r_words.findall(text)]:
        if word in stopwords_:
            continue
        if len(word) <= 2 or re.match(r'-+$', word) or re.match(r'_+$', word):
            continue
        words.append(word)
    return words


def normalize_words(words):
    """
    Merge word and his translit analog. If translit and normal word in text - we detect fraud
    Transform words in normal form

    :param words: list of words
    :return: (<list of normalize words>, <flag that detect or not fraud>)
    """

    tokens = []
    is_fraud = False
    set_words = set(words)
    for word in words:
        translit_word = translit.translify(word)
        if translit_word != word and translit_word in set_words:
            word = translit_word
            is_fraud = True
        tokens.append(RussianStemmer(ignore_stopwords=True).stem(word))
    return tokens, is_fraud


def get_nausea_ratio(words, count=5):
    """
    Get {count} most popular word in text and calculate Academic Nausea ratio:
    Summary frequency of those {count} words / summary frequency all words in text

    :param words: list of words
    :param count: count of popular
    :return: return float(ratio)
    """

    if not words:
        return 0
    popular_tokens = sorted(Counter(words).items(), key=lambda w_info: w_info[1], reverse=True)[:count]
    return sum([x[1] for x in popular_tokens]) / len(words)


def get_text_stats(text_info):
    """
    :param text_info:
    :return: (<file_name>, <academic nausea ratio>, <detect or not fraud>)
    """
    if not text_info:
        return

    id_, text = text_info
    tokens, is_fraud = normalize_words(cleanup_words(text))
    nausea_ratio = get_nausea_ratio(tokens)
    return id_, nausea_ratio, is_fraud
