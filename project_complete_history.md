# S3 파일 업로더 프로젝트 완전 히스토리

## 📋 프로젝트 개요
- **프로젝트명**: S3 파일 업로더 - 보안 강화 버전
- **목적**: AWS S3를 활용한 안전한 파일 업로드 및 공유 시스템
- **특징**: AWS 정보 완전 숨김, 프록시 다운로드, 사용자 구분 시스템

## 🏗️ AWS 인프라 구성

### EC2 인스턴스
- **인스턴스 ID**: `i-07c121de197e1eb85`
- **인스턴스 타입**: t3.micro
- **퍼블릭 IP**: 54.244.128.44
- **프라이빗 IP**: 172.31.32.90
- **키 페어**: s3-uploader-key.pem
- **VPC**: vpc-0f761b4ae7b3c4394
- **서브넷**: subnet-0b01fa9931a30e6cf (us-west-2a)
- **보안 그룹**: sg-04515c5c61bf47a24 (s3-uploader-sg)

### IAM 역할 및 정책
- **역할명**: S3UploaderRole
- **인스턴스 프로파일**: S3UploaderInstanceProfile
- **정책**: S3 전체 접근 권한 (s3:*)
- **목적**: Access Key 없이 안전한 S3 접근

### S3 버킷
- **버킷명**: presigned-url-generator-janghwan
- **리전**: us-west-2
- **용도**: 업로드된 파일 저장

### Application Load Balancer
- **이름**: s3-uploader-alb
- **DNS**: s3-uploader-alb-1960127651.us-west-2.elb.amazonaws.com
- **타입**: Application Load Balancer
- **스킴**: internet-facing
- **VPC**: vpc-0f761b4ae7b3c4394
- **서브넷**: subnet-0b01fa9931a30e6cf, subnet-0e86c3425eb9edd30
- **보안 그룹**: sg-0b7da421fc63d2356 (s3-uploader-elb-sg)

### 타겟 그룹
- **이름**: s3-uploader-targets
- **프로토콜**: HTTP
- **포트**: 8081
- **헬스체크 경로**: /health
- **타겟**: i-07c121de197e1eb85:8081
- **상태**: Healthy

### 보안 그룹 규칙
**ELB 보안 그룹 (sg-0b7da421fc63d2356)**:
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0

**EC2 보안 그룹 (sg-04515c5c61bf47a24)**:
- SSH (22): 0.0.0.0/0
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- Custom (8081): sg-0b7da421fc63d2356 (ELB에서만)

## 💻 애플리케이션 구성

### 서버 사이드 (Flask)
- **파일**: app.py
- **포트**: 8081
- **데이터베이스**: SQLite (file_links.db)
- **서비스**: systemd (s3-uploader.service)
- **자동 시작**: 부팅 시 자동 실행

### 주요 엔드포인트
- `/`: 메인 페이지
- `/upload`: 파일 업로드 (POST)
- `/download/<secure_key>`: 보안 다운로드
- `/health`: 헬스체크
- `/file-info/<secure_key>`: 파일 정보 조회

### 클라이언트 사이드 (HTML/JavaScript)
- **파일**: templates/index.html
- **프레임워크**: Bootstrap 5.3.0
- **아이콘**: Font Awesome 6.0.0
- **기능**: 드래그 앤 드롭, 다중 파일 업로드, 복사 기능

## 🔧 주요 기능

### 1. 사용자 구분 시스템
- **첫 접속 시 모달**: AWS 직원 / AWS 고객사 선택
- **저장 방식**: localStorage
- **저장 정보**: 
  ```json
  {
    "type": "aws-staff" | "aws-customer",
    "timestamp": "2025-07-09T05:26:21.000Z",
    "sessionId": "sess_1720507581000_abc123def"
  }
  ```

### 2. 파일 업로드
- **다중 파일 지원**: 최대 10개
- **드래그 앤 드롭**: 지원
- **파일 크기 표시**: 자동 계산
- **진행률 표시**: 업로드 중 표시

### 3. 보안 링크 생성
- **보안 키**: 32자리 랜덤 문자열
- **만료 시간**: 기본 7일 (설정 가능)
- **다운로드 추적**: 횟수 기록
- **프록시 다운로드**: AWS 정보 완전 숨김

### 4. 복사 기능
- **텍스트 형태**: 파일명: URL
- **HTML 형태**: `<a href="URL">파일명</a>`
- **HTTP 지원**: navigator.clipboard 실패 시 폴백
- **한글 파일명**: UTF-8 인코딩 지원

### 5. 초기화 기능
- **초기화 버튼**: 헤더 우측
- **제목 클릭**: S3 파일 업로더 클릭으로 초기화
- **확인 대화상자**: 실수 방지

## 🌐 접속 URL

