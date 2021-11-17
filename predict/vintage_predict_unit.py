# -*- coding: utf-8 -*-
# @Time    : 2021/9/7 1:22 下午
# @Author  : HuangSir
# @FileName: vintage_predict.py
# @Software: PyCharm
# @Desc: vintage预测

import pandas as pd
import copy
import numpy as np


class VintagePredictUnit(object):
    """vintage预测，mark单元"""

    def __init__(self, vintage_base_unit: pd.DataFrame, month_stamp):
        self.vintage_base = vintage_base_unit
        self.month_stamp = month_stamp

    def vintage_unstack_unit(self):
        """将原始vintage数据拉平"""
        df = copy.deepcopy(self.vintage_base)
        # 填充, 当月无任何账期到期
        df.loc[df['loan_mth'] == self.month_stamp, :] = df.loc[df['loan_mth'] == self.month_stamp, :].fillna(value=0)
        # 拉平vintage数据
        df = pd.pivot_table(data=df, values='bad_ratio',
                            index=['mark', 'tenor', 'loan_mth', 'loan_amt', 'loan_cnt'],
                            columns='curr_tenor', aggfunc='max', dropna=True)
        # 重置索引
        df.reset_index(drop=False, inplace=True)
        # 还原当月数据
        df.loc[df['loan_mth'] == self.month_stamp, :] = df.loc[df['loan_mth'] == self.month_stamp, :].replace(
            {0.: np.nan})
        # 修改列名并大写
        rcn = {k: 'MOB_' + str(k) if str(k).isdigit() else k.upper() for k in df.columns.tolist()}
        df.rename(columns=rcn, inplace=True)
        # 按照放款月排序
        df.sort_values(by='LOAN_MTH', ascending=True, inplace=True, ignore_index=True)

        return df

    def vintage_increment_unit(self):
        """vintage增量报表"""
        base_df = self.vintage_unstack_unit()
        increase_df = copy.deepcopy(base_df)

        # 第一行和MOB_1增量
        mob_cols = [i for i in base_df.columns if 'MOB' in i]
        for col in mob_cols:
            if col == 'MOB_1':  # 第一列
                increase_df.loc[:, col] = np.nan
            else:  # 第一行其他列
                i = int(col.replace('MOB_', ''))
                increase_value = 0 if str(base_df.loc[0, col]) == 'nan' else base_df.loc[0, f'MOB_{i}'] - base_df.loc[
                    0, f'MOB_{i - 1}']
                increase_df.loc[0, col] = 0 if increase_value < 0 else increase_value

        # 第二行及以上增量
        mob_cols = [i for i in base_df.columns if 'MOB' in i and i != 'MOB_1']
        for col in mob_cols:
            i = int(col.replace('MOB_', ''))
            for ind in base_df.loc[1:].index:
                if str(base_df.loc[ind, col]) == 'nan':
                    increase_value = np.mean(increase_df.loc[ind - 6:ind - 1, col])
                else:
                    increase_value = base_df.loc[ind, f'MOB_{i}'] - base_df.loc[ind, f'MOB_{i - 1}']
                increase_df.loc[ind, col] = 0 if increase_value < 0 else increase_value
        return increase_df

    def vintage_predict_unit(self):
        """vintage预测报表"""
        base_df = self.vintage_unstack_unit()
        increase_df = self.vintage_increment_unit()
        predict_df = copy.deepcopy(base_df)

        # 预测MOB_1
        for ind in base_df.index:
            if str(base_df.loc[ind, 'MOB_1']) != 'nan':
                predict_value = base_df.loc[ind, 'MOB_1']
            elif ind <= 1:
                predict_value = np.mean(base_df.loc[0, 'MOB_1'])
            else:
                predict_value = np.mean(base_df.loc[ind - 6:ind - 1, 'MOB_1'])

            predict_df.loc[ind, 'MOB_1'] = 0 if predict_value < 0 else predict_value

        # 预测MOB2及以上
        mob_cols = [i for i in base_df.columns if 'MOB' in i and i != 'MOB_1']
        for col in mob_cols:
            i = int(col.replace('MOB_', ''))
            for ind in base_df.index:
                if str(base_df.loc[ind, col]) != 'nan':
                    predict_value = base_df.loc[ind, col]
                else:
                    predict_value = predict_df.loc[ind, f'MOB_{i - 1}'] + increase_df.loc[ind, f'MOB_{i}']
                predict_df.loc[ind, col] = 0 if predict_value < 0 else predict_value
        return predict_df

    def vintage_stack_unit(self, predict_df: pd.DataFrame):
        """压缩"""
        keys = ['MARK', 'TENOR', 'LOAN_MTH', 'LOAN_AMT', 'LOAN_CNT']
        # 转置
        df = predict_df.set_index(keys=keys).stack(dropna=False).reset_index()
        # 处理期数
        df = df.rename(columns={'level_5': 'CURR_TENOR', 0: 'P_1'})
        df.columns = [i.upper() for i in df.columns]
        df['CURR_TENOR'] = df['CURR_TENOR'].apply(lambda x: int(str(x).replace('MOB_', '')))
        return df
