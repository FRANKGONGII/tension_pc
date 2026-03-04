import sqlite3
from PO.input_data import inputManager
from utils.system_logger import get_logger

class DataManager:
    @staticmethod
    def queryTestDataByFormId(form_id):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        sql = '''SELECT displacement, force FROM test_data WHERE form_id = ?'''
        cursor.execute(sql, (form_id,))
        results = cursor.fetchall()
        conn.close()
        x_list = [row[0] for row in results]
        y_list = [row[1] for row in results]
        return x_list, y_list
    def __init__(self):
        self.init_db()


    def init_db(self):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_detail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_time TEXT,
                user TEXT,
                吊点代号 TEXT,
                出厂编号 TEXT,
                型号规格 TEXT,
                工作荷载 TEXT,
                位移方向 TEXT,
                总位移 TEXT,
                工作位移 TEXT,
                操作员 TEXT,
                检验员 TEXT,
                位移起始点值 TEXT,
                位移终止点值 TEXT,
                实测位移值 TEXT,
                超载试验值 TEXT,
                起止时间 TEXT,
                保持时间 TEXT,
                恒定度 TEXT,
                锁定位置 TEXT,
                载荷偏差度 TEXT,
                测试结果 TEXT,
                file_path TEXT
            )
        ''')

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS test_data (
                test_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 主键
                form_id INTEGER,                            -- 外键，关联主表
                displacement REAL,                          -- 测试位移
                force REAL,                                 -- 测试力
                FOREIGN KEY(form_id) REFERENCES test_detail(id) ON DELETE CASCADE
            )
            '''
        )
        conn.commit()
        conn.close()

    @staticmethod
    def queryById(data_id):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        sql = '''SELECT * FROM test_detail WHERE id = ?'''
        cursor.execute(sql, (data_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    @staticmethod
    def save_detail(data: inputManager):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        # print("first get and save", data)

        cursor.execute('''
            INSERT INTO test_detail (
                test_time, user, 吊点代号, 出厂编号, 型号规格, 工作荷载, 位移方向,
                总位移, 工作位移, 操作员, 检验员,
                位移起始点值, 位移终止点值, 实测位移值,
                超载试验值, 起止时间, 保持时间,
                恒定度, 锁定位置, 载荷偏差度, 测试结果
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get_value("test_time"),
            data.get_value("user"),
            data.get_value("吊点代号"),
            data.get_value("出厂编号"),
            data.get_value("型号规格"),
            data.get_value("工作载荷"),
            data.get_value("位移方向"),
            data.get_value("总位移"),
            data.get_value("工作位移"),
            data.get_value("操作员"),
            data.get_value("检验员"),
            data.get_value("位移起始点值"),
            data.get_value("位移终止点值"),
            data.get_value("实测位移值"),
            data.get_value("超载试验值"),
            data.get_value("起始-终止时间"),
            data.get_value("超载试验保持时间"),
            data.get_value("恒定度"),
            data.get_value("锁定位置"),
            data.get_value("载荷偏差度"),
            data.get_value("测试结果")
        ))

        conn.commit()
        conn.close()
        return cursor.lastrowid

    @staticmethod
    def update_file_path(form_id: int, file_path: str):
        """更新记录的打印文件完整路径"""
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE test_detail SET file_path = ? WHERE id = ?", (file_path, form_id))
        conn.commit()
        conn.close()

    @staticmethod
    def save_test_data(form_id: int, x_list: list, y_list: list):
        if len(x_list) != len(y_list):
            raise ValueError("x_list 和 y_list 长度不一致")
        # print(form_id)

        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        data_tuples = [(form_id, x, y) for x, y in zip(x_list, y_list)]
        cursor.executemany(
            '''
            INSERT INTO test_data (form_id, displacement, force)
            VALUES (?, ?, ?)
            ''',
            data_tuples
        )
        conn.commit()

    @staticmethod
    def queryByYear(year):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        # 构建SQL(通过年份查找)
        sql = f'''
               SELECT *
               FROM test_detail
               WHERE test_time LIKE ?
           '''
        params = [f"{year}%"]
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results

    @staticmethod
    def queryByYearAndUser(year, user):
        conn = sqlite3.connect("form_data.db")
        cursor = conn.cursor()
        # 构建SQL(通过年份查找)
        sql = f'''
               SELECT *
               FROM test_detail
               WHERE test_time LIKE ?
               AND user LIKE ?
           '''
        params = [f"{year}%", f"{user}%"]
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results

    @staticmethod
    def queryByYearAndFactoryNum(year, number):
        conn = sqlite3.connect("form_data.db")
        # print(number == None)
        cursor = conn.cursor()
        # 构建SQL(通过年份查找)
        sql = f'''
               SELECT *
               FROM test_detail
               WHERE test_time LIKE ?
               AND 出厂编号 LIKE ?
           '''
        params = [f"{year}%", f"{number}%"]
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        return results






