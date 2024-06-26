# 测试阶段从token获取，正式发布阶段通过浏览器获取session
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed, format_soql
from simple_salesforce.exceptions import SalesforceMalformedRequest, SalesforceExpiredSession
import socket
import requests
import urllib
from config_manager import config
import webbrowser

class SalesforceManager:
    def __init__(self):
        self.sf = None
        self.refresh_token = None
        self.initialize_salesforce(config.get("CLIENT_ID"))

    def initialize_salesforce(self, client_id):
        print("即将开始 Salesforce 登录，登录完成后请返回本窗口")
        webbrowser.open(
            f'https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http%3A%2F%2Flocalhost%3A5000&scope=refresh_token%20full'
        )
        auth_code = self.get_code()
        access_token, instance_url, self.refresh_token = self.get_access_token(auth_code)
        try:
            self.sf = Salesforce(instance_url=instance_url, session_id=access_token)
            print('Salesforce 登录成功，请等待数据处理...')
        except Exception as e:
            print(e)
            input('登录失败，请联系管理员')

    def get_code(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('localhost', 5000))
        serversocket.listen(5)
        serversocket.settimeout(120)  # 设置超时时间为120秒（2分钟）
        try:
            connection, address = serversocket.accept()
            buf = connection.recv(1024)
            if len(buf) > 0:
                raw = buf.decode().split(' ')[1]
                url = 'http://localhost' + raw
                url_components = urllib.parse.urlparse(url)
                authorization_code = urllib.parse.parse_qs(url_components.query)['code'][0]
                
                # 一个简单的登陆成功反馈页面
                response_text = '<html><body><h1>Login successful!</h1></body></html>'
                response_header = 'HTTP/1.1 200 OK\nContent-Type: text/html; charset=utf-8\nContent-Length: {}\n\n'.format(len(response_text))
                connection.sendall(response_header.encode())
                connection.sendall(response_text.encode())
                connection.close()
                
                return authorization_code
        except socket.timeout:
            serversocket.close()  # 当超时
            print("No connection was made within 2 minutes.")  # 引发超时错误

    def get_access_token(self, auth_code):
        url = "https://login.salesforce.com/services/oauth2/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": config.get("CLIENT_ID"),
            "client_secret": config.get("CLIENT_SECRET"),
            "redirect_uri": "http://localhost:5000",
            "code": auth_code,
        }

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            data = response.json()
            return data["access_token"], data["instance_url"], data["refresh_token"]
        else:
            print("Error:%s"% (response.content))

    def get_init(self):
        d = {}
        try:
            #result = self.sf.query_all(format_soql("SELECT Status FROM Lead where RecordTypeId='0123j000001QWVZAA4' GROUP BY Status"))
            #d['Lead_Status_dropdown'] = [record['Status'] for record in result['records'] if record['Status'] is not None and record['Status'][-2:] != '_c']
            d['Lead_Status_dropdown'] = ["New", "MKT Connecting", "CIS Connecting", "Group Connecting", "Waiting OE", "No Response", "Lost Comp" ,
                                         "Lost School", "Enrolled Not Verified", "Enrolled", "Canceled", "Expired", "Converted"]

            result = self.sf.query("SELECT WeChat_Agents_List__c FROM Lead where RecordTypeId='0123j000001QWVZAA4' GROUP BY WeChat_Agents_List__c")
            d['WeChat_Agents_dropdown'] = [record['WeChat_Agents_List__c'] for record in result['records'] if record['WeChat_Agents_List__c'] and record['WeChat_Agents_List__c'][-2:] != '_c']

            result = self.sf.query("SELECT WeCom_Agents_List__c FROM Lead where RecordTypeId='0123j000001QWVZAA4' GROUP BY WeCom_Agents_List__c")
            d['WeCom_Agents_dropdown'] = [record['WeCom_Agents_List__c'] for record in result['records'] if record['WeCom_Agents_List__c'] and record['WeCom_Agents_List__c'][-2:] != '_c']

            lead_description = self.sf.Lead.describe()
            d['Sales_WeChat_dropdown'] = []

            for field in lead_description['fields']:
                if field['name'] == 'Sales_WeChat_Account__c': 
                    picklist_values = field['picklistValues']
                    for picklist_value in picklist_values:
                        d['Sales_WeChat_dropdown'].append(picklist_value['label'])

            account = self.sf.query("SELECT Id, Name FROM Account Group by Id, Name")
            d['account_dict'] = {record['Id']: record['Name'] for record in account['records']}

            print("初始化数据加载完毕，即将查询Leads")
            return d
        except Exception as e:
            print(e)

    def search_contact(self, contacts_info, account_dict, app):
        initial_values = {key: {} for key in contacts_info.keys()}

        #通过wxid 查找
        for wxid, info in contacts_info.items():
            lastname = info['Alias']
            result = self.sf.query(f"SELECT Lead_ID__c, Status, Student_or_Parent__c, FirstName, LastName, Account__c, Social_Media_Platform__c, \
                                WeChat_Agents_List__c, WeCom_Agents_List__c, Sales_WeChat_Account__c, \
                                Group_Name__c, Member_First_Name__c, Member_Last_Name__c, Date_of_Birth__c, Email, Note_and_Description__c \
                                FROM Lead where RecordTypeId='0123j000001QWVZAA4' AND LastName = '{lastname}'")
            if result['records']:
                initial_values[wxid]["is_in_SF"] = 1
            
                # TODO：这里先假设默认使用第一条记录，后续需要额外处理
                record = result['records'][0]
                leadid = result['records'][0]['Lead_ID__c']
                initial_values[wxid]["link"] =  "https://smcovered.lightning.force.com/lightning/r/Lead/%s/view"%(leadid)
                # 遍历记录中的每个字段
                for field in record:
                    # 跳过attributes字段，它通常包含元数据而非实际数据
                    if field != 'attributes':
                        # 将字段名作为键，字段值作为值，添加到initial_values[wxid]的字典中
                        initial_values[wxid][field] = record[field]
                    if field == 'Account__c' and record[field] is not None:
                        initial_values[wxid]['Account__c'] = account_dict[record[field]]
            else:
                initial_values[wxid]["is_in_SF"] = 0

            # 对initial values的额外处理
            if initial_values[wxid]['is_in_SF'] == 0:
                # 默认识别LastName
                initial_values[wxid]['LastName'] = contacts_info[wxid]['Alias']

                # 识别家长
                initial_values[wxid]['Student_or_Parent__c'] = 'Parent' if '家长' in info['Remark'] else 'Student'

                # 识别默认Social Media Platform
                initial_values[wxid]['Social_Media_Platform__c'] = app.config['global_data']['DefaultPlatform']
                initial_values[wxid]['WeChat_Agents_List__c'] = app.config['global_data']['DefaultWechatAgent']
                initial_values[wxid]['WeCom_Agents_List__c'] = app.config['global_data']['DefaultWecomAgent']
                initial_values[wxid]['Sales_WeChat_Account__c'] = app.config['global_data']['DefaultSalesWechatAgent']
            
        return initial_values

    def refresh_access_token(self):
        url = "https://login.salesforce.com/services/oauth2/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": config.get("CLIENT_ID"),
            "client_secret": config.get("CLIENT_SECRET"),
            "refresh_token": self.refresh_token,
        }

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            data = response.json()
            self.sf = Salesforce(instance_url=data["instance_url"], session_id=data["access_token"])

        else:
            print("Refresh Token Error:%s"% response.content)