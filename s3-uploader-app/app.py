from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, Response, stream_with_context
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
import uuid
from datetime import datetime, timedelta
import mimetypes
import traceback
import logging
import hashlib
import sqlite3
import secrets
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS S3 설정 - 고정된 버킷과 리전 사용
BUCKET_NAME = 'presigned-url-generator-janghwan'
AWS_REGION = 'us-west-2'
DB_FILE = 'file_links.db'

# 데이터베이스 초기화
def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secure_key TEXT UNIQUE NOT NULL,
            s3_key TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            content_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            download_count INTEGER DEFAULT 0
        )
    ''')
    
    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_secure_key ON file_links(secure_key)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON file_links(expires_at)')
    
    conn.commit()
    conn.close()

def generate_secure_key():
    """보안 키 생성 (32자리 랜덤 문자열)"""
    return secrets.token_urlsafe(24)  # 32자리 URL-safe 문자열

def store_file_link(s3_key, original_filename, file_size, content_type, expiration_days):
    """파일 링크를 데이터베이스에 저장"""
    secure_key = generate_secure_key()
    expires_at = datetime.now() + timedelta(days=expiration_days)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO file_links 
            (secure_key, s3_key, original_filename, file_size, content_type, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (secure_key, s3_key, original_filename, file_size, content_type, expires_at))
        
        conn.commit()
        logger.info(f"파일 링크 저장 완료: {secure_key} -> {s3_key}")
        return secure_key
    except Exception as e:
        logger.error(f"파일 링크 저장 실패: {e}")
        return None
    finally:
        conn.close()

def get_file_info(secure_key):
    """보안 키로 파일 정보 조회"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT s3_key, original_filename, file_size, content_type, expires_at, download_count
            FROM file_links 
            WHERE secure_key = ? AND expires_at > datetime('now')
        ''', (secure_key,))
        
        result = cursor.fetchone()
        if result:
            return {
                's3_key': result[0],
                'original_filename': result[1],
                'file_size': result[2],
                'content_type': result[3],
                'expires_at': result[4],
                'download_count': result[5]
            }
        return None
    except Exception as e:
        logger.error(f"파일 정보 조회 실패: {e}")
        return None
    finally:
        conn.close()

def increment_download_count(secure_key):
    """다운로드 횟수 증가"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE file_links 
            SET download_count = download_count + 1 
            WHERE secure_key = ?
        ''', (secure_key,))
        conn.commit()
    except Exception as e:
        logger.error(f"다운로드 횟수 업데이트 실패: {e}")
    finally:
        conn.close()

def cleanup_expired_links():
    """만료된 링크 정리"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM file_links WHERE expires_at <= datetime('now')")
        deleted_count = cursor.rowcount
        conn.commit()
        if deleted_count > 0:
            logger.info(f"만료된 링크 {deleted_count}개 정리 완료")
    except Exception as e:
        logger.error(f"만료된 링크 정리 실패: {e}")
    finally:
        conn.close()

# S3 클라이언트 생성
try:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    logger.info(f"S3 클라이언트 생성 완료 - 리전: {AWS_REGION}")
except Exception as e:
    logger.error(f"S3 클라이언트 생성 실패: {e}")
    s3_client = None

def ensure_bucket_exists():
    """S3 버킷이 존재하는지 확인하고 없으면 생성"""
    if not s3_client:
        logger.error("S3 클라이언트가 초기화되지 않았습니다.")
        return False
        
    try:
        # 버킷 존재 여부 확인
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        logger.info(f"버킷 '{BUCKET_NAME}'이 이미 존재합니다.")
        return True
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            # 버킷이 존재하지 않으면 생성
            try:
                if AWS_REGION == 'us-east-1':
                    s3_client.create_bucket(Bucket=BUCKET_NAME)
                else:
                    s3_client.create_bucket(
                        Bucket=BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
                    )
                logger.info(f"버킷 '{BUCKET_NAME}'을 생성했습니다.")
                return True
            except ClientError as create_error:
                logger.error(f"버킷 생성 실패: {create_error}")
                return False
        else:
            logger.error(f"버킷 확인 실패: {e}")
            return False
    except NoCredentialsError:
        logger.error("AWS 자격 증명이 설정되지 않았습니다.")
        return False
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return False

