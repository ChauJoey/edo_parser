import logging
from datetime import datetime
import re
import numpy as np
import pandas as pd
from gspread_dataframe import get_as_dataframe

from google_base.QueryWrapper import QueryWrapper
from Decorators.SingletonDecorator import Singleton
from utils.PandasUtils import PandasUtils

logger = logging.getLogger("quart.app")


def printNow(tag=""):
    # 获取当前时间
    now = datetime.now()
    # 打印当前时间，格式为年-月-日 时:分:秒
    logger.info(now.strftime("%Y-%m-%d %H:%M:%S"), tag)


# 定义数据类型推断函数，现在也处理空值
def datetime_to_excel_serial(dt):
    delta = dt - datetime(1899, 12, 30)
    return float(delta.days) + (float(delta.seconds) + delta.microseconds / 1e6) / 86400.0


def determine_type(data):
    if pd.isna(data) or data == "":
        return 'stringValue'
    data = data.replace(",", "") if "," in data else data
    datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')  # 新增日期模式
    time_pattern = re.compile(r'^\d{2}:\d{2}$')
    number_pattern = re.compile(r'^\d+(\.\d+)?$')
    integer_pattern = re.compile(r'^\d+$')  # 增加整数模式

    if datetime_pattern.match(data) or date_pattern.match(data):
        return 'numberValue'
    elif time_pattern.match(data):
        return 'stringValue'
    elif number_pattern.match(data):
        if integer_pattern.match(data):
            return 'numberValue'
        return 'numberValue'
    else:
        return 'stringValue'


def determine_value(_type, data):
    if _type == 'stringValue':
        return str(data)
    if pd.isna(data) or data == "":
        return None  # 对空值使用 None 处理
    datetime_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')  # 新增日期模式
    time_pattern = re.compile(r'^\d{2}:\d{2}$')
    number_pattern = re.compile(r'^\d+(\.\d+)?$')
    integer_pattern = re.compile(r'^\d+$')  # 增加整数模式

    if datetime_pattern.match(data):
        dt = datetime.strptime(data, "%Y-%m-%d %H:%M")
        return datetime_to_excel_serial(dt)
    elif date_pattern.match(data):
        dt = datetime.strptime(data, "%Y-%m-%d")
        return datetime_to_excel_serial(dt)
    elif time_pattern.match(data):
        time_part = datetime.strptime(data, "%H:%M")
        # return (time_part.hour / 24.0 + time_part.minute / 1440.0)
        return data
    elif number_pattern.match(data):
        if integer_pattern.match(data):
            return int(data)  # 直接作为整数处理
        return float(data)  # 浮点数处理

    return str(data)  # 其他类型作为字符串处理


def infer_sheet_column_types(df):
    # 获取所有数据
    column_types = {}
    # 遍历DataFrame的每列
    for column in df.columns:
        # 过滤空值后应用determine_type，并获取最常见的数据类型
        non_empty_values = df[column][df[column].apply(lambda x: not pd.isna(x) and x != "")]
        if non_empty_values.empty:
            column_types[column] = 'stringValue'  # 如果整列都是空值，则标记为 'empty'
        else:
            types = [determine_type(val) for val in non_empty_values]
            most_common_type = pd.Series(types).mode()[0]
            column_types[column] = most_common_type

    return column_types


