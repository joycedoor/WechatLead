from pywxdump import VERSION_LIST, read_info, merge_real_time_db, get_core_db
import sys
import config
from salesforce import *
import sqlite3
import datetime

def initialize_wechat():
    wx_info = read_info(VERSION_LIST, True)[0]
    try:
        if not wx_info['key']:
            _ = input("信息获取失败，请关闭程序后重试，若错误持续出现，请联系管理员")
            
    except:
        print("信息获取失败，请关闭程序后重试，若错误持续出现，请联系管理员")
        input()
        sys.exit()

    return wx_info  # 返回微信初始化信息

def decrypt_wechat_database(wx_info):
    #根据key解密数据库
    current_datetime = datetime.datetime.now()
    last_datetime = current_datetime - datetime.timedelta(days=int(config.CONTACT_DAYS))
    last_datetime_timestamp = int(last_datetime.timestamp())

    db_type = ["MSG", "MicroMsg"]
    code,dbs = get_core_db(wx_path = wx_info['filePath'], db_type=db_type)
    if not code:
        _ = input("数据库路径信息获取失败，请联系管理员")
    try:
        for d in dbs:
            merge_real_time_db(wx_info["key"], d, config.DB_PATH, last_datetime_timestamp, 999999999999)
        print("数据库消息信息解密成功")
    except Exception as e:
        print(e)
        _ = input("数据库MSG信息解密失败，请联系管理员")

def query_contacts_and_messages(Merged_Msg_path, msg_days, contact_days):
    # 连接到数据库
    conn_merge_msg = sqlite3.connect(Merged_Msg_path)
    
    # 获取今天日期和14天前的日期
    current_datetime = datetime.datetime.now()
    last_datetime = current_datetime - datetime.timedelta(days=int(contact_days))
    last_datetime_timestamp = int(last_datetime.timestamp())
    msg_days_ago = current_datetime - datetime.timedelta(days=int(msg_days))
    
    # 查询 Contact_days 内联系过的人的用户名
    cursor_micro_msg = conn_merge_msg.cursor()
    cursor_micro_msg.execute("""
        SELECT StrTalker, Alias, Nickname, Remark
        FROM MSG join Contact on MSG.StrTalker = Contact.UserName
        WHERE CreateTime >= ? AND Username NOT LIKE '%@chatroom' AND Username Not Like '%@openim'
        Group by StrTalker
    """, (last_datetime_timestamp,))       #排除群聊和企业微信的聊天记录

    # 查询联系人的详细信息
    contacts_info = {}
    for row in cursor_micro_msg.fetchall():
        contacts_info[row[0]] = [row[1], row[2], row[3]]
        if row[1] == '':  #当没有alia时，也就是用户从没有改过WXID
            contacts_info[row[0]][0] = row[0]   #用原始WXID填充Alias

    # 查询聊天记录
    messages = {}
    for username in contacts_info.keys():
        # 获取TalkerID
        cursor_merge_msg = conn_merge_msg.cursor()
        
        # 获取对应聊天记录
        cursor_merge_msg.execute("""
            SELECT StrContent, IsSender, CreateTime 
            FROM MSG 
            WHERE StrTalker = ? AND Type = 1 AND CreateTime > ?
            ORDER BY CreateTime
        """, (username,msg_days_ago.timestamp()))
        messages[username] = cursor_merge_msg.fetchall()

    # 关闭数据库连接
    conn_merge_msg.close()

    # 返回结果
    return contacts_info, messages