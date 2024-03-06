import os
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
from app import app
if __name__ == "__main__":
    app.run(debug=False)
