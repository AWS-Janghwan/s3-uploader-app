#!/bin/bash

echo "Stopping S3 Uploader application..."

# systemd 서비스 중지
if sudo systemctl is-active --quiet s3-uploader; then
    echo "Stopping s3-uploader service..."
    sudo systemctl stop s3-uploader
    echo "Service stopped."
else
    echo "Service is not running."
fi

# 프로세스가 완전히 종료될 때까지 대기
sleep 5

echo "Application stop completed."
