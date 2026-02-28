@echo off
echo Starting YOLOv8 Platform...

cd backend
echo Installing Backend Dependencies...
call D:\ProgramData\miniconda3\Scripts\activate.bat yolov8
pip install -r requirements.txt

echo Starting Backend Server...
start "YOLOv8 Backend" cmd /k "call D:\ProgramData\miniconda3\Scripts\activate.bat yolov8 && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

cd ..\frontend
echo Installing Frontend Dependencies...
call npm install

echo Starting Frontend Dev Server...
npm run dev