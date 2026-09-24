# Socket Server 실행 결과

## 실행 결과

`curl`로 텍스트 필드와 PNG 이미지를 `multipart/form-data` 형식으로 전송했다.
Python 소켓 서버는 HTTP 요청 전체를 이진 파일로 저장하고, 이미지 파트만
분리하여 별도의 PNG 파일로 저장했다.

```text
Socket server listening on 127.0.0.1:8000
Saved raw request: result/2026-09-24-18-05-06.bin
Saved image: result/2026-09-24-18-05-06-image.png
Saved 2026-09-24-18-05-06.bin; extracted 1 image(s)
```

## 원본 HTTP 요청

- 파일: `result/2026-09-24-18-05-06.bin`
- 요청: `POST /api_root/Post/ HTTP/1.1`
- 형식: `multipart/form-data`
- 포함 필드: `author`, `title`, `text`, `created_date`, `published_date`, `image`
- 이미지 파일명: `pig.png`

## 추출 이미지

![multipart에서 추출한 이미지](result/2026-09-24-18-05-06-image.png)

원본 이미지와 추출 이미지의 SHA-256 해시가 일치하므로 이미지 데이터가
손상 없이 분리되었음을 확인했다.

```text
541a1ef5373be3dc49fc542fd9a65177b664aec01c8d8608f99e6ec95577d8c1  원본 이미지
541a1ef5373be3dc49fc542fd9a65177b664aec01c8d8608f99e6ec95577d8c1  추출 이미지
```
