@echo off
CALL conda.bat activate pywx
set PYTHONIOENCODING=utf-8
git pull
REM CALL conda.bat install --file requirements.txt
REM 或者使用以下命令如果使用 pip
CALL python -m pip install -r requirements.txt

REM 检查Loggings.txt的大小，如果大于5MB，则删除并创建新的日志文件
if exist Loggings.txt (
    FOR %%A IN (Loggings.txt) DO (
        set size=%%~zA
        if %%~zA GTR 5120000 (
            del Loggings.txt
        )
    )
)

python app.py