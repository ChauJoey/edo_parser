import copy

import gspread
import numpy as np
from gspread import Worksheet
import pandas as pd
from pandas import DataFrame

from Decorators.SingletonDecorator import Singleton


class PandasUtils(metaclass=Singleton):

    def __init__(self):
        pass

    @staticmethod
    def transWorkSheetToDataframe(worksheet_data: Worksheet):
        # 假设第一行是列名
        wsData = worksheet_data.get_all_values()
        headers = wsData[0]
        # 剩余数据是数据行
        data = wsData[1:]
        # 创建DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df

    @staticmethod
    def replaceBlank(df: pd.DataFrame):
        df.replace([np.inf, -np.inf, np.nan], ["", "", ""], inplace=True)
        df.replace([pd.NaT, pd.NA], ["", ""])
        return df

    @staticmethod
    def getChangedGoogleSheetCells(oldDf, newDf, columnsFilter: list = None, ):
        oldDf = PandasUtils.replaceBlank(oldDf)
        newDf = PandasUtils.replaceBlank(newDf)
        # 用这个方法的时候,old df的结构一定要与GoogleSheets一致，即列的排列顺序要一致。
        # 对索引相同部分进行改造。
        common_columns = oldDf.columns.intersection(newDf.columns)
        common_index = oldDf.index.intersection(newDf.index)
        oldDfAligned = oldDf.loc[common_index, common_columns]
        newDfAligned = newDf.loc[common_index, common_columns]
        diff = newDfAligned.compare(oldDfAligned)
        # 找出公式列
        formula_cols = [col for col in oldDf.columns if oldDf[col].astype(str).str.startswith('=').any()]

        changed_cells = []

        # index不变、列名不变
        for index in diff.index:
            for col in diff.columns.get_level_values(0).unique():
                if columnsFilter and col not in columnsFilter:
                    continue

                if col in formula_cols:
                    continue  # 公式列则跳过
                if (col, 'self') in diff.columns and (col, 'other') in diff.columns:
                    if pd.isna(diff.loc[index, (col, 'self')]) and pd.isna(diff.loc[index, (col, 'other')]):
                        continue
                    else:

                        # 获取行号和列号（+1因为gspread是1索引）
                        row, column = index + 2, oldDf.columns.get_loc(col) + 1
                        # 获取新值
                        new_value = newDf.at[index, col]
                        if str(new_value) == 'NaT':
                            continue
                        # 创建单元格对象
                        cell = gspread.Cell(row, column, new_value)
                        changed_cells.append(cell)
        return changed_cells

    @staticmethod
    def updateDataframe(oldDf, fetchedData: dict, index: str, updateColumnList: list) -> DataFrame:
        """

        :param oldDf:这个是从google sheets里获得的数据框对象。
        :param fetchedData:这个是抓取的数据。是字典的形式。有两层，比如{"ctnNumber":{"event":'ok',"status":"ok" }}
        :param index:这个是google sheet里的ctnNumber对应的列的列名。也就是，你依据什么了数据（比如ctnNumber）去其他网站查了相关信息，这个信息在原表格里的列名。
        :param updateColumnList:这个是你从其他网站获得了什么数据。比如你从ONESTEP网站爬了Event，status，那么这里你就应该写【"Event","status"】
        :return:newDf，返回的是一个整合过了爬取的信息和原信息的数据框。
        """

        newDf = copy.deepcopy(oldDf)
        # 这个方法完成的是从googleSheet中获得的一个数据表内容和爬虫获取的数据进行整合，得到一个新的数据表结构。
        already = []  # ctnNumber这类key确保了不会重复，这里严格的保证了。
        for index, ctn in newDf[index].items():
            if ctn in fetchedData and ctn not in already:
                already.append(already)
                for col in updateColumnList:
                    newDf.at[index, col] = fetchedData[ctn][col]
        return newDf

    @staticmethod
    def updateGoogleSheet(workSheet: Worksheet, changedCells: list):
        if changedCells:
            # 将所有区别部分更新回googleSheets
            workSheet.update_cells(changedCells, value_input_option='USER_ENTERED')
        return

    @staticmethod
    def dataFrameToDict(df, key_cols):
        """
        将DataFrame转换为字典，特定列组合作为键，剩余列的列名和值构成的字典作为值。
        参数:
        - df: 要转换的pandas DataFrame。
        - key_cols: 作为键的列名列表。
        返回:
        - dict: 转换后的字典。
        """
        # 初始化结果字典
        result_dict = {}
        # 确定值列，即不在key_cols中的列
        value_cols = [col for col in df.columns if col not in key_cols]
        # 遍历DataFrame的每一行
        for index, row in df.iterrows():
            # 生成键：从key_cols中选取值，组成元组
            key = tuple(row[col] for col in key_cols)
            # 生成值：剩余列的列名和值构成的字典
            value = {col: row[col] for col in value_cols}
            # 将键值对添加到结果字典
            result_dict[key] = value
        return result_dict
