@echo off
CALL conda.bat activate pywx
git pull
REM CALL conda.bat install --file requirements.txt
REM 或者使用以下命令如果使用 pip
CALL python -m pip install -r requirements.txt
python app.py
pause
