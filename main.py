"""
@File: main.py
@Author: 秦宇
@Created: 2023/11/4 0:40
@Description: Created in 爬虫-咸鱼-XHSAUTO后台管理.
"""
import os
import getpass
import requests
import pymysql
from typing import Iterable, List, Dict
from datetime import datetime
from tabulate import tabulate
from config import *


class Timer:
    @staticmethod
    def get_current_time(type_: str = 'datetime'):
        now = datetime.now()
        if type_ == 'str':
            return now.strftime('%Y-%m-%d %H:%M:%S')
        elif type_ == 'datetime':
            return now
        else:
            return None


class text:
    def __init__(self, text, display='default', fore='white', back='none'):
        display_modes = {'default': 0, 'highlight': 1, 'underline': 4, 'inverse': 7}
        foreground_colors = {'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'magenta': 35, 'cyan': 36,
                             'white': 37}
        background_colors = {'black': 40, 'red': 41, 'green': 42, 'yellow': 43, 'blue': 44, 'magenta': 45, 'cyan': 46,
                             'white': 47}
        self.text = text
        self.display_code = display_modes.get(display, 0)
        self.foreground_code = foreground_colors.get(fore, 37)
        self.background_code = background_colors.get(back, None)

    def __repr__(self):
        if self.background_code:
            return f"\033[{self.display_code};{self.foreground_code};{self.background_code}m{self.text}\033[0m"
        return f"\033[{self.display_code};{self.foreground_code}m{self.text}\033[0m"


class DBTool:
    def __init__(self, config: dict):
        self.db_config = config

    def __enter__(self):
        self.connection = pymysql.connect(**self.db_config)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

    def execute(self, query, params=None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"Error executing query: {e}")
            self.connection.rollback()

    def insert(self, table: str, data: dict):
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({keys}) VALUES ({values})"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                self.connection.commit()
        except pymysql.Error as e:
            print(f"Error inserting data: {e}")
            self.connection.rollback()

    def update(self, table: str, data: dict, condition: str):
        set_values = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table} SET {set_values} WHERE {condition}"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, tuple(data.values()))
                self.connection.commit()
        except pymysql.Error as e:
            print(f"Error updating data: {e}")
            self.connection.rollback()

    def delete(self, table: str, condition: str):
        query = f"DELETE FROM {table} WHERE {condition}"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
        except pymysql.Error as e:
            print(f"Error deleting data: {e}")
            self.connection.rollback()

    def select(self, table: str, columns: Iterable, condition: str = None, count: int = 0):
        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table}"
        if condition:
            query += f" WHERE {condition}"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if count <= 0:
                    return cursor.fetchall()
                elif count == 1:
                    return cursor.fetchone()
                else:
                    return cursor.fetchmany(count)
        except pymysql.Error as e:
            print(f"Error selecting data: {e}")
            self.connection.rollback()


class ConfigViewer:
    def __init__(self, baseAPI: str, token: str | None):
        self.baseAPI = baseAPI
        self.token = token

    def show_json(self):
        if not self.token:
            print("System：无权限操作")
            return

        headers = {'Authorization': f'Bearer {self.token}'}

        while True:
            if self.ask_yes_no("是否查看有哪些用户？[Y/n] "):
                users = self.get_users(headers)
                if users:
                    self.print_users(users)
                    uname = input("查看哪位用户的配置？[输入用户名] ")
                    if uname:
                        jsons = self.get_user_jsons(headers, uname)
                        if jsons:
                            self.print_jsons(jsons)
                            spider_name = input("选择查看哪个爬虫的配置？[输入爬虫名] ")
                            if spider_name:
                                file_json = self.get_spider_json(headers, uname, spider_name)
                                self.print_spider_json(file_json)
            else:
                break

    def ask_yes_no(self, question: str) -> bool:
        option = input(question).lower()
        return option != "n"

    def get_users(self, headers: dict) -> List[str]:
        response = requests.get(url=f"{self.baseAPI}/admin/json", headers=headers)
        return response.json().get("data", [])

    def print_users(self, users: List[str]):
        print(tabulate(enumerate(users), headers=["序号", "用户名"], tablefmt="grid"))

    def get_user_jsons(self, headers: dict, uname: str) -> List[str]:
        data = {"uname": uname}
        response = requests.post(url=f"{self.baseAPI}/admin/json", data=data, headers=headers)
        return response.json().get("data", [])

    def print_jsons(self, jsons: List[str]):
        print(tabulate(enumerate(jsons), headers=['序号', '爬虫名'], tablefmt="grid"))

    def get_spider_json(self, headers: dict, uname: str, spider_name: str) -> Dict[str, str]:
        data = {"uname": uname, "spider_name": spider_name}
        response = requests.post(url=f"{self.baseAPI}/admin/v/json", data=data, headers=headers)
        return response.json().get("data", {})

    def print_spider_json(self, file_json: Dict[str, str]):
        for key, val in file_json.items():
            print(f'{text(key, fore="blue")}', '->', val)


