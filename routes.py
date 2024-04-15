from flask import request, jsonify, render_template, g
from salesforce import SalesforceManager
from wechat_utils import *
from config_manager import config

def configure_routes(app, sf, sf_init, wx_info):
    
    @app.route('/')
    def index():
        return render_template('index.html', contacts_info=g.contacts_info, initial_values = g.initial_values, 
                            messages=g.messages, Lead_Status_dropdown=sf_init['Lead_Status_dropdown'], WeChat_Agents_dropdown=sf_init['WeChat_Agents_dropdown'],
                            WeCom_Agents_dropdown=sf_init['WeCom_Agents_dropdown'], Sales_WeChat_dropdown=sf_init['Sales_WeChat_dropdown'])

    @app.route('/get_messages/<user_id>')
    def get_messages(user_id):
        user_messages = g.messages.get(user_id, [])
        return jsonify(user_messages)

    @app.route('/get_school_names')
    def get_school_names():
        # school_names是包含所有account学校名字的list
        return jsonify(list(sf_init['account_dict'].values()))
    
    @app.route('/get_config_values')
    def get_config_values():
        c = {}
        c['MSG_DAYS'] = config.get('MSG_DAYS')
        c['CONTACT_DAYS'] = config.get('CONTACT_DAYS')   
        return jsonify(c)
    
    @app.route('/set_config_values', methods=['POST'])
    def set_config_values():
        try:
            MSG_DAYS = request.json.get('MSG_DAYS')
            CONTACT_DAYS = request.json.get('CONTACT_DAYS')

            config.set('MSG_DAYS', MSG_DAYS)
            config.set('CONTACT_DAYS', CONTACT_DAYS)

            return jsonify({'status': 'Success'})
        except Exception as e:
            print(e) 
            return jsonify({'status': 'Failed'})

    @app.route('/get_initial_values/<user_id>')
    def get_initial_values(user_id):
        return jsonify(g.initial_values[user_id])

    @app.route('/submit_action', methods=['POST'])
    def submit_action():
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
                account = sf.sf.query(query)
            except SalesforceExpiredSession:
                sf.refresh_access_token()
                account = sf.sf.query(query)
            account_id = account['records'][0]['Id'] if account['totalSize'] > 0 else None
            if account_id is not None:
                action_data['Account__c'] = account_id
            else:
                print("没有检索到学校，请检查学校是否填写正确")
                print(action_data)
                return jsonify({'status': 'Failed'})

        LastName = action_data.get('LastName', False)
        if not LastName:
            #如果前端没输入last name（which is wrong），那就用contacts_info去找，总归是能找到的
            action_data['LastName'] = g.contacts_info[user_id][0]
            
        action_data['Original_WXID__c'] = user_id #添加原始wxid

        try:
            res = sf.sf.Lead.create(action_data)
            g.initial_values[user_id] = action_data
            g.initial_values[user_id]['is_in_SF'] = 1
            g.initial_values[user_id]['Account__c'] = school_text
            g.initial_values[user_id]['link'] = "https://smcovered.lightning.force.com/lightning/r/Lead/%s/view"%(res.get('id'))

            return jsonify({'status': 'success'})
        except SalesforceExpiredSession:
            try:
                sf.refresh_access_token()
                sf.sf.Lead.create(action_data)
            except Exception as e:
                print(e)
                return jsonify({'status': 'Failed'})
        except Exception as e:
            print(e)
            return jsonify({'status': 'Failed'})
        

    @app.route('/refresh_data')
    def refresh_data():
        decrypt_wechat_database(wx_info)

        contacts_info, messages = query_contacts_and_messages(config.get("DB_PATH"), config.get("MSG_DAYS"), config.get("CONTACT_DAYS"))
        sf.refresh_access_token()
        initial_values = sf.search_contact(contacts_info, sf_init['account_dict'])

        # 更新 g 对象的全局变量
        g.contacts_info = contacts_info
        g.messages = messages
        g.initial_values = initial_values

        return jsonify({
            'contacts_info': contacts_info,
            'messages': messages,
            'initial_values': initial_values
        })
