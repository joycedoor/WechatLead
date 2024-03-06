import os
import shutil
import hashlib
import hmac
from Cryptodome.Cipher import AES
import sqlite3
import time
import datetime
import re

SQLITE_FILE_HEADER = "SQLite format 3\x00"  # SQLite文件头

KEY_SIZE = 32
DEFAULT_PAGESIZE = 4096
DEFAULT_ITER = 64000

def execute_sql(connection, sql, params=None):
    """
    执行给定的SQL语句，返回结果。
    参数：
        - connection： SQLite连接
        - sql：要执行的SQL语句
        - params：SQL语句中的参数
    """
    try:
        # connection.text_factory = bytes
        cursor = connection.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall()
    except Exception as e:
        try:
            connection.text_factory = bytes
            cursor = connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rdata = cursor.fetchall()
            connection.text_factory = str
            return rdata
        except Exception as e:
            print(f"**********\nSQL: {sql}\nparams: {params}\n{e}\n**********")
            return None
        

def decrypt(key: str, db_path, out_path):
    """
    通过密钥解密数据库
    :param key: 密钥 64位16进制字符串
    :param db_path:  待解密的数据库路径(必须是文件)
    :param out_path:  解密后的数据库输出路径(必须是文件)
    :return:
    """
    if not os.path.exists(db_path) or not os.path.isfile(db_path):
        return False, f"[-] db_path:'{db_path}' File not found!"
    if not os.path.exists(os.path.dirname(out_path)):
        return False, f"[-] out_path:'{out_path}' File not found!"

    if len(key) != 64:
        return False, f"[-] key:'{key}' Len Error!"

    password = bytes.fromhex(key.strip())

    try:
        with open(db_path, "rb") as file:
            blist = file.read()
    except Exception as e:
        return False, f"[-] db_path:'{db_path}' {e}!"

    salt = blist[:16]
    byteKey = hashlib.pbkdf2_hmac("sha1", password, salt, DEFAULT_ITER, KEY_SIZE)
    first = blist[16:DEFAULT_PAGESIZE]
    if len(salt) != 16:
        return False, f"[-] db_path:'{db_path}' File Error!"

    mac_salt = bytes([(salt[i] ^ 58) for i in range(16)])
    mac_key = hashlib.pbkdf2_hmac("sha1", byteKey, mac_salt, 2, KEY_SIZE)
    hash_mac = hmac.new(mac_key, first[:-32], hashlib.sha1)
    hash_mac.update(b'\x01\x00\x00\x00')

    if hash_mac.digest() != first[-32:-12]:
        return False, f"[-] Key Error! (key:'{key}'; db_path:'{db_path}'; out_path:'{out_path}' )"

    newblist = [blist[i:i + DEFAULT_PAGESIZE] for i in range(DEFAULT_PAGESIZE, len(blist), DEFAULT_PAGESIZE)]

    with open(out_path, "wb") as deFile:
        deFile.write(SQLITE_FILE_HEADER.encode())
        t = AES.new(byteKey, AES.MODE_CBC, first[-48:-32])
        decrypted = t.decrypt(first[:-48])
        deFile.write(decrypted)
        deFile.write(first[-48:])

        for i in newblist:
            t = AES.new(byteKey, AES.MODE_CBC, i[-48:-32])
            decrypted = t.decrypt(i[:-48])
            deFile.write(decrypted)
            deFile.write(i[-48:])
    return True, [db_path, out_path, key]


# 迁移数据库
def move_db(wx_info):
    multi_path = os.path.join(wx_info['filePath'], 'Msg', 'Multi')
    msg_path = os.path.join(wx_info['filePath'], 'Msg')
    destination_path = os.path.join(os.getcwd(), 'Origin_db')

    # 确保目标目录存在
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    # 复制以MSG开头且以.db结尾的文件
    for item in os.listdir(multi_path):
        if item.startswith('MSG') and item.endswith('.db'):
            shutil.copy(os.path.join(multi_path, item), destination_path)

    # 复制MicroMsg.db文件
    de_micro_msg_db_path = os.path.join(msg_path, 'MicroMsg.db')
    if os.path.exists(de_micro_msg_db_path):
        shutil.copy(de_micro_msg_db_path, destination_path)

# 数据库解密
def decrypt_db(wx_info):
    #先移动
    move_db(wx_info)

    destination_path = os.path.join(os.getcwd(), 'Decrypted_db')
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    origin_path = os.path.join(os.getcwd(), 'Origin_db')

    for item in os.listdir(origin_path):
        decrypt(wx_info["key"], os.path.join(origin_path, item), os.path.join(destination_path, item))

