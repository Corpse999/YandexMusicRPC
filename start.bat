@echo off
chcp 65001
cls

call pip install -r requirements.txt
call npm install ws

call python start.py

pause