def upload_file_to_s3(file, filename=None):
    """파일을 S3에 업로드"""
    if not s3_client:
        logger.error("S3 클라이언트가 초기화되지 않았습니다.")
        return None
        
    try:
        # 파일명 처리 - 타임스탬프 추가로 중복 방지
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = file.filename
            name, ext = os.path.splitext(original_filename)
            filename = f"{timestamp}_{name}{ext}"
        
        # Content-Type 설정
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        
        logger.info(f"파일 업로드 시작: {filename}")
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': content_type}
        )
        logger.info(f"파일 업로드 완료: {filename}")
        return filename
    except ClientError as e:
        logger.error(f"파일 업로드 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"예상치 못한 업로드 오류: {e}")
        return None

def generate_presigned_url(filename, expiration_days=7):
    """보안 강화된 Presigned URL 생성 - 공유 가능"""
    if not s3_client:
        logger.error("S3 클라이언트가 초기화되지 않았습니다.")
        return None
        
    try:
        expiration_seconds = expiration_days * 24 * 60 * 60  # 일을 초로 변환
        
        # 보안 강화된 presigned URL 생성 (V4 서명 사용)
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME, 
                'Key': filename,
                'ResponseContentDisposition': f'attachment; filename="{filename}"'
            },
            ExpiresIn=expiration_seconds,
            HttpMethod='GET'
        )
        
        # URL에서 민감한 정보 마스킹 (로그용)
        masked_url = response.split('?')[0] + '?[SECURED_PARAMETERS]'
        logger.info(f"Presigned URL 생성 완료: {filename} -> {masked_url}")
        
        return response
    except ClientError as e:
        logger.error(f"Presigned URL 생성 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"예상치 못한 URL 생성 오류: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("파일 업로드 요청 받음")
        
        # 요청 데이터 디버깅
        logger.info(f"Request files keys: {list(request.files.keys())}")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        
        # AWS 자격 증명 확인
        if not s3_client:
            logger.error("AWS 자격 증명이 설정되지 않았습니다.")
            return jsonify({'error': 'AWS 자격 증명이 설정되지 않았습니다. AWS CLI를 설정하거나 환경 변수를 확인해주세요.'}), 500
        
        # 다중 파일 처리 - 'files' 키로 수정
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            logger.error(f"파일이 선택되지 않았습니다. files: {files}")
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파일 개수 제한 확인
        if len(files) > 10:
            return jsonify({'error': '최대 10개의 파일만 업로드할 수 있습니다.'}), 400
        
        expiration_days = int(request.form.get('expiration_days', 7))
        logger.info(f"업로드 파일 개수: {len(files)}, 유효기간: {expiration_days}일")
        
        # 버킷 존재 확인
        if not ensure_bucket_exists():
            return jsonify({'error': 'S3 버킷 설정에 실패했습니다. AWS 권한을 확인해주세요.'}), 500
        
        uploaded_files = []
        total_size = 0
        
        # 각 파일 처리
        for file in files:
            if file.filename == '':
                continue
                
            logger.info(f"처리 중인 파일: {file.filename}")
            
            # 파일 크기 계산
            file.seek(0, 2)  # 파일 끝으로 이동
            file_size = file.tell()
            file.seek(0)  # 파일 시작으로 되돌리기
            total_size += file_size
            
            logger.info(f"파일 크기: {file_size} bytes")
            
            # 파일 업로드
            uploaded_filename = upload_file_to_s3(file)
            if not uploaded_filename:
                logger.error(f"파일 업로드 실패: {file.filename}")
                return jsonify({'error': f'파일 "{file.filename}" 업로드에 실패했습니다. S3 권한을 확인해주세요.'}), 500
            
            logger.info(f"S3 업로드 성공: {uploaded_filename}")
            
            # Content-Type 확인
            content_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            # 보안 키 생성 및 데이터베이스 저장
            secure_key = store_file_link(
                uploaded_filename, 
                file.filename, 
                file_size, 
                content_type, 
                expiration_days
            )
            
            if not secure_key:
                logger.error(f"보안 링크 생성 실패: {file.filename}")
                return jsonify({'error': f'파일 "{file.filename}"의 보안 링크 생성에 실패했습니다.'}), 500
            
            logger.info(f"보안 키 생성 성공: {secure_key}")
            
            # 안전한 다운로드 URL 생성
            download_url = f"{request.host_url}download/{secure_key}"
            
            uploaded_files.append({
                'original_filename': file.filename,
                'uploaded_filename': uploaded_filename,
                'download_url': download_url,
                'secure_key': secure_key,
                'file_size': file_size
            })
        
        # 만료 시간 계산
        expiry_date = datetime.now() + timedelta(days=expiration_days)
        
        result = {
            'success': True,
            'bucket_name': BUCKET_NAME,
            'region': AWS_REGION,
            'files': uploaded_files,
            'file_count': len(uploaded_files),
            'total_size': total_size,
            'expiry_date': expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'expiration_days': expiration_days
        }
        
        logger.info(f"업로드 성공: {len(uploaded_files)}개 파일")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"업로드 처리 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'서버 내부 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/download/<secure_key>')
def download_file(secure_key):
    """보안 키를 통한 프록시 다운로드"""
    try:
        # 파일 정보 조회
        file_info = get_file_info(secure_key)
        if not file_info:
            return "파일을 찾을 수 없거나 링크가 만료되었습니다.", 404
        
        # 다운로드 횟수 증가
        increment_download_count(secure_key)
        
        # S3에서 파일 스트리밍
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_info['s3_key'])
            
            def generate():
                for chunk in response['Body'].iter_chunks(chunk_size=8192):
                    yield chunk
            
            # 한글 파일명 인코딩 처리
            from urllib.parse import quote
            encoded_filename = quote(file_info['original_filename'].encode('utf-8'))
            
            # 응답 헤더 설정
            headers = {
                'Content-Type': file_info['content_type'],
                'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                'Content-Length': str(file_info['file_size']),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            
            logger.info(f"파일 다운로드 시작: {secure_key} -> {file_info['original_filename']}")
            
            return Response(
                stream_with_context(generate()),
                headers=headers
            )
            
        except ClientError as e:
            logger.error(f"S3 파일 조회 실패: {e}")
            return "파일 다운로드 중 오류가 발생했습니다.", 500
            
    except Exception as e:
        logger.error(f"다운로드 처리 중 오류: {e}")
        logger.error(traceback.format_exc())
        return "다운로드 중 오류가 발생했습니다.", 500

@app.route('/file-info/<secure_key>')
def get_file_info_api(secure_key):
    """파일 정보 조회 API (다운로드 없이)"""
    try:
        file_info = get_file_info(secure_key)
        if not file_info:
            return jsonify({'error': '파일을 찾을 수 없거나 링크가 만료되었습니다.'}), 404
        
        return jsonify({
            'original_filename': file_info['original_filename'],
            'file_size': file_info['file_size'],
            'content_type': file_info['content_type'],
            'expires_at': file_info['expires_at'],
            'download_count': file_info['download_count']
        })
    except Exception as e:
        logger.error(f"파일 정보 조회 중 오류: {e}")
        return jsonify({'error': '파일 정보 조회 중 오류가 발생했습니다.'}), 500

@app.route('/health')
def health_check():
    try:
        # AWS 자격 증명 확인
        if not s3_client:
            return jsonify({
                'status': 'unhealthy',
                'error': 'AWS 자격 증명이 설정되지 않았습니다.',
                'bucket': BUCKET_NAME,
                'region': AWS_REGION
            }), 500
        
        # 버킷 접근 가능 여부 확인
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        
        return jsonify({
            'status': 'healthy',
            'bucket': BUCKET_NAME,
            'region': AWS_REGION
        })
    except ClientError as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'bucket': BUCKET_NAME,
            'region': AWS_REGION
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': f'예상치 못한 오류: {str(e)}',
            'bucket': BUCKET_NAME,
            'region': AWS_REGION
        }), 500

