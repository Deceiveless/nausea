# -*- coding: utf-8 -*-

from peewee import *

__author__ = 'anna'

db = SqliteDatabase('./model/statistics.db')


class TextStats(Model):
    id = CharField()
    nausea_ratio = FloatField()
    is_fraud = BooleanField()

    class Meta:
        database = db


def init_db():
    """
    Drop table if exist and create new
    :return:
    """

    if TextStats.table_exists():
        TextStats.drop_table()
    TextStats.create_table()


def save(texts_stats):
    """
    Initialize table.
    Batch insert rows

    :param texts_stats:
    :return:
    """
    init_db()

    if not texts_stats:
        return

    data = [dict(id=stats[0], nausea_ratio=stats[1], is_fraud=stats[2])
            for stats in texts_stats if stats]
    with db.atomic():
        TextStats.insert_many(data).execute()