class AdminTool:
    def __init__(self, config: dict):
        self.config = config
        self.baseAPI = BASE_API
        self.menu = {
            '1': (self.main_menu, '查看菜单'),
            '2': (self.add_user, '添加用户'),
            '3': (self.view_users, '查看用户'),
            '4': (self.delete_user, '删除用户'),
            '5': (self.promote_user, '升降权限'),
            '6': (self.change_limit, '修改限额'),
            '7': (self.modify_account, '修改账号'),
            '8': (self.change_password, '修改密码'),
            '9': (self.ban_user, '解禁封禁'),
            '10': (self.show_json, '查看配置'),
        }
        self.token = None
        self.jsonViewer = ConfigViewer(self.baseAPI, self.token)
        self.identities = {False: '用户', True: '管理员'}
        self.userStates = {False: '正常', True: '已封禁'}

    def login(self, username, password):
        try:
            response = requests.post(
                url=f'{self.baseAPI}/admin/login',
                data={
                    'uname': username,
                    'upwd': password
                }
            )
            self.token = response.json().get('token')
            return bool(response.status_code == 200 and response.json()['success']), response.json()['msg']
        except Exception:
            return False, '当前无法登录，请检查网络服务'

    def main_menu(self):
        print(text("用户管理菜单".center(30, '-'), fore="yellow"))
        for option, item in self.menu.items():
            print(f"{option} {item[-1]}".center(15), end='')
            if int(option) % 2 == 0:
                print()
        print(f"输入 q|0|exit 可退出系统".center(30), end='\n')
        print(f"输入 cls 可清除屏幕信息".center(30), end='\n')

    def add_user(self):
        try:
            user_data = {
                'uname': input(text('设定账号：', fore='yellow')).replace(" ", ''),
                'upwd': input(text('设定密码：', fore='yellow')).replace(" ", ''),
                'max_limit': int(input(text('设定额度：', fore='yellow'))),
            }
            if not (user_data['uname'] and user_data['upwd']):
                return print(f'{text("System：", fore="blue")}账号、密码不能为空')
            if user_data['max_limit'] < 0:
                return print(f'{text("System：", fore="blue")}额度不能设置为负值')
            if input('确定设定新用户？[Y/n]').lower() == 'n':
                return
            response = requests.post(url=f'{self.baseAPI}/user/register', data=user_data)
            print(f'{text("System：", fore="blue")}{response.json().get("msg")}')
        except Exception as e:
            print(f'{text("System：", fore="blue")}{e}')

    def view_users(self):
        uname = input('查询账号（回车查看全部）：').replace(" ", '')
        with DBTool(self.config) as db:
            result = db.select('users', ('uname', 'max_limit', 'is_admin', 'is_disabled'),
                               f'uname={uname!r}' if uname else None)
            result = list(map(lambda x: list(x), result))
            for i in range(len(result)):
                result[i][2] = self.identities[result[i][2]]
                result[i][3] = self.userStates[result[i][3]]
            headers = ['账号', '额度', '身份', '状态']
            print(tabulate(result, headers=headers, tablefmt='grid'))

    def delete_user(self):
        uname = input('输入要删除的用户账号：')
        with DBTool(self.config) as db:
            user = db.select('users', ('uname',), f'uname={uname!r}', count=1)
            if not user:
                print(f"{text('System：', fore='blue')}用户 {uname} 不存在")
                return
            confirm = input(f"确定要删除用户`{user[0]}`? [Y/n] ").lower()
            if confirm == 'n':
                return
            db.delete('users', f'uname={uname!r}')
            print(f"{text('System：', fore='blue')}成功删除用户`{user[0]}`")

    def promote_user(self):
        uname = input('输入升降权限的用户账号：')
        with DBTool(self.config) as db:
            user = db.select('users', ('uname', 'is_admin'), f'uname={uname!r}', count=1)
            if not user:
                print(f"{text('System：', fore='blue')}用户 {uname} 不存在")
                return
            target = self.identities[not user[1]]
            confirm = input(f"确定要将用户 {user[0]} 改变为 {target} ? [Y/n] ").lower()
            if confirm == 'n':
                return
            db.update('users', {'is_admin': int(not user[1])}, f'uname={uname!r}')
            print(f"{text('System：', fore='blue')}成功将用户 {user[0]} 改变为 {target}")

    def change_limit(self):
        uname = input('输入要修改额度的用户账号：')
        new_limit = int(input('输入新的额度：'))
        with DBTool(self.config) as db:
            user = db.select('users', ('uname',), f'uname={uname!r}', count=1)
            if not user:
                print(f"{text('System：', fore='blue')}用户 {uname} 不存在")
                return
            db.update('users', {'max_limit': new_limit}, f'uname={user[0]!r}')
            print(f"{text('System：', fore='blue')}成功将用户 {user[0]} 的额度更改为 {new_limit}")

    def modify_account(self):
        uname = input('输入要修改账号的用户账号：')
        new_uname = input('输入新的账号：')
        with DBTool(self.config) as db:
            user = db.select('users', ('uname',), f'uname={uname!r}', count=1)
            if not user:
                print(f"{text('System：', fore='blue')}用户 {uname} 不存在")
                return
            db.update('users', {'uname': new_uname}, f'uname={user[0]!r}')
            print(f"{text('System：', fore='blue')}成功将用户 {user[0]} 的账号更改为 {new_uname}")

    def change_password(self):
        try:
            user_data = {
                'uname': input('输入要修改账号的用户账号：').replace(' ', ''),
                'upwd': input('输入新的密码：').replace(' ', ''),
            }
            if not (user_data['uname'] and user_data['upwd']):
                return print(f'{text("System：", fore="blue")}账号、密码不能为空')
            headers = {
                'Authorization': f'Bearer {self.token}'
            }
            if not self.token:
                return print(f'{text("System：", fore="blue")}无权限操作')
            response = requests.post(
                url=f'{self.baseAPI}/admin/password',
                data=user_data,
                headers=headers
            )
            print(f"{text('System：', fore='blue')}{response.json().get('msg')}")
        except Exception as e:
            print(f'{text("System：", fore="blue")}{e}')

    def ban_user(self):
        uname = input('输入要封禁/解封的用户账号：')
        with DBTool(self.config) as db:
            user = db.select('users', ('uname', 'is_disabled'), f'uname={uname!r}', count=1)
            if not user:
                print(f"{text('System：', fore='blue')}用户 {uname} 不存在")
                return
            db.update('users', {'is_disabled': not user[1]}, f'uname={user[0]!r}')
            action = "封禁" if not user[1] else "解封"
            print(f"{text('System：', fore='blue')}成功{action}用户 {user[0]}")

    def show_json(self):
        self.jsonViewer.token = self.token
        self.jsonViewer.show_json()

    def run(self):
        os.system('cls')
        while True:
            admin_username = input("管理员账号> ").replace(' ', '')
            admin_password = getpass.getpass('管理员密码> ').replace(' ', '')
            if not admin_username or not admin_password:
                return
            os.system('cls')
            state, msg = self.login(admin_username, admin_password)
            print(f"{text('System：', fore='blue')}{msg}")
            if state:
                break
        self.main_menu()
        while True:
            option = input(text('>>> ', fore='blue'))
            if option.lower() in ('0', 'q', 'exit', 'quit'):
                print(f'{text("System：", fore="blue")}退出系统...')
                break
            if option == 'cls':
                os.system('cls')
                self.main_menu()
                continue
            self.menu.get(option, (lambda: print(f'{text("System：", fore="blue")}你输入的选项无效'), '输入无效'))[0]()
            print()


if __name__ == "__main__":
    admin_tool = AdminTool(DATABASE_PARAMS)
    admin_tool.run()
