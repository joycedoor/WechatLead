import config

class ConfigManager:
    def __init__(self):
        self.config = {
            "CLIENT_ID": config.CLIENT_ID,
            "CLIENT_SECRET": config.CLIENT_SECRET,
            "DB_PATH": config.DB_PATH,
            "DEBUG": config.DEBUG,

            "MSG_DAYS": config.MSG_DAYS,
            "CONTACT_DAYS": config.CONTACT_DAYS
        }
    
    def get(self, key):
        return self.config.get(key)
    
    def set(self, key, value):
        self.config[key] = value

# 在模块级别创建配置管理器实例
config = ConfigManager()
