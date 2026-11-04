"""Kiểm HTTP thật: Uvicorn riêng, đăng ký thật, checkpoint/default YAML thật.

SQLite, tài khoản và storage đều ở thư mục tạm; không gọi backend dev đang
chạy và không ghi dữ liệu vào DB của nhóm. Chạy sau khi chốt cấu hình mặc định.
"""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import torch
import yaml

from src.training.adapt_domain import digest, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    root = Path(args.run).resolve()
    model_dir = Path(__file__).resolve().parents[2]
    backend = model_dir.parent / "backend"
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    expected = torch.load(selection["checkpoint"], map_location="cpu", weights_only=False)[
        "model_version"
    ]
    cfg_path = model_dir / "configs/default.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert cfg["xai"]["method"] == "gradcam_plusplus"
    assert cfg["xai"]["reliability"]["enabled"]
    assert cfg["preprocess"]["leaf_crop"]["enabled"] == selection["crop_enabled"]
    temporary = Path(tempfile.mkdtemp(prefix="agrixai-real-http-"))
    env = {
        **os.environ,
        "DEBUG": "false",
        "DATABASE_URL": f"sqlite:///{(temporary / 'db.sqlite').as_posix()}",
        "STORAGE_DIR": str(temporary / "storage"),
        "MODEL_CHECKPOINT": str(Path(selection["checkpoint"]).resolve()),
        "MODEL_PACKAGE_DIR": str(model_dir),
        "MODEL_GATE_CHECKPOINT": str(model_dir / "checkpoints/organ_gate.pt"),
        "MODEL_DEVICE": "cpu",
        "SECRET_KEY": secrets.token_urlsafe(40),
        "PYTHONUTF8": "1",
        "OMP_NUM_THREADS": "4",
        "MKL_NUM_THREADS": "4",
    }
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    server_log = temporary / "server.log"
    with server_log.open("wb") as log:
        subprocess.run(
            [sys.executable, "-m", "app.db.init_db"],
            cwd=backend,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            creationflags=flags,
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=backend,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        try:
            with httpx.Client(
                base_url=f"http://127.0.0.1:{port}", timeout=40, trust_env=False
            ) as client:
                for _ in range(100):
                    if server.poll() is not None:
                        raise RuntimeError(server_log.read_text(encoding="utf-8", errors="replace"))
                    if f"http://127.0.0.1:{port}" in server_log.read_text(
                        encoding="utf-8", errors="replace"
                    ):
                        break
                    time.sleep(0.5)
                else:
                    raise RuntimeError("Uvicorn chưa khởi động trong thời hạn kiểm tra")
                health = client.get("/health")
                health.raise_for_status()
                health = health.json()
                assert health["using_real_model"] and health["model_version"] == expected, health
                response = client.post(
                    "/api/v1/auth/register",
                    json={
                        "username": "validation_smoke",
                        "full_name": "Kiểm tra HTTP mô hình",
                        "email": "validation_smoke@agrixai.vn",
                        "password": secrets.token_urlsafe(24),
                    },
                )
                response.raise_for_status()
                headers = {"Authorization": "Bearer " + response.json()["access_token"]}
                references = json.loads((root / "api-smoke.json").read_text(encoding="utf-8"))
                results = {}
                for tag, case in references.items():
                    raw = Path(case["source"]).read_bytes()
                    response = client.post(
                        "/api/v1/diagnoses",
                        headers=headers,
                        data={"save": "true" if tag == "visible" else "false"},
                        files=[("files", (f"image{i}.jpg", raw, "image/jpeg")) for i in range(3)],
                    )
                    payload = response.json()
                    assert response.status_code == (422 if tag == "rejected" else 201), payload
                    if tag == "hidden":
                        assert (
                            payload["overlay_path"] is None
                            and "chụp lại" in payload["explanation"].lower()
                        ), payload
                        assert all(item["overlay_path"] is None for item in payload["images"])
                    elif tag == "visible":
                        assert payload["overlay_path"] is not None, payload
                        assert payload["id"] > 0 and payload["model_version"] == expected
                        persisted = client.get(
                            f"/api/v1/diagnoses/{payload['id']}", headers=headers
                        )
                        assert (
                            persisted.status_code == 200
                            and persisted.json()["model_version"] == expected
                        )
                        overlay = client.get(payload["overlay_url"])
                        assert overlay.status_code == 200 and overlay.headers[
                            "content-type"
                        ].startswith("image/")
                        assert len(overlay.content) > 100
                    results[tag] = {
                        "status": response.status_code,
                        "source": case["source"],
                        "response": payload,
                    }
                write_json(
                    root / "api-http.json",
                    {
                        "health": health,
                        "checkpoint_sha256": digest(selection["checkpoint"]),
                        "default_config_sha256": digest(cfg_path),
                        "uses_real_auth": True,
                        "uses_real_loader": True,
                        "isolated_database": True,
                        "cases": results,
                    },
                )
                print(
                    "HTTP thật qua Uvicorn: đăng ký, nạp checkpoint/default, overlay, ẩn vùng và từ chối ảnh âm đều đúng"
                )
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
    (root / "api-http-server.log").write_text(
        server_log.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
