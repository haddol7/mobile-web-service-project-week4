# Assignment 4 - Python Socket Server

This server receives a raw HTTP request from `curl`, saves the complete request
as a timestamped binary file, and extracts image parts from
`multipart/form-data` into separate image files.

## Run in WSL

```bash
cd /mnt/c/Users/haddo/mobile_web_service/week3/assignment4_socket_server
python3 server.py
```

In another WSL terminal, send an image request:

```bash
curl -X POST \
  -F "author=1" \
  -F "title=curl test" \
  -F "text=Assignment 4 multipart test" \
  -F "image=@/path/to/image.png;type=image/png" \
  http://127.0.0.1:8000/
```

Replace `/path/to/image.png` with an image path that exists in WSL. A Windows
file such as `C:\Users\name\Pictures\sample.png` is available to WSL as
`/mnt/c/Users/name/Pictures/sample.png`.

The `request/` directory will contain:

- `YYYY-MM-DD-HH-MM-SS.bin`: the complete HTTP request
- `YYYY-MM-DD-HH-MM-SS-image.png`: the extracted image

## Test

```bash
python3 -m unittest discover -s tests -v
```

To confirm that extraction did not alter the image, compare checksums:

```bash
sha256sum /path/to/image.png request/*-image.png
```