class WorksheetUtils(metaclass=Singleton):

    def __init__(self):
        pass

    @staticmethod
    def transWorkSheetToDataframeAllStr(worksheet) -> pd.DataFrame:
        # 应该用这个方法去读取所有包含公式的表格，转换为Dataframe
        # 获取包含计算结果的数据
        values_data = get_as_dataframe(worksheet, evaluate_formulas=True, headers=True, dtype=str).dropna(how='all')
        # 获取包含公式的数据
        formulas_data = get_as_dataframe(worksheet, evaluate_formulas=False, headers=True, dtype=str).dropna(how='all')
        # 初始化一个空DataFrame，用于存储公式列
        formulas_columns = pd.DataFrame(index=formulas_data.index)
        # 遍历所有列，检查是否包含公式
        for col in formulas_data.columns:
            # 检查该列是否包含公式，即以"="开始的字符串
            if formulas_data[col].str.startswith('=').any():
                # 创建一个新列来存储公式，列名为原列名后加"_FORMULA"
                formula_col_name = f"{col}_FORMULA"
                formulas_columns[formula_col_name] = formulas_data[col]
        # 将公式列合并到计算结果DataFrame中
        combined_df = pd.concat([values_data, formulas_columns], axis=1)
        combined_df.replace([np.inf, -np.inf, np.nan], ["", "", ""], inplace=True)
        # combined_df.replace('\u00A0', ' ')
        return combined_df.loc[:, ~combined_df.columns.str.contains('^Unnamed')]

    @staticmethod
    def transWorkSheetToDataframeAllStrTotal(worksheet) -> pd.DataFrame:
        qw = QueryWrapper()
        # 应该用这个方法去读取所有包含公式的表格，转换为Dataframe
        # 获取包含计算结果的数据
        values_data = get_as_dataframe(worksheet, evaluate_formulas=True, headers=True, dtype=str).dropna(how='all')
        # 获取包含公式的数据
        formulas_data = get_as_dataframe(worksheet, evaluate_formulas=False, headers=True, dtype=str).dropna(how='all')
        # 初始化一个空DataFrame，用于存储公式列
        formulas_columns = pd.DataFrame(index=formulas_data.index)
        # 遍历所有列，检查是否包含公式
        for col in formulas_data.columns:
            # 检查该列是否包含公式，即以"="开始的字符串
            if formulas_data[col].str.startswith('=').any():
                # 创建一个新列来存储公式，列名为原列名后加"_FORMULA"
                formula_col_name = f"{col}_FORMULA"
                formulas_columns[formula_col_name] = formulas_data[col]
        # 将公式列合并到计算结果DataFrame中
        combined_df = pd.concat([values_data, formulas_columns], axis=1)
        combined_df.replace([np.inf, -np.inf, np.nan], ["", "", ""], inplace=True)
        # combined_df.replace('\u00A0', ' ')
        df = combined_df.loc[:, ~combined_df.columns.str.contains('^Unnamed')]
        df = QueryWrapper.convertTimeColumnsToDatetime(df, qw)
        if qw.conditions:  # 如果有查询条件
            # 构建查询字符串和局部变量字典，然后执行查询
            queryStr, queryVars = qw.buildQuery()
            df = df.query(queryStr, local_dict=queryVars)
            df.replace([np.inf, -np.inf, np.nan], ['', '', ''], inplace=True)
        return df

    @staticmethod
    def transDataframeWithFormula(df):
        # 这个方法将包含A_Formula的Dataframe，用A_Formula列替换了A列，然后将A列写入到了GoogleSheet中
        # 步骤 1: 处理DataFrame
        formula_columns = [col for col in df.columns if col.endswith('_FORMULA')]
        for formula_col in formula_columns:
            original_col = formula_col.replace('_FORMULA', '')
            # 将_FORMULA列的值替换到原列
            if original_col in df.columns:
                df[original_col] = df[formula_col]
            # 删除_FORMULA列
            df.drop(columns=[formula_col], inplace=True)
        return df

    @staticmethod
    def useDataframeBatchUpdateSheet(worksheet, df, diyTypeMap=None):
        new_rows = df.shape[0] + 1  # 加1是因为标题行
        new_cols = df.shape[1]
        # 调整工作表大小以适应DataFrame
        worksheet.resize(rows=new_rows + 100, cols=new_cols + 40)
        formula_cols = [col for col in df.columns if df[col].astype(str).str.startswith('=').any()]
        df.replace([np.inf, -np.inf, np.nan], ['', '', ''], inplace=True)
        # 将df中的公式写入worksheet。
        requests = []  # 初始化请求列表
        max_row = worksheet.row_count
        max_col = worksheet.col_count
        # 更新单元格的请求
        typeMap = infer_sheet_column_types(df)
        if diyTypeMap:
            typeMap.update(diyTypeMap)
        for col_idx, col_name in enumerate(df.columns, start=1):  # 遍历列
            # 公式列直接跳过
            colDataType = typeMap.get(col_name, "stringValue")
            if col_name in formula_cols:
                continue
            for row_idx, value in enumerate(df[col_name], start=2):  # 遍历行，跳过标题行
                value = value.strip()
                cell_value = {colDataType: determine_value(colDataType, value)}
                cell_range = {
                    "sheetId": worksheet.id,
                    "startRowIndex": row_idx - 1,
                    "endRowIndex": row_idx,
                    "startColumnIndex": col_idx - 1,
                    "endColumnIndex": col_idx
                }
                vs = {"values": [{"userEnteredValue": cell_value}]}
                requests.append({
                    "updateCells": {
                        "range": cell_range,
                        "rows": [vs],
                        "fields": "userEnteredValue"
                    }
                })
        # 确定是否需要清空额外的行和列
        last_row = df.shape[0] + 1
        last_col = df.shape[1] + 1
        if last_row < max_row:
            # 添加清空DataFrame下方单元格的请求
            requests.append({
                "updateCells": {
                    "range": {
                        "sheetId": worksheet.id,
                        "startRowIndex": last_row,
                        "endRowIndex": max_row
                    },
                    "fields": "userEnteredValue"
                }
            })
        if last_col < max_col:
            # 添加清空DataFrame右侧单元格的请求
            requests.append({
                "updateCells": {
                    "range": {
                        "sheetId": worksheet.id,
                        "startColumnIndex": last_col,
                        "endColumnIndex": max_col
                    },
                    "fields": "userEnteredValue"
                }
            })
        # 执行batch_update操作
        body = {"requests": requests}
        worksheet.spreadsheet.batch_update(body)

    @staticmethod
    def updateSelectedRowsWithFormulaBatch(worksheet, df, queryWrapper):
        selected_rows_df = QueryWrapper.applyQuery(df, queryWrapper)
        if selected_rows_df.empty:
            return
            # 处理无效值
        df.replace([np.inf, -np.inf, np.nan], ['', '', ''], inplace=True)

        # 找出哪些列是公式列
        formula_cols = [col for col in df.columns if df[col].astype(str).str.startswith('=').any()]

        # 找出需要更新的行

        # 对选定的行应用更新
        requests = []  # 初始化请求列表
        for index, row in selected_rows_df.iterrows():
            index: int
            for col in df.columns:
                # 跳过公式列
                if col in formula_cols:
                    continue
                cell_type = "formulaValue" if col in formula_cols else "stringValue"
                cell_value = {cell_type: row[col]}
                cell_range = {
                    "sheetId": worksheet.id,
                    "startRowIndex": index + 1,
                    "endRowIndex": index + 2,
                    "startColumnIndex": df.columns.get_loc(col),
                    "endColumnIndex": df.columns.get_loc(col) + 1
                }
                requests.append({
                    "updateCells": {
                        "range": cell_range,
                        "rows": [{"values": [{"userEnteredValue": cell_value}]}],
                        "fields": "userEnteredValue"
                    }
                })

        # 执行batch_update操作
        body = {"requests": requests}
        worksheet.spreadsheet.batch_update(body)
        logger.info(len(requests))

    @staticmethod
    def updateSheetsEnoughSize(worksheet, newDfWithFormula):
        # newDf公式列就放的是公式，而不是公式计算结果，所以要转为公式
        # 表格大小不变、足够的的情况下
        originDf = WorksheetUtils.transWorkSheetToDataframeAllStr(worksheet)
        originDf = WorksheetUtils.transDataframeWithFormula(originDf)
        changedCells = PandasUtils.getChangedGoogleSheetCells(originDf, newDfWithFormula)
        if changedCells:
            logger.info(f"changed Cells {changedCells},length:{str(len(changedCells))}")
            PandasUtils.updateGoogleSheet(worksheet, changedCells)

    @staticmethod
    def addRowsToSheet(worksheet, newRecordsDf):
        targetDfWithFormula = WorksheetUtils.transDataframeWithFormula(
            WorksheetUtils.transWorkSheetToDataframeAllStr(worksheet))
        # 默认传进来的都是带公式列的
        newRecordsDfWithFormula = WorksheetUtils.transDataframeWithFormula(newRecordsDf)
        updated_target_df = pd.concat([targetDfWithFormula, newRecordsDfWithFormula], ignore_index=True)
        empty_rows_df = pd.DataFrame(
            index=range(len(targetDfWithFormula), len(targetDfWithFormula) + len(newRecordsDfWithFormula)),
            columns=targetDfWithFormula.columns)
        changedCells = PandasUtils.getChangedGoogleSheetCells(empty_rows_df, updated_target_df)
        # 调整工作表大小以适应DataFrame
        if changedCells:
            logger.info(f"changedCells {changedCells} :length{len(changedCells)} ")
            worksheet.resize(rows=updated_target_df.shape[0] + 1, cols=updated_target_df.shape[1])
            PandasUtils.updateGoogleSheet(worksheet, changedCells)
