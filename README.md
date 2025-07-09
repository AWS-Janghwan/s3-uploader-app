# 🚀 S3 파일 업로더 - 보안 강화 버전

AWS S3를 활용한 안전한 파일 업로드 및 공유 시스템입니다. AWS 정보를 완전히 숨기고 프록시 다운로드를 통해 보안을 강화했습니다.

## ✨ 주요 기능

### 🔐 보안 강화
- **AWS 정보 완전 숨김**: presigned URL 대신 보안 키 기반 프록시 다운로드
- **IAM 역할 기반 인증**: Access Key 없이 안전한 S3 접근
- **만료 시간 설정**: 링크 유효 기간 제한 (기본 7일)

### 👥 사용자 구분 시스템
- **첫 접속 시 모달**: AWS 직원 / AWS 고객사 선택
- **로컬 저장**: 사용자 정보 브라우저에 안전 저장
- **향후 확장**: 로그인 시스템 기반 마련

### 📁 파일 업로드
- **다중 파일 지원**: 최대 10개 파일 동시 업로드
- **드래그 앤 드롭**: 직관적인 파일 선택
- **실시간 진행률**: 업로드 상태 표시
- **한글 파일명 지원**: UTF-8 인코딩으로 완벽 지원

### 🔗 링크 공유
- **복사 기능**: 텍스트/HTML 형태 선택 가능
- **HTTP 환경 지원**: 폴백 메커니즘으로 모든 브라우저 지원
- **보안 배지**: "완전 보안 링크 (보안 점검 완료)" 표시

### 🔄 사용자 편의
- **초기화 기능**: 헤더 클릭 또는 초기화 버튼
- **반응형 디자인**: 모바일/데스크톱 완벽 지원
- **직관적 UI**: Bootstrap 5 기반 세련된 인터페이스

## 🏗️ 아키텍처

```
인터넷 → Application Load Balancer → EC2 (Flask) → S3 버킷
                    ↓
              헬스체크 (/health)
```

### AWS 인프라
- **EC2**: t3.micro (Flask 애플리케이션 서버)
- **ALB**: Application Load Balancer (고가용성)
- **S3**: 파일 저장소
- **IAM**: 역할 기반 권한 관리
- **VPC**: 네트워크 보안

## 🌐 접속 URL

### 프로덕션 (권장)
```
http://s3-uploader-alb-1960127651.us-west-2.elb.amazonaws.com
```

### 개발/백업
```
http://54.244.128.44:8081
```

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/AWS-Janghwan/s3-uploader-app.git
cd s3-uploader-app
```

### 2. 의존성 설치
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. AWS 설정
```bash
# IAM 역할 설정 (EC2에서) 또는
aws configure  # 로컬 개발 시
```

### 4. 애플리케이션 실행
```bash
python app.py
```

## 📋 요구사항

### Python 패키지
- Flask 2.3.3
- boto3 1.28.62
- Werkzeug 2.3.7

### AWS 권한
- S3 전체 접근 권한 (`s3:*`)
- EC2 인스턴스 프로파일 (프로덕션)

## 🔧 설정

### 환경 변수 (선택적)
```bash
export BUCKET_NAME=your-s3-bucket-name
export AWS_REGION=us-west-2
export PORT=8081
```

### S3 버킷 설정
- 버킷명: `presigned-url-generator-janghwan`
- 리전: `us-west-2`
- 퍼블릭 액세스: 차단 (프록시 다운로드 사용)

## 📊 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 메인 페이지 |
| `/upload` | POST | 파일 업로드 |
| `/download/<key>` | GET | 보안 다운로드 |
| `/health` | GET | 헬스체크 |
| `/file-info/<key>` | GET | 파일 정보 조회 |

## 🔐 보안 고려사항

### 1. 네트워크 보안
- ELB 보안 그룹: HTTP(80), HTTPS(443)
- EC2 보안 그룹: ELB에서만 8081 포트 허용

### 2. 애플리케이션 보안
- 32자리 랜덤 보안 키 생성
- 파일 만료 시간 제한
- 다운로드 횟수 추적

### 3. AWS 보안
- IAM 역할 기반 인증
- S3 버킷 퍼블릭 액세스 차단
- VPC 내 프라이빗 통신

## 📈 모니터링

### 헬스체크
```bash
curl http://localhost:8081/health
```

### 로그 확인 (systemd)
```bash
sudo journalctl -u s3-uploader -f
```

### 타겟 그룹 상태
AWS 콘솔에서 ELB 타겟 그룹 헬스 상태 확인

## 🚀 배포

### systemd 서비스 (프로덕션)
```bash
sudo systemctl start s3-uploader
sudo systemctl enable s3-uploader
```

### Docker (선택적)
```bash
docker build -t s3-uploader .
docker run -p 8081:8081 s3-uploader
```

## 🔄 향후 계획

### 단기 (1-2주)
- [ ] HTTPS 설정 (SSL 인증서)
- [ ] 도메인 연결 (Route 53)
- [ ] 로그인 시스템 구현

### 중기 (1-2개월)
- [ ] 파일 관리 대시보드
- [ ] 사용 통계 및 분석
- [ ] Auto Scaling Group

### 장기 (3-6개월)
- [ ] RDS 데이터베이스 연동
- [ ] CloudWatch 모니터링
- [ ] WAF 보안 강화

## 🐛 문제 해결

### 서비스 시작 실패
```bash
sudo systemctl status s3-uploader
sudo journalctl -u s3-uploader -n 20
```

### 파일 업로드 실패
1. IAM 역할 권한 확인
2. S3 버킷 존재 확인
3. 네트워크 연결 확인

### ELB 헬스체크 실패
```bash
curl http://localhost:8081/health
sudo netstat -tlnp | grep 8081
```

## 📞 지원

### 문서
- [완전 히스토리](project_complete_history.md): 전체 설정 및 구성 정보
- [채팅 히스토리](chat_history.md): 개발 과정 기록

### 연락처
- **개발자**: AWS-Janghwan
- **GitHub**: https://github.com/AWS-Janghwan
- **이슈 리포트**: GitHub Issues 활용

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

## 🙏 감사의 말

이 프로젝트는 AWS의 다양한 서비스를 활용하여 실제 프로덕션 환경에서 사용 가능한 보안 강화 파일 업로드 시스템을 구현했습니다. 

**주요 성과:**
- ✅ 완전한 AWS 정보 숨김
- ✅ 프로덕션 레디 인프라
- ✅ 사용자 친화적 UI/UX
- ✅ 확장 가능한 아키텍처

---

**현재 상태**: 프로덕션 운영 중 🚀  
**마지막 업데이트**: 2025-07-09
