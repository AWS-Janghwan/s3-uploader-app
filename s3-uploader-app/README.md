# S3 파일 업로더 & Presigned URL 생성기

웹 기반으로 파일을 AWS S3에 업로드하고 공유 가능한 Presigned URL을 생성하는 애플리케이션입니다.

## 주요 기능

- 🚀 **드래그 앤 드롭** 파일 업로드
- 📁 **다중 파일 업로드** (최대 10개)
- 📅 **유효기간 설정** (1일~30일)
- 🔗 **Presigned URL 자동 생성**
- 📋 **하이퍼링크 형태** 복사 (메일/메신저 친화적)
- 📱 **반응형 웹 디자인**
- ⚡ **실시간 업로드 진행률**
- 🛡️ **파일명 중복 방지** (타임스탬프 자동 추가)
- 📊 **개별/전체 링크 복사** 기능

## S3 설정

- **버킷명**: `presigned-url-generator-janghwan`
- **리전**: `us-west-2` (미국 서부)
- **자동 버킷 생성**: 버킷이 없으면 자동으로 생성됩니다

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. AWS 자격 증명 설정
AWS CLI를 통해 자격 증명을 설정하거나 환경 변수를 설정하세요:

```bash
# AWS CLI 설정
aws configure

# 또는 환경 변수 설정
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

### 3. 애플리케이션 실행
```bash
# 자동 실행 스크립트 사용
./run.sh

# 또는 직접 실행
python app.py
```

### 4. 웹 브라우저에서 접속
```
http://localhost:8080
```

## 사용법

1. **파일 선택**: 드래그 앤 드롭 또는 클릭하여 최대 10개 파일 선택
2. **유효기간 설정**: 링크가 유효할 기간 선택 (기본값: 7일)
3. **업로드**: "업로드 & URL 생성" 버튼 클릭
4. **링크 공유**: 생성된 하이퍼링크를 복사하여 메일/메신저에 붙여넣기

### 💡 편리한 공유 방법
- **하이퍼링크 형태**: `<a href="https://..." target="_blank">파일명.pdf</a>`
- **메일/메신저 붙여넣기**: 링크가 클릭 가능한 형태로 표시됨
- **개별 복사**: 각 파일별로 개별 복사 가능
- **전체 복사**: 모든 파일 링크를 한번에 복사

## 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Cloud**: AWS S3
- **Icons**: Font Awesome

## 주요 특징

### 보안
- 고정된 S3 버킷 사용으로 관리 용이
- **단축 URL 시스템**으로 AWS 자격 증명 정보 숨김
- 설정된 기간 후 자동 링크 만료
- AWS IAM 권한 기반 접근 제어
- 파일명 중복 방지 (타임스탬프 자동 추가)
- **보안 강화된 presigned URL** 생성

### 사용자 경험
- 직관적인 드래그 앤 드롭 인터페이스
- 실시간 파일 정보 표시
- 업로드 진행률 표시
- 원클릭 URL 복사 기능
- 상세한 업로드 결과 정보

### 확장성
- 모든 파일 형식 지원
- 대용량 파일 업로드 지원
- 반응형 디자인으로 모바일 지원

## 파일 구조

```
s3-uploader-app/
├── app.py              # Flask 메인 애플리케이션
├── templates/
│   └── index.html      # 웹 인터페이스
├── requirements.txt    # Python 의존성
├── run.sh             # 실행 스크립트
├── Dockerfile         # Docker 지원
├── docker-compose.yml # Docker Compose 설정
└── README.md          # 프로젝트 문서
```

## API 엔드포인트

### POST /upload
파일을 업로드하고 Presigned URL을 생성합니다.

**Parameters:**
- `file`: 업로드할 파일
- `expiration_days`: 링크 유효 기간 (일 단위)

**Response:**
```json
{
    "success": true,
    "bucket_name": "presigned-url-generator-janghwan",
    "filename": "20240109_143022_example.pdf",
    "original_filename": "example.pdf",
    "presigned_url": "https://...",
    "expiry_date": "2024-01-16 14:30:22 UTC",
    "file_size": 1048576,
    "region": "us-west-2"
}
```

### GET /health
애플리케이션 상태를 확인합니다.

### GET /bucket-info
S3 버킷 정보를 확인합니다.

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 | - |
| `AWS_DEFAULT_REGION` | AWS 리전 | us-west-2 |

## Docker 실행

```bash
# Docker Compose로 실행
docker-compose up --build

# 또는 Docker로 직접 실행
docker build -t s3-uploader .
docker run -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  s3-uploader
```

## 주의사항

1. **AWS 비용**: S3 스토리지 및 데이터 전송에 따른 비용이 발생할 수 있습니다.
2. **보안**: 프로덕션 환경에서는 적절한 보안 설정을 적용하세요.
3. **파일 관리**: 업로드된 파일은 수동으로 관리해야 합니다.
4. **권한**: S3 버킷에 대한 적절한 읽기/쓰기 권한이 필요합니다.

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해 주세요.
