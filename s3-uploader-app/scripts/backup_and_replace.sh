#!/bin/bash

echo "🔄 백업 및 애플리케이션 교체 중..."

cd /home/ubuntu

# 기존 애플리케이션 백업
if [ -d "s3-uploader-app" ]; then
    echo "📦 기존 애플리케이션 백업 중..."
    BACKUP_DIR="s3-uploader-app-backup-$(date +%Y%m%d-%H%M%S)"
    mv s3-uploader-app $BACKUP_DIR
    echo "백업 완료: $BACKUP_DIR"
fi

# 새 애플리케이션을 원래 위치로 이동
if [ -d "s3-uploader-app-new" ]; then
    echo "🔄 새 애플리케이션 배치 중..."
    mv s3-uploader-app-new s3-uploader-app
    echo "애플리케이션 교체 완료"
else
    echo "❌ 새 애플리케이션 디렉토리를 찾을 수 없습니다."
    exit 1
fi

# 기존 데이터베이스 파일 복원 (있는 경우)
if ls s3-uploader-app-backup-*/file_links.db 1> /dev/null 2>&1; then
    echo "📊 기존 데이터베이스 복원 중..."
    cp s3-uploader-app-backup-*/file_links.db s3-uploader-app/ 2>/dev/null || true
    echo "데이터베이스 복원 완료"
fi

# 파일 소유권 설정
echo "🔐 파일 소유권 설정 중..."
chown -R ubuntu:ubuntu s3-uploader-app

echo "✅ 백업 및 교체 완료"
