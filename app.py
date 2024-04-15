from flask import Flask, g
from config_manager import config
from wechat_utils import *
from salesforce import SalesforceManager
import threading
import time
import webbrowser
import requests

def open_browser():
    while True:
        try:
            response = requests.get('http://127.0.0.1:5000/')
            if response.status_code == 200:
                webbrowser.open_new('http://127.0.0.1:5000/')
                break
        except requests.exceptions.ConnectionError:
            time.sleep(1)

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    from routes import configure_routes
    wx_info = initialize_wechat()
    decrypt_wechat_database(wx_info)

    sf = SalesforceManager()
    sf_init = sf.get_init()

    # 这里初始化 initial_values, contacts_info, messages
    contacts_info, messages = query_contacts_and_messages(config.get("DB_PATH"), config.get("MSG_DAYS"), config.get("CONTACT_DAYS"))
    initial_values = sf.search_contact(contacts_info, sf_init['account_dict'])

    # 将这些变量存储到 g 对象中
    @app.before_request
    def before_request():
        g.initial_values = initial_values
        g.contacts_info = contacts_info
        g.messages = messages

    configure_routes(app, sf, sf_init, wx_info)
    return app

if __name__ == '__main__':
    # 设置最大日志文件大小（例如10MB）和备份文件数量（例如5）
    '''
    max_log_size = 5 * 1024 * 1024  # 10 MB
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  

    handler = RotatingFileHandler('Loggings.txt', maxBytes=max_log_size)
    handler.setLevel(logging.INFO)  # 设置处理器的日志级别
    logger.addHandler(handler)
    sys.stderr = logging.StreamHandler(sys.stderr)
    '''
    app = create_app()
    threading.Thread(target=open_browser).start()
    app.run(debug=config.get("DEBUG"))