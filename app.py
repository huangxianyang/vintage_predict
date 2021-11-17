# -*- coding: utf-8 -*-
# @Time    : 2021/9/7 5:23 下午
# @Author  : HuangSir
# @FileName: app.py
# @Software: PyCharm
# @Desc: vintage 预测

import pandas as pd

from model import (RepayPlanVintage, VintageProductBase, VintageIndustryBase,
                   VintageCashBase,VintageCompanyBase,VintageAllBase,
                   VintageFinance)

from utils.db import DB
from predict.vintage_predict import VintagePredict

db_url = 'oracle+cx_oracle://user:passwd@ip:port/sid'
db = DB(db_url)

# 基础数据跑批，比较耗时
print('start create base vintage dt ---------------------------------------------')
# RepayPlanVintage(db_url=db_url).create_table_dt()

# VintageProductBase(db_url=db_url).create_table_dt()
# VintageIndustryBase(db_url=db_url).create_table_dt()
# VintageCashBase(db_url=db_url).create_table_dt()
# VintageCompanyBase(db_url=db_url).create_table_dt()
VintageAllBase(db_url=db_url).create_table_dt()

print('finished create base vintage dt ---------------------------------------------')

print('start predict ---------------------------------------------------------------')
vintage_finance_df = pd.DataFrame()
for t in ['VINTAGE_PRODUCT_BASE', 'VINTAGE_INDUSTRY_BASE', 'VINTAGE_CASH_BASE','VINTAGE_COMPANY_BASE']:
# for t in ['VINTAGE_ALL_BASE']:
    sql = f"""SELECT * FROM RISKMART.{t} WHERE TENOR >= CURR_TENOR"""
    base_dt = db.query_df(sql)
    print(f'finished read base vintage，{t}:{base_dt.shape}\n')

    vp = VintagePredict(base_dt = base_dt,month_stamp = '202109')
    predict_dt = vp.predict()
    print(f'finished predict vintage:{t}:{predict_dt.shape}\n')
    vintage_finance_df = pd.concat([vintage_finance_df, predict_dt])

print('end predict ---------------------------------------------------------------')
vintage_finance_df.to_excel(f'./data/vintage_finance{str(202109)}.xlsx', index=False)

print('start insert ---------------------------------------------------------------')
vin = VintageFinance(db_url=db_url)
# 数据库初始化
vin.db_init()
# 添加观测月
vintage_finance_df['MONTH_STAMP'] = 202109
# 重置索引
vintage_finance_df.reset_index(drop=True, inplace=True)
# 结果写入
vin.write_vintage(vintage_dt=vintage_finance_df,month_stamp=202109)

