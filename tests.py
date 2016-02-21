# -*- coding: utf-8 -*-
from __future__ import division
import unittest
from testfixtures import Replacer
from mock import Mock, mock_open, patch, call
import os
import sys

path = os.path.abspath(__file__)
sys.path.append(os.path.join(os.path.dirname(path), "../"))

from nausea.run import get_texts
from nausea.model import init_db, save, TextStats
from nausea.bl import get_text_stats, get_nausea_ratio, normalize_words, cleanup_words

__author__ = 'anna'


class MockQuery(object):
    def execute(self):
        pass


class NauseaTest(unittest.TestCase):
    def test_get_texts(self):
        mock_listdir = Mock(return_value=['a.txt', '.hidden.txt', 'dir'])
        mock_is_file = Mock(side_effect=lambda x: 'dir' not in x)
        with Replacer() as r:
            r.replace('os.listdir', mock_listdir)
            r.replace('os.path.isfile', mock_is_file)

            m_open = mock_open(read_data='Foo')
            with patch('nausea.run.open', m_open, create=True):
                texts = get_texts('test_path')
                mock_listdir.assert_called_once_with('test_path')
                mock_is_file.assert_has_calls([
                    call('test_path/a.txt'),
                    call('test_path/.hidden.txt'),
                    call('test_path/dir'),
                ])
                m_open.assert_called_once_with('test_path/a.txt', 'r')

                self.assertListEqual(texts, [('a.txt', 'Foo')])

    def test_init_db(self):
        mock_drop = Mock()
        mock_create = Mock()
        with Replacer() as r:
            r.replace('peewee.Model.drop_table', mock_drop)
            r.replace('peewee.Model.create_table', mock_create)
            r.replace('peewee.Model.table_exists', Mock(return_value=False))

            init_db()
            self.assertEqual(mock_create.call_count, 1)
            self.assertEqual(mock_drop.call_count, 0)

            r.replace('peewee.Model.table_exists', Mock(return_value=True))
            init_db()
            self.assertEqual(mock_create.call_count, 2)
            self.assertEqual(mock_drop.call_count, 1)

    def test_save(self):
        mock_init = Mock()
        mock_insert = Mock(return_value=MockQuery())
        with Replacer() as r:
            r.replace('nausea.model.init_db', mock_init)
            r.replace('peewee._atomic.__enter__', Mock())
            r.replace('peewee._atomic.__exit__', Mock())
            r.replace('peewee.Model.insert_many', mock_insert)

            save([])
            self.assertEqual(mock_init.call_count, 1)
            self.assertEqual(mock_insert.call_count, 0)

            save([('foo.txt', 0.2, False), None, ('bar.txt', 0.7, True)])
            self.assertEqual(mock_init.call_count, 2)
            mock_insert.assert_called_once_with(TextStats, [
                dict(id='foo.txt', nausea_ratio=0.2, is_fraud=False),
                dict(id='bar.txt', nausea_ratio=0.7, is_fraud=True)
            ])

    def test_get_text_stats(self):
        mock_cleanup = Mock(return_value=['foo', 'bar'])
        mock_normalize = Mock(return_value=(['foo', 'ba'], False))
        mock_get_ratio = Mock(return_value=0.2)
        with Replacer() as r:
            r.replace('nausea.bl.get_nausea_ratio', mock_get_ratio)
            r.replace('nausea.bl.normalize_words', mock_normalize)
            r.replace('nausea.bl.cleanup_words', mock_cleanup)

            get_text_stats([])
            self.assertEqual(mock_get_ratio.call_count, 0)
            self.assertEqual(mock_normalize.call_count, 0)
            self.assertEqual(mock_cleanup.call_count, 0)

            result = get_text_stats((1, 'Foo is Bar'))
            mock_cleanup.assert_called_once_with('Foo is Bar')
            mock_normalize.assert_called_once_with(['foo', 'bar'])
            mock_get_ratio.assert_called_once_with(['foo', 'ba'])

            self.assertEqual(result, (1, 0.2, False))

    def test_get_nausea_ratio(self):
        self.assertEqual(get_nausea_ratio([]), 0)
        self.assertEqual(get_nausea_ratio(['a', 'a', 'a']), 1)
        self.assertEqual(get_nausea_ratio(['a', 'a', 'b', 'c'], count=1), 0.5)

        input_data = 5 * ['a'] + 3 * ['b'] + 2 * ['c'] + 3 * ['d'] + 4 * ['e'] + ['f'] + 5 * ['g']
        self.assertEqual(get_nausea_ratio(input_data), (5 + 5 + 4 + 3 + 3) / (5 + 5 + 4 + 3 + 3 + 2 + 1))

    def test_normalize_words(self):
        test_data = [
            # words, result
            ([], ([], False)),
            ([u'простые', u'слова'], ([u'простые', u'слова'], False)),
            ([u'slovo', u'only', u'english'], ([u'slovo', u'only', u'english'], False)),
            ([u'slovo', u'слово', u'english'], ([u'slovo', u'slovo', u'english'], True)),
            ([u'слово', u'slovo', u'english'], ([u'slovo', u'slovo', u'english'], True)),
        ]
        with Replacer() as r:
            r.replace('nltk.stem.snowball.RussianStemmer.stem', Mock(side_effect=lambda x: x))

            for words, wait in test_data:
                self.assertEqual(normalize_words(words), wait)

    def test_cleanup_words(self):
        test_data = [
            # text, words
            (u'Самый простой текст. Вот!', [u'самый', u'простой', u'текст', u'вот']),
            (u'Стоп-слова: в по на!', [u'стоп-слова']),
            (u'Одни ----- \n ______ \n короткое слово a-', [u'одни', u'короткое', u'слово']),
            (u'Цифры 23 и 154', [u'цифры']),
        ]
        with Replacer() as r:
            r.replace('nltk.corpus.stopwords.words', Mock(return_value=[u'в', 'по', 'на']))

            for text, words in test_data:
                self.assertListEqual(cleanup_words(text), words)
