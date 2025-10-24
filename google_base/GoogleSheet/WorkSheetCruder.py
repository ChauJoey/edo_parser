from functools import wraps
from typing import List
import numpy as np
import pandas as pd
from gspread import Worksheet

from google_base.GoogleSheet.GoogleSheetClient import GoogleSheetClient
from google_base.QueryWrapper import QueryWrapper
from utils.WorksheetUtil import WorksheetUtils


def validateRecords(records, df, worksheet):
    for record in records:
        record: dict[str, str]
        keyList = list(record.keys())
        for key in keyList:
            if key not in df.columns:
                record.pop(key)
        # raise InternalException(f"{key}列在{worksheet.title}中不存在，无法插入。", "insertRecords")


def changed(func):
    # 所有可能对表格数据进行改变的方法都需要加这个装饰器。
    # 标记装饰器
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._needs_refresh = True
        print("更改了标志位")
        return result

    return wrapper


def refresh(func):
    # refresh 应用于可能需要最新数据的读取方法。
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._needs_refresh:
            print("不是最新数据")
            self.refreshWorkSheet()  # 假设这个方法负责重新获取 worksheet 对象
            self._needs_refresh = False
        result = func(self, *args, **kwargs)
        return result

    return wrapper



class WorkSheetCruder:
    def __init__(self, worksheetName: str):
        self._needs_refresh = False  # 初始化标志
        self.worksheet: Worksheet = GoogleSheetClient.getWorkSheet(worksheetName)

    def remove_duplicates(records: List[dict], df: pd.DataFrame, key_columns: List[str]) -> List[dict]:
        existing_combinations = set(df[key_columns].apply(tuple, axis=1).tolist())
        unique_records = []
        for record in records:
            record_combination = tuple(record[key] for key in key_columns)
            if record_combination not in existing_combinations:
                unique_records.append(record)
        return unique_records

    @refresh
    def getAllRecords(self) -> pd.DataFrame:
        # 计算公式的结果，将第一行设置为列名，删除列名为空的列，删除全部为空的行。
        return WorksheetUtils.transWorkSheetToDataframeAllStr(self.worksheet)

    @refresh
    def getRecordsByQueryWrapper(self, queryWrapper: QueryWrapper) -> pd.DataFrame:
        """根据QueryWrapper对象中的条件查询记录"""
        df = self.getAllRecords()
        df = QueryWrapper.convertTimeColumnsToDatetime(df, queryWrapper)
        if queryWrapper.conditions:  # 如果有查询条件
            # 构建查询字符串和局部变量字典，然后执行查询
            queryStr, queryVars = queryWrapper.buildQuery()
            df = df.query(queryStr, local_dict=queryVars)
            df.replace([np.inf, -np.inf, np.nan], ['', '', ''], inplace=True)
        return df

    @refresh
    @changed
    def insertRecords(self, records: List[dict], diyTypeMap=None) -> None:
        records = [{key: str(value) for key, value in record.items()} for record in records]  # 要转换为字符串类型
        """插入一条新记录"""
        df: pd.DataFrame = self.getAllRecords()
        validateRecords(records, df, self.worksheet)
        newRecordDf = pd.DataFrame(records)
        df = pd.concat([df, newRecordDf], ignore_index=True)
        df = WorksheetUtils.transDataframeWithFormula(df)
        WorksheetUtils.useDataframeBatchUpdateSheet(self.worksheet, df, diyTypeMap)
        return

    @refresh
    @changed
    def insertRecordsUnique(self, records: List[dict], diyTypeMap=None, key_columns: List[str] = None) -> None:
        records = [{key: str(value) for key, value in record.items()} for record in records]  # 要转换为字符串类型
        """插入一条新记录"""
        df: pd.DataFrame = self.getAllRecords()
        # 调用去重函数
        records = WorkSheetCruder.remove_duplicates(records, df, key_columns)
        validateRecords(records, df, self.worksheet)
        newRecordDf = pd.DataFrame(records)
        df = pd.concat([df, newRecordDf], ignore_index=True)
        df = WorksheetUtils.transDataframeWithFormula(df)
        WorksheetUtils.useDataframeBatchUpdateSheet(self.worksheet, df, diyTypeMap)
        return

    @refresh
    @changed
    def insertRecordsByDf(self, insertDf, diyTypeMap=None) -> None:
        """插入一条新记录"""
        if diyTypeMap is None:
            diyTypeMap = {}
        df: pd.DataFrame = self.getAllRecords()
        df = pd.concat([df, insertDf], ignore_index=True, join="inner")
        df = WorksheetUtils.transDataframeWithFormula(df)
        WorksheetUtils.useDataframeBatchUpdateSheet(self.worksheet, df, diyTypeMap)
        return

    @refresh
    @changed
    def deleteRecordByQueryWrapper(self, queryWrapper: QueryWrapper) -> None:
        """根据QueryWrapper对象中的条件删除记录"""
        df = self.getAllRecords()
        df = QueryWrapper.applyQuery(df, queryWrapper)
        df = WorksheetUtils.transDataframeWithFormula(df)
        WorksheetUtils.useDataframeBatchUpdateSheet(self.worksheet, df.reset_index(drop=True))
        return

    def refreshWorkSheet(self):
        print("获取最新数据中")
        client = GoogleSheetClient.getGlobalGoogleSheetClient()
        self.worksheet = client.getWorkSheet(self.worksheet.title)
        print("最新数据获取完成了")


if __name__ == "__main__":
    cruder = WorkSheetCruder("TEST2")
    # 新增
    records = [{"ID1": 10, "FORMULA": 3}, {"ID1": 3, "FORMULA": 8}]
    cruder.insertRecords(records)
    # 查找
    qw = QueryWrapper().eq("ID", "10")
    result = cruder.getRecordsByQueryWrapper(qw)
    print("查询的结果:", result)
