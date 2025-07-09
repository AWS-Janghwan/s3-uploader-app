#!/bin/bash

echo "Starting S3 Uploader application..."

cd /home/ubuntu/s3-uploader-app

# systemd 서비스 시작
echo "Starting s3-uploader service..."
sudo systemctl start s3-uploader

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable s3-uploader

# 서비스 상태 확인
sleep 3
if sudo systemctl is-active --quiet s3-uploader; then
    echo "✅ S3 Uploader service started successfully!"
    sudo systemctl status s3-uploader --no-pager -l
else
    echo "❌ Failed to start S3 Uploader service"
    sudo systemctl status s3-uploader --no-pager -l
    exit 1
fi

echo "Application start completed."
