# -*- coding: utf-8 -*-
# @Time    : 2021/9/6 5:37 下午
# @Author  : HuangSir
# @FileName: db.py
# @Software: PyCharm
# @Desc:

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


class DB(object):
    '''数据库引擎对象'''

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def query_df(self, sql: str):
        """批查询,返回dataFrame"""
        with self.engine.connect() as conn:
            df = pd.read_sql_query(sql=sql, con=conn)
        return df

    def op_sql(self, sql: str):
        # 数据库操作,查询数据,以List返回
        sql_start = sql.strip()[:6].upper()  # SELECT
        with self.engine.connect() as conn:
            rep = conn.execute(sql)
            if sql_start == 'SELECT':
                res_list = rep.fetchall()
                res = [dict(i) for i in res_list]
                return res

    def drop_table(self, t_name: str):
        '''删表'''
        try:
            self.op_sql(f"""DROP TABLE RISKMART.{t_name}""")
        except Exception as error:
            print(f" WHEN DROP TABLE {t_name}, RAISE {str(error)}")

    def del_clear(self, tableModel):
        """
        清空表中数据,不删表
        :param tableModel: 表名
        :return:
        """
        DBSession = sessionmaker(bind=self.engine)
        with DBSession() as  session:
            session.query(tableModel).delete()
            session.commit()

    def add_data(self, ModelList):
        '''
        单条添加数据
        :param modelData:数据模型实例列表
        :return:
        '''
        DBSession = sessionmaker(bind=self.engine)
        with DBSession() as  session:
            session.add_all(ModelList)
            session.commit()
