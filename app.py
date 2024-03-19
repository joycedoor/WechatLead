import config
from wechat_utils import *
from flask import Flask
from salesforce import *
from routes import *
import time
import threading

def open_browser():
    while True:
        try:
            # 尝试连接到 Flask 服务器
            response = requests.get('http://127.0.0.1:5000/')
            if response.status_code == 200:
                # 服务器已启动且可以接受请求，打开浏览器
                webbrowser.open_new('http://127.0.0.1:5000/')
                break
        except requests.exceptions.ConnectionError:
            # 服务器尚未启动，等待一段时间后重试
            time.sleep(1)

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    wx_info = initialize_wechat()
    decrypt_wechat_database(wx_info)

    sf = SalesforceManager()
    sf_init = sf.get_init()

    contacts_info, messages = query_contacts_and_messages(config.DB_PATH, config.MSG_DAYS, config.CONTACT_DAYS)

    initial_values = sf.search_contact(contacts_info, sf_init['account_dict'])

    # TODO: 将以下内容整合到一个处理initial_values的函数里，并且需要方便后续维护，添加诸如chatgpt之类的功能
    for k, v in initial_values.items():
        # LastName可以预先更新到initial_values里
        if 'LastName' not in initial_values[k]:
            initial_values[k]['LastName'] = contacts_info[k][0]

    configure_routes(app, sf, initial_values, contacts_info, messages, sf_init, sf.refresh_token, wx_info)

    return app

if __name__ == '__main__':
    app = create_app()
    threading.Thread(target=open_browser).start()
    app.run(debug=config.DEBUG)