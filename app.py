import config
from wechat_utils import *
from flask import Flask
from salesforce import *
from routes import *

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    wx_info = initialize_wechat()
    decrypt_wechat_database(wx_info)

    sf, refresh_token = initialize_salesforce(config.CLIENT_ID)
    sf_init = get_init(sf)

    contacts_info, messages = query_contacts_and_messages(config.DB_PATH, config.MSG_DAYS, config.CONTACT_DAYS)

    initial_values = search_contact(contacts_info, sf, sf_init['account_dict'])

    # TODO: 将以下内容整合到一个处理initial_values的函数里，并且需要方便后续维护，添加诸如chatgpt之类的功能
    for k, v in initial_values.items():
        # LastName可以预先更新到initial_values里
        if 'LastName' not in initial_values[k]:
            initial_values[k]['LastName'] = contacts_info[k][0]

    configure_routes(app, sf, initial_values, contacts_info, messages, sf_init, refresh_token, wx_info)

    return app

if __name__ == '__main__':
    import subprocess
    import sys

    # 检查并更新Python包依赖
    def check_and_update_dependencies():
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

    # 检查并拉取最新的GitHub更改
    def check_and_pull_latest():
        subprocess.check_call(['git', 'pull'])

    try:
        # 检查依赖并更新
        check_and_update_dependencies()
        # 拉取最新代码
        check_and_pull_latest()
    except subprocess.CalledProcessError as e:
        print("更新失败:", e)
        sys.exit(1)

    # 运行Flask应用
    app = create_app()
    app.run(debug=config.DEBUG)