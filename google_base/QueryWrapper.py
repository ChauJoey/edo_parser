import pandas as pd


class QueryWrapper:
    def __init__(self):
        self.conditions = []

    def eq(self, column, value):
        if value:
            self.conditions.append((column, '==', value))
        else:
            self.isNullOrEmpty(column)
        return self

    def ne(self, column, value):
        if value:
            self.conditions.append((column, '!=', value))
        else:
            self.notNullEmpty(column)
        return self

    def gt(self, column, value):
        if value:
            self.conditions.append((column, '>', value))
        return self

    def lt(self, column, value):
        if value:
            self.conditions.append((column, '<', value))
        return self

    def dateGt(self, column, value):
        if value:
            self.conditions.append((column, '>', value))
        return self

    def dateLt(self, column, value):
        if value:
            self.conditions.append((column, '<', value))
        return self

    def dateGte(self, column, value):
        if value:
            self.conditions.append((column, '>=', value))
        return self

    def dateLte(self, column, value):
        if value:
            self.conditions.append((column, '<=', value))
        return self

    def gte(self, column, value):
        """添加一个大于等于的条件"""
        if value:
            self.conditions.append((column, '>=', value))
        return self

    def lte(self, column, value):
        """添加一个小于等于的条件"""
        if value:
            self.conditions.append((column, '<=', value))
        return self

    def inList(self, column, values):
        """添加一个'in'条件，检查列值是否在提供的列表中"""
        if values:
            self.conditions.append((column, 'in', values))
        return self

    def between(self, column, start_value, end_value):
        """添加一个时间范围的条件，检查列值是否在指定的开始和结束时间之间"""
        if start_value and end_value:
            self.conditions.append((column, '>=', start_value))
            self.conditions.append((column, '<=', end_value))
        return self

    def isNullOrEmpty(self, column):
        """添加一个列值为空或为空字符串的条件"""
        self.conditions.append((column, 'isnullorempty', None))
        return self

    def notInList(self, column, values):
        """检查列值是否不在给定的列表中"""
        if values:
            self.conditions.append((column, 'not in', values))
        return self

    def buildQuery(self):
        query_str = ''
        query_vars = {}
        for i, (col, op, val) in enumerate(self.conditions):
            if op == 'in':
                # 对于'in'操作，生成一个匹配列表的表达式
                vals = ','.join([f"'{v}'" for v in val])  # 将列表转换为字符串
                query_str += f"(`{col}` in [{vals}])"
            elif op == 'notnull':
                query_str += f"(`{col}`.notnull() & `{col}` != '')"
            elif op == 'isnullorempty':
                query_str += f"(`{col}`.isnull() | `{col}` == '')"
            else:
                query_str += f"(`{col}` {op} @{f'val{i}'})"
                query_vars[f"val{i}"] = val
            if i < len(self.conditions) - 1:
                query_str += ' & '
        return query_str, query_vars

    def notNullEmpty(self, column):
        """添加一个列值不为空的条件"""
        self.conditions.append((column, 'notnull', None))
        return self

    @staticmethod
    def convertTimeColumnsToDatetime(df, queryWrapper) -> pd.DataFrame:
        """识别并转换时间比较条件相关的列为datetime类型"""
        if queryWrapper.conditions:  # 如果有查询条件
            time_columns = set()  # 用于存储需要转换为datetime类型的列名
            for col, op, val in queryWrapper.conditions:
                try:
                    # 尝试将值转换为datetime，如果成功，则认为这是一个时间比较条件
                    import warnings
                    warnings.filterwarnings('ignore', category=UserWarning)
                    if not val:
                        continue
                    _ = pd.to_datetime(val, errors='raise')
                    time_columns.add(col)
                except ValueError:
                    # 如果转换失败，忽略这个异常，继续检查下一个条件
                    pass

            # 转换所有识别出的时间列
            for col in time_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')  # 使用'coerce'以处理无法转换的值

        return df

    @staticmethod
    def applyQuery(df: pd.DataFrame, queryWrapper=None, ) -> pd.DataFrame:
        # 条件为空直接返回
        if not queryWrapper or (not queryWrapper.conditions):
            return df
        df = QueryWrapper.convertTimeColumnsToDatetime(df, queryWrapper)
        if queryWrapper.conditions:  # 如果有查询条件
            # 构建查询字符串和局部变量字典，然后执行查询
            queryStr, queryVars = queryWrapper.buildQuery()
            df = df.query(queryStr, local_dict=queryVars)
            return df
        return df.astype(str)


if __name__ == "__main__":
    df = pd.read_table("../df.tsv", sep="\t")
    kwargs = {
        "operation": "ffcartageDailyReport",
        "ff": ["AGL LOGISTICS"],
        "fda": ["3b/8 Judge St, Sunshine VIC 3020 (SDL)"],
        "eta": "2024-09-05 12:00:00"
    }
    ffList = kwargs.get("ff", [])
    fdaList = kwargs.get("fda", [])
    eta = kwargs.get("eta", None)
    qw = QueryWrapper().notNullEmpty("ID").inList("Freight Forwarders", ffList).inList("FULL Deliver Address",
                                                                                       fdaList).dateGte("ETA",
                                                                                                        eta)
    newDf = QueryWrapper.applyQuery(df, qw)
    print(1)