### 프로덕션 (ELB)
```
http://s3-uploader-alb-1960127651.us-west-2.elb.amazonaws.com
```

### 개발/백업 (직접 EC2)
```
http://54.244.128.44:8081
```

## 🔍 해결된 주요 문제들

### 1. 복사 기능 실패
- **문제**: HTTP 환경에서 navigator.clipboard API 제한
- **해결**: document.execCommand 폴백 + 수동 복사 모달

### 2. 한글 파일명 다운로드 오류
- **문제**: UnicodeEncodeError (latin-1 인코딩 제한)
- **해결**: RFC 5987 표준 `filename*=UTF-8''` 형식 사용

### 3. 파일 선택 UI 문제
- **문제**: 파일 선택 후에도 계속 파일 선택 팝업
- **해결**: 조건부 클릭 이벤트 + UI 상태 관리

### 4. 여러 파일 업로드 실패
- **문제**: 서버-클라이언트 파일 키 이름 불일치
- **해결**: 'file' → 'files'로 통일

### 5. ELB 엔드포인트 접근 불가
- **문제**: 기존 ELB가 다른 VPC에 위치
- **해결**: 새로운 ALB + 타겟 그룹 + 리스너 생성

## 📁 파일 구조

```
/home/ubuntu/s3-uploader-app/
├── app.py                 # Flask 애플리케이션
├── requirements.txt       # Python 의존성
├── venv/                 # 가상 환경
├── templates/
│   └── index.html        # 메인 템플릿
├── file_links.db         # SQLite 데이터베이스
└── logs/                 # 로그 파일 (선택적)
```

## 🔄 시스템 서비스

### systemd 서비스 파일
```ini
[Unit]
Description=S3 File Uploader Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/s3-uploader-app
Environment=PATH=/home/ubuntu/s3-uploader-app/venv/bin
ExecStart=/home/ubuntu/s3-uploader-app/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 서비스 관리 명령어
```bash
sudo systemctl start s3-uploader
sudo systemctl stop s3-uploader
sudo systemctl restart s3-uploader
sudo systemctl status s3-uploader
sudo systemctl enable s3-uploader  # 부팅 시 자동 시작
```

## 🔐 보안 고려사항

### 1. AWS 자격 증명
- IAM 역할 사용 (Access Key 불필요)
- EC2 인스턴스 프로파일 연결
- S3 전체 접근 권한 (필요시 제한 가능)

### 2. 네트워크 보안
- 보안 그룹으로 트래픽 제어
- ELB를 통한 트래픽 분산
- 프라이빗 서브넷 배치 가능

### 3. 애플리케이션 보안
- 보안 키 기반 다운로드
- 파일 만료 시간 설정
- 다운로드 횟수 추적

## 📊 모니터링 및 로깅

### 애플리케이션 로그
```bash
sudo journalctl -u s3-uploader -f  # 실시간 로그
sudo journalctl -u s3-uploader -n 50  # 최근 50줄
```

### 헬스체크
- **ELB 헬스체크**: `/health` 엔드포인트
- **수동 확인**: `curl http://localhost:8081/health`

## 🚀 향후 확장 계획

### 1. 보안 강화
- HTTPS 설정 (SSL 인증서)
- 도메인 연결 (Route 53)
- WAF 적용

### 2. 기능 확장
- 로그인 시스템 (사용자 구분 활용)
- 파일 관리 대시보드
- 사용 통계 및 분석

### 3. 인프라 개선
- Auto Scaling Group
- RDS 데이터베이스 (SQLite → PostgreSQL/MySQL)
- CloudWatch 모니터링
- S3 버킷 정책 세분화

## 📞 문제 해결 가이드

### 서비스가 시작되지 않을 때
```bash
sudo systemctl status s3-uploader
sudo journalctl -u s3-uploader -n 20
```

### ELB 헬스체크 실패 시
```bash
curl http://localhost:8081/health
sudo netstat -tlnp | grep 8081
```

### 파일 업로드 실패 시
- IAM 역할 권한 확인
- S3 버킷 존재 확인
- 네트워크 연결 확인

## 📝 개발 노트

### 주요 Python 패키지
- Flask: 웹 프레임워크
- boto3: AWS SDK
- sqlite3: 데이터베이스

### 주요 JavaScript 기능
- 드래그 앤 드롭 API
- Fetch API (파일 업로드)
- localStorage (사용자 정보)
- Clipboard API + 폴백

---

## 🎯 현재 상태: 완전 동작 ✅

**마지막 업데이트**: 2025-07-09
**상태**: 프로덕션 레디
**접속 URL**: http://s3-uploader-alb-1960127651.us-west-2.elb.amazonaws.com

모든 기능이 정상 작동하며, ELB를 통한 안정적인 서비스 제공이 가능한 상태입니다.
