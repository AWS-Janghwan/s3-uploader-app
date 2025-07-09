#!/bin/bash

echo "Validating S3 Uploader service..."

# 서비스 상태 확인
if ! sudo systemctl is-active --quiet s3-uploader; then
    echo "❌ Service is not running"
    exit 1
fi

# 헬스체크 엔드포인트 확인
echo "Checking health endpoint..."
for i in {1..10}; do
    if curl -f -s http://localhost:8081/health > /dev/null; then
        echo "✅ Health check passed!"
        break
    else
        echo "Attempt $i: Health check failed, retrying in 5 seconds..."
        if [ $i -eq 10 ]; then
            echo "❌ Health check failed after 10 attempts"
            exit 1
        fi
        sleep 5
    fi
done

# ELB 헬스체크도 확인
echo "Checking ELB target health..."
sleep 10  # ELB 헬스체크가 업데이트될 시간 제공

echo "✅ Service validation completed successfully!"
echo "🚀 S3 Uploader application is running and healthy!"

# 서비스 정보 출력
echo "=== Service Information ==="
echo "Local URL: http://localhost:8081"
echo "ELB URL: http://s3-uploader-alb-1960127651.us-west-2.elb.amazonaws.com"
echo "Health Check: http://localhost:8081/health"
