# -*- coding: utf-8 -*-
# @Time    : 2021/9/7 4:53 下午
# @Author  : HuangSir
# @FileName: vintage_predict.py
# @Software: PyCharm
# @Desc: vintage 预测全量

import pandas as pd
from predict.vintage_predict_unit import VintagePredictUnit


class VintagePredict(object):
    """vintage预测，全量"""

    def __init__(self, base_dt: pd.DataFrame, month_stamp):
        self.base_dt = base_dt
        self.month_stamp = month_stamp

    def predict(self):
        """全量预测"""
        marks = self.base_dt['mark'].unique()
        tenors = self.base_dt['tenor'].unique()
        result = pd.DataFrame()
        for mark in marks:
            for tenor in tenors:
                base_df = self.base_dt.loc[(self.base_dt['mark'] == mark) & (self.base_dt['tenor'] == tenor),
                          :]

                # 单独预测样本：放款笔数较小(<30)月份，或 历史较久的样本
                base_df['old'] = base_df['loan_mth'].apply(lambda x:1 if float(x) < 201901 else 0)

                base_norma_df = base_df.loc[(base_df['loan_cnt'] >= 30) | (base_df['old'] == 0), :]
                base_unorma_df = base_df.loc[(base_df['loan_cnt'] < 30) | (base_df['old'] == 1), :]
                # 近期正常样本
                if not base_norma_df.empty:
                    del base_norma_df['old']
                    vpu = VintagePredictUnit(vintage_base_unit=base_norma_df, month_stamp=self.month_stamp)
                    predict_df = vpu.vintage_predict_unit()
                    predict_dt = vpu.vintage_stack_unit(predict_df)
                    result = pd.concat([result, predict_dt])
                # 远期或异常
                if not base_unorma_df.empty:
                    del base_unorma_df['old']
                    vpu = VintagePredictUnit(vintage_base_unit=base_unorma_df, month_stamp=self.month_stamp)
                    predict_df = vpu.vintage_predict_unit()
                    predict_dt = vpu.vintage_stack_unit(predict_df)
                    result = pd.concat([result, predict_dt])

        return result
