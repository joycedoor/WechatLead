from config_manager import config
from wechat_utils import *
from flask import Flask
from salesforce import *
from routes import *
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
import sys

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
    contacts_info, messages = query_contacts_and_messages(config.get("DB_PATH"), config.get("MSG_DAYS"), config.get("CONTACT_DAYS"))
    initial_values = sf.search_contact(contacts_info, sf_init['account_dict'])
    # TODO: 处理initial_values的函数，并且需要方便后续维护，添加诸如chatgpt之类的功能

    configure_routes(app, sf, initial_values, contacts_info, messages, sf_init, sf.refresh_token, wx_info)
    return app

if __name__ == '__main__':
    # 设置最大日志文件大小（例如10MB）和备份文件数量（例如5）
    max_log_size = 5 * 1024 * 1024  # 10 MB
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  

    handler = RotatingFileHandler('Loggings.txt', maxBytes=max_log_size)
    handler.setLevel(logging.INFO)  # 设置处理器的日志级别
    logger.addHandler(handler)
    sys.stderr = logging.StreamHandler(sys.stderr)

    app = create_app()
    threading.Thread(target=open_browser).start()
    app.run(debug=config.get("DEBUG"))