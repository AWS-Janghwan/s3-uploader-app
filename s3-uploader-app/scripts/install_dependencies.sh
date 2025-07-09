#!/bin/bash

echo "Installing dependencies for S3 Uploader application..."

cd /home/ubuntu/s3-uploader-app

# Python 가상환경 생성 (없는 경우에만)
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# 가상환경 활성화 및 의존성 설치
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 파일 권한 설정
echo "Setting file permissions..."
chmod +x app.py
chmod -R 755 templates/
chmod +x scripts/*.sh

# SQLite 데이터베이스 파일 권한 설정 (있는 경우)
if [ -f "file_links.db" ]; then
    chmod 664 file_links.db
fi

echo "Dependencies installation completed."
