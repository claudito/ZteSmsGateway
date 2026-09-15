@echo off
cd /d D:\Proyectos\Python\ZteSmsGateway
python -m uvicorn api:app --host 0.0.0.0 --port 8888 >> log.txt 2>&1