@app.route('/bucket-info')
def bucket_info():
    """버킷 정보 확인 엔드포인트"""
    try:
        if not s3_client:
            return jsonify({
                'bucket_name': BUCKET_NAME,
                'region': AWS_REGION,
                'exists': False,
                'error': 'AWS 자격 증명이 설정되지 않았습니다.'
            })
        
        # 버킷 존재 여부 확인
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        
        # 버킷 내 객체 수 확인 (최대 1000개까지)
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, MaxKeys=1000)
        object_count = response.get('KeyCount', 0)
        
        return jsonify({
            'bucket_name': BUCKET_NAME,
            'region': AWS_REGION,
            'exists': True,
            'object_count': object_count
        })
    except ClientError as e:
        return jsonify({
            'bucket_name': BUCKET_NAME,
            'region': AWS_REGION,
            'exists': False,
            'error': str(e)
        })
    except Exception as e:
        return jsonify({
            'bucket_name': BUCKET_NAME,
            'region': AWS_REGION,
            'exists': False,
            'error': f'예상치 못한 오류: {str(e)}'
        })

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 에러 발생: {error}")
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '요청한 페이지를 찾을 수 없습니다.'}), 404

if __name__ == '__main__':
    print(f"S3 버킷: {BUCKET_NAME}")
    print(f"AWS 리전: {AWS_REGION}")
    print("=" * 50)
    
    # 데이터베이스 초기화
    init_database()
    print("✅ 데이터베이스 초기화 완료")
    
    # 만료된 링크 정리
    cleanup_expired_links()
    
    # AWS 자격 증명 확인
    try:
        if s3_client:
            # 간단한 AWS 연결 테스트
            s3_client.list_buckets()
            print("✅ AWS 자격 증명 확인됨")
        else:
            print("❌ AWS 자격 증명 설정 필요")
    except NoCredentialsError:
        print("❌ AWS 자격 증명이 설정되지 않았습니다.")
        print("다음 명령어로 설정하세요: aws configure")
    except Exception as e:
        print(f"⚠️  AWS 연결 확인 중 오류: {e}")
    
    print("=" * 50)
    print("🔒 보안 강화된 프록시 다운로드 시스템 활성화")
    print("📊 SQLite 데이터베이스 기반 링크 관리")
    print("=" * 50)
    
    # 배포 환경에서는 환경 변수에서 포트 가져오기
    port = int(os.environ.get('PORT', 8081))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(debug=debug, host=host, port=port)
