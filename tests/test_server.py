import socket
import tempfile
import unittest
from pathlib import Path

from server import SocketServer


class FakeSocket:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = iter(chunks)

    def recv(self, _size: int) -> bytes:
        return next(self.chunks, b"")


class SocketServerTests(unittest.TestCase):
    def test_receive_request_uses_content_length(self) -> None:
        body = b"hello world"
        request = (
            b"POST / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            + f"Content-Length: {len(body)}\r\n\r\n".encode()
            + body
        )
        fake_socket = FakeSocket([request[:20], request[20:]])

        self.assertEqual(SocketServer.receive_request(fake_socket), request)

    def test_extracts_only_image_payload(self) -> None:
        boundary = "assignment4-boundary"
        image = b"\xff\xd8\xff\xe0example-jpeg-data\xff\xd9"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="title"\r\n\r\n'
            "socket test\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="image"; filename="sample.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode() + image + f"\r\n--{boundary}--\r\n".encode()
        request = (
            b"POST / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            + f"Content-Type: multipart/form-data; boundary={boundary}\r\n".encode()
            + f"Content-Length: {len(body)}\r\n\r\n".encode()
            + body
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            server = SocketServer(temp_dir)
            paths = server.save_multipart_images(request, "2026-09-23-12-00-00")

            self.assertEqual(len(paths), 1)
            self.assertEqual(paths[0].suffix, ".jpg")
            self.assertEqual(paths[0].read_bytes(), image)


if __name__ == "__main__":
    unittest.main()
