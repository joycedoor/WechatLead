from pywxdump import VERSION_LIST, read_info, merge_real_time_db, get_core_db, decrypt
from db_process import query_contacts_and_messages
import sys
from flask import Flask, render_template, request, jsonify
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed, format_soql
from simple_salesforce.exceptions import SalesforceMalformedRequest, SalesforceExpiredSession
import webbrowser
from salesforce import *


wx_info = read_info(VERSION_LIST, True)[0]

#检查Key的获取是否成功
try:
    if not wx_info['key']:
        _ = input("信息获取失败，请关闭程序后重试，若错误持续出现，请联系管理员")
except:
    print("信息获取失败，请关闭程序后重试，若错误持续出现，请联系管理员")
    input()
    sys.exit()

#根据key解密数据库
db_type = ["MSG", "MicroMsg"]
code,dbs = get_core_db(wx_path = wx_info['filePath'], db_type=db_type)
if not code:
    _ = input("数据库路径信息获取失败，请联系管理员")
try:
    for d in dbs:
        merge_real_time_db(wx_info["key"], d, "./temp_db/MSG.db", 0, 999999999999)
    print("数据库消息信息解密成功")
except Exception as e:
    print(e)
    _ = input("数据库MSG信息解密失败，请联系管理员")

msg_days = input("即将提取聊天记录，请选择需要显示多少天前的聊天记录（请输入整数）：")
contact_days = input("请选择需要显示多少天内的聊天对象（请输入整数）：")
contacts_info, messages = query_contacts_and_messages("./temp_db/MSG.db", msg_days, contact_days)

_ = input("即将开始salesforce登录，请回车确认，登录完成后请返回本窗口")

webbrowser.open(
    'https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id={}&redirect_uri=http%3A%2F%2Flocalhost%3A5000&scope=refresh_token%20full'.format(CLIENT_ID)
)

auth_code = get_code()
access_token, instance_url, refresh_token = get_access_token(auth_code)

try:
    sf = Salesforce(instance_url=instance_url, session_id=access_token)
except SalesforceAuthenticationFailed as e:
    print(e)
    _ = input('登录失败，请联系管理员')

Lead_Status_dropdown, WeChat_Agents_dropdown, WeCom_Agents_dropdown, Sales_WeChat_dropdown = get_init(sf)
account = sf.query("SELECT Id, Name FROM Account Group by Id, Name")
account_dict = {record['Id']: record['Name'] for record in account['records']}

school_names = list(account_dict.values())

initial_values = search_contact(contacts_info, sf)

# TODO: 将以下内容整合到一个处理initial_values的函数里，并且需要方便后续维护，添加诸如chatgpt之类的功能
for k, v in initial_values.items():
    # 将initial_values里的Account__c的Id换成Name
    if 'Account__c' in initial_values[k]:
        initial_values[k]['Account__c'] = account_dict[initial_values[k]['Account__c']]
    # LastName可以预先更新到initial_values里
    if 'LastName' not in initial_values[k]:
        initial_values[k]['LastName'] = contacts_info[k][0]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', contacts_info=contacts_info, initial_values = initial_values, 
                           messages=messages, Lead_Status_dropdown=Lead_Status_dropdown, WeChat_Agents_dropdown=WeChat_Agents_dropdown,
                           WeCom_Agents_dropdown=WeCom_Agents_dropdown, Sales_WeChat_dropdown=Sales_WeChat_dropdown)

@app.route('/get_messages/<user_id>')
def get_messages(user_id):
    user_messages = messages.get(user_id, [])
    return jsonify(user_messages)

@app.route('/get_school_names')
def get_school_names():
    # school_names是包含所有account学校名字的list
    return jsonify(school_names)

@app.route('/get_initial_values')
def get_initial_values():
    return jsonify(initial_values)

@app.route('/submit_action', methods=['POST'])
def submit_action():
    global sf
    global initial_values

    data = request.get_json()  # 获取 JSON 数据
    user_id = data['user_id']
    action_data = data['action_data']
    # 这里处理提交的数据
    action_data = {k: v for k, v in action_data.items() if v != ''}
    action_data['Company'] = "SM"

    school_text = action_data.get('Account__c', False)
    if school_text:
        query = f"SELECT Id FROM Account WHERE Name = '{school_text}'"
        try:
            account = sf.query(query)
        except SalesforceExpiredSession:
            access_token, instance_url = refresh_access_token(refresh_token)
            sf = Salesforce(instance_url=instance_url, session_id=access_token)
            account = sf.query(query)
        account_id = account['records'][0]['Id'] if account['totalSize'] > 0 else None
        if account_id is not None:
            action_data['Account__c'] = account_id
        else:
            print("没有检索到学校，请检查学校是否填写正确")
            return jsonify({'status': 'Failed'})

    LastName = action_data.get('LastName', False)
    if not LastName:
        #如果前端没输入last name（which is wrong），那就用contacts_info去找，总归是能找到的
        action_data['LastName'] = contacts_info[user_id][0]

    try:
        sf.Lead.create(action_data)
        initial_values[user_id] = action_data
        initial_values[user_id]['is_in_SF'] = 1
        initial_values[user_id]['Account__c'] = school_text

        return jsonify({'status': 'success'})
    except SalesforceExpiredSession:
        try:
            access_token, instance_url = refresh_access_token(refresh_token)
            sf = Salesforce(instance_url=instance_url, session_id=access_token)
            sf.Lead.create(action_data)
        except Exception as e:
            print(e)
            return jsonify({'status': 'Failed'})
    except Exception as e:
        print(e)
        return jsonify({'status': 'Failed'})
    

@app.route('/refresh_data')
def refresh_data():
    global messages
    global initial_values
    global contacts_info
    try:
        for d in dbs:
            merge_real_time_db(wx_info["key"], d, "./temp_db/MSG.db", 0, 999999999999)
        print("数据库消息信息解密成功")
    except Exception as e:
        print(e)
        _ = input("数据库MSG信息解密失败，请联系管理员")

    contacts_info, messages = query_contacts_and_messages("./temp_db/MSG.db", msg_days, contact_days)
    initial_values = search_contact(contacts_info, sf)
    return jsonify({
            'contacts_info': contacts_info,
            'messages': messages,
            'initial_values': initial_values
        })

app.run(debug=False)