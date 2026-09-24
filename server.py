"""Raw HTTP socket server for inspecting multipart/form-data requests."""

from __future__ import annotations

import argparse
import os
import re
import socket
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from pathlib import Path


BUFFER_SIZE = 64 * 1024
HEADER_SEPARATOR = b"\r\n\r\n"


class SocketServer:
    def __init__(self, output_dir: str | Path = "request") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def receive_request(client: socket.socket) -> bytes:
        """Read one complete HTTP request using its Content-Length header."""
        received = bytearray()
        header_end = -1
        content_length = 0

        while header_end < 0:
            chunk = client.recv(BUFFER_SIZE)
            if not chunk:
                return bytes(received)
            received.extend(chunk)
            header_end = received.find(HEADER_SEPARATOR)

        raw_headers = bytes(received[:header_end])
        match = re.search(br"(?im)^Content-Length:\s*(\d+)\s*$", raw_headers)
        if match:
            content_length = int(match.group(1))

        expected_size = header_end + len(HEADER_SEPARATOR) + content_length
        while len(received) < expected_size:
            chunk = client.recv(min(BUFFER_SIZE, expected_size - len(received)))
            if not chunk:
                break
            received.extend(chunk)

        return bytes(received)

    def save_raw_request(self, request_data: bytes, timestamp: str) -> Path:
        output_path = self.output_dir / f"{timestamp}.bin"
        output_path.write_bytes(request_data)
        return output_path

    def save_multipart_images(self, request_data: bytes, timestamp: str) -> list[Path]:
        """Extract image parts without including multipart headers/boundaries."""
        try:
            raw_headers, body = request_data.split(HEADER_SEPARATOR, 1)
        except ValueError:
            return []

        # The first line is the HTTP request line, not a MIME header.
        _, separator, mime_headers = raw_headers.partition(b"\r\n")
        if not separator:
            return []
        message = BytesParser(policy=default).parsebytes(
            mime_headers + HEADER_SEPARATOR + body
        )
        if not message.is_multipart():
            return []

        saved_images: list[Path] = []
        image_number = 0
        for part in message.iter_attachments():
            content_type = part.get_content_type()
            if not content_type.startswith("image/"):
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue

            image_number += 1
            original_name = Path(part.get_filename() or "image").name
            extension = Path(original_name).suffix.lower()
            if not re.fullmatch(r"\.[a-z0-9]{1,10}", extension):
                extension = ".bin"

            suffix = "" if image_number == 1 else f"-{image_number}"
            output_path = self.output_dir / f"{timestamp}-image{suffix}{extension}"
            output_path.write_bytes(payload)
            saved_images.append(output_path)

        return saved_images

    @staticmethod
    def send_response(client: socket.socket, status: str, message: str) -> None:
        body = message.encode("utf-8")
        response = (
            f"HTTP/1.1 {status}\r\n"
            "Server: assignment4-socket-server/1.0\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("ascii") + body
        client.sendall(response)

    def handle_client(self, client: socket.socket, address: tuple[str, int]) -> None:
        client.settimeout(10)
        request_data = self.receive_request(client)
        if not request_data:
            self.send_response(client, "400 Bad Request", "Empty request\n")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        raw_path = self.save_raw_request(request_data, timestamp)
        image_paths = self.save_multipart_images(request_data, timestamp)

        print(f"Request from {address[0]}:{address[1]}")
        print(f"Saved raw request: {raw_path}")
        for image_path in image_paths:
            print(f"Saved image: {image_path}")

        summary = f"Saved {raw_path.name}; extracted {len(image_paths)} image(s)\n"
        self.send_response(client, "200 OK", summary)

    def run(self, host: str, port: int, once: bool = False) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((host, port))
            server_socket.listen(10)
            print(f"Socket server listening on {host}:{port}")

            while True:
                client, address = server_socket.accept()
                with client:
                    try:
                        self.handle_client(client, address)
                    except (OSError, ValueError) as error:
                        print(f"Failed to process request: {error}")
                        try:
                            self.send_response(client, "400 Bad Request", f"{error}\n")
                        except OSError:
                            pass
                if once:
                    break


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output-dir", default="request")
    parser.add_argument(
        "--once", action="store_true", help="Handle one request and then stop"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    SocketServer(args.output_dir).run(args.host, args.port, args.once)
