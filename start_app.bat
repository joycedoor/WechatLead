@echo off
CALL conda.bat activate pywx
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

REM 将输出和错误重定向到同一文件
python app.py >> Loggings.txt 2>&1
pause