def merge_db(db_paths, save_path="merge.db", CreateTime: int = 0, endCreateTime: int = 0):
    """
    合并数据库 会忽略主键以及重复的行。
    :param db_paths:
    :param save_path:
    :param CreateTime:
    :return:
    """
    if os.path.isdir(save_path):
        save_path = os.path.join(save_path, f"merge_{int(time.time())}.db")

    if isinstance(db_paths, list):
        # alias, file_path
        databases = {f"MSG{i}": db_path for i, db_path in enumerate(db_paths)}
    elif isinstance(db_paths, str):
        databases = {"MSG": db_paths}
    else:
        raise TypeError("db_paths 类型错误")

    outdb = sqlite3.connect(save_path)
    out_cursor = outdb.cursor()
    # 将MSG_db_paths中的数据合并到out_db_path中
    for alias in databases:
        db = sqlite3.connect(databases[alias])
        # 获取表名
        sql = f"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        tables = execute_sql(db, sql)
        for table in tables:
            table = table[0]
            if table == "sqlite_sequence":
                continue
            # 获取表中的字段名
            sql = f"PRAGMA table_info({table})"
            columns = execute_sql(db, sql)
            col_type = {
                (i[1] if isinstance(i[1], str) else i[1].decode(), i[2] if isinstance(i[2], str) else i[2].decode()) for
                i in columns}
            columns = [i[1] if isinstance(i[1], str) else i[1].decode() for i in columns]
            if not columns or len(columns) < 1:
                continue

            # 检测表是否存在
            sql = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
            out_cursor.execute(sql)
            if len(out_cursor.fetchall()) < 1:
                # 创建表
                # 拼接创建表的SQL语句
                column_definitions = []
                for column in col_type:
                    column_name = column[0] if isinstance(column[0], str) else column[0].decode()
                    column_type = column[1] if isinstance(column[1], str) else column[1].decode()
                    column_definition = f"{column_name} {column_type}"
                    column_definitions.append(column_definition)
                sql = f"CREATE TABLE IF NOT EXISTS {table} ({','.join(column_definitions)})"
                # sql = f"CREATE TABLE IF NOT EXISTS {table} ({','.join(columns)})"
                out_cursor.execute(sql)

                # 创建包含 NULL 值比较的 UNIQUE 索引
                index_name = f"{table}_unique_index"
                coalesce_columns = ','.join(f"COALESCE({column}, '')" for column in columns)  # 将 NULL 值转换为 ''
                sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON {table} ({coalesce_columns})"
                out_cursor.execute(sql)

            # 获取表中的数据
            if "CreateTime" in columns and CreateTime > 0:
                sql = f"SELECT {','.join([i[0] for i in col_type])} FROM {table} WHERE CreateTime>? ORDER BY CreateTime"
                src_data = execute_sql(db, sql, (CreateTime,))
            else:
                sql = f"SELECT {','.join([i[0] for i in col_type])} FROM {table}"
                src_data = execute_sql(db, sql)
            if not src_data or len(src_data) < 1:
                continue
            # 插入数据
            sql = f"INSERT OR IGNORE INTO {table} ({','.join([i[0] for i in col_type])}) VALUES ({','.join(['?'] * len(columns))})"
            out_cursor.executemany(sql, src_data)
            outdb.commit()
    outdb.close()
    return save_path

#操作数据库提取聊天记录部分
def query_contacts_and_messages(MicroMsg_path, Merged_Msg_path, msg_days, contact_days):
    # 连接到数据库
    conn_micro_msg = sqlite3.connect(MicroMsg_path)
    conn_merge_msg = sqlite3.connect(Merged_Msg_path)
    
    # 获取今天日期和14天前的日期
    current_datetime = datetime.datetime.now()
    last_datetime = current_datetime - datetime.timedelta(days=int(contact_days))
    last_datetime_timestamp = int(last_datetime.timestamp())
    msg_days_ago = current_datetime - datetime.timedelta(days=int(msg_days))
    
    # 查询24小时内联系过的人的用户名
    cursor_micro_msg = conn_micro_msg.cursor()
    cursor_micro_msg.execute("""
        SELECT Username 
        FROM ChatInfo 
        WHERE LastReadedCreateTime >= ? AND Username NOT LIKE '%@chatroom' AND Username Not Like '%@openim'
    """, (last_datetime_timestamp * 1000,))  # 时间戳是毫秒级的          #排除群聊和企业微信的聊天记录
    usernames = [row[0] for row in cursor_micro_msg.fetchall()]
    # 查询联系人的详细信息
    contacts_info = {}
    for username in usernames:
        cursor_micro_msg.execute("""
            SELECT Alias, Nickname, Remark 
            FROM Contact 
            WHERE Username = ?
        """, (username,))
        contacts_info[username] = cursor_micro_msg.fetchone()
        
    # 查询聊天记录
    messages = {}
    for username in usernames:
        # 获取TalkerID
        cursor_merge_msg = conn_merge_msg.cursor()
        #cursor_merge_msg.execute("SELECT ROWID FROM Name2ID WHERE Usrname = ?", (username,))
        #talker_id = cursor_merge_msg.fetchone()[0]

        # 获取对应聊天记录
        cursor_merge_msg.execute("""
            SELECT StrContent, IsSender, CreateTime 
            FROM MSG 
            WHERE StrTalker = ? AND Type = 1 AND CreateTime > ?
            ORDER BY CreateTime
        """, (username,msg_days_ago.timestamp()))
        messages[username] = cursor_merge_msg.fetchall()

    # 关闭数据库连接
    conn_micro_msg.close()
    conn_merge_msg.close()

    # 返回结果
    return contacts_info, messages

def extract_msg():
    #先将MSG 数据库合并
    msg_db_path = os.path.join(os.getcwd(), 'Decrypted_db')
    msg_db_list = os.listdir(msg_db_path)
    msg_db_files = [os.path.join(msg_db_path, file) for file in msg_db_list if file.startswith("MSG") and file.endswith(".db")]
    merge_db(msg_db_files, save_path='Decrypted_db/Merged_MSG.db')

    MicroMSG_path = os.path.join(os.getcwd(), 'Decrypted_db/MicroMsg.db')
    MergedMSG_path = os.path.join(os.getcwd(), 'Decrypted_db/Merged_MSG.db')
    contacts_info, messages = query_contacts_and_messages(MicroMSG_path, MergedMSG_path)

    return contacts_info, messages

if __name__ == '__main__':
    contacts_info, messages, initial_values = extract_msg()
    print(contacts_info)
    print(messages)