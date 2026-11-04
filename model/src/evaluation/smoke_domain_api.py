"""POST multipart thật qua FastAPI/TestClient, checkpoint thật, SQLite tạm.

Không gọi dịch vụ dev và không ghi dữ liệu người dùng. Mỗi ca lặp cùng ảnh
ba lần để kiểm tra hợp đồng endpoint (không phải ba mẫu đánh giá độc lập).
"""

import argparse
import csv
import json
import os
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    root = Path(args.run).resolve()
    temporary = Path(tempfile.mkdtemp(prefix="agrixai-domain-api-"))
    os.environ.update(
        DEBUG="false",
        DATABASE_URL=f"sqlite:///{(temporary / 'db.sqlite').as_posix()}",
        STORAGE_DIR=str(temporary / "storage"),
        MODEL_CHECKPOINT="",
        MODEL_GATE_CHECKPOINT="",
    )
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))
    import torch
    from app.api.deps import get_current_user
    from app.db.session import Base, engine
    from app.main import app
    from app.models.user import User, UserRole
    from app.services import diagnosis_service
    from app.services.storage.local import open_and_normalize
    from app.services.xai.overlay import has_visible_region
    from fastapi.testclient import TestClient

    from src.predictor import DiseasePredictor
    from src.training.adapt_domain import write_json

    torch.set_num_threads(4)

    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_current_user] = lambda: User(
        id=1,
        username="smoke",
        role=UserRole.FARMER,
        full_name="Kiểm tra tích hợp",
        is_active=True,
        hashed_password="unused",
    )
    predictor = DiseasePredictor(
        selection["checkpoint"],
        device="cpu",
        gate_checkpoint="checkpoints/organ_gate.pt",
        xai_config_path=root / "evaluation/deployment.yaml",
    )
    diagnosis_service.get_predictor = lambda: predictor
    records = json.loads((root / "evaluation/guard-pv-test.json").read_text(encoding="utf-8"))
    records += json.loads((root / "evaluation/guard-pd-test.json").read_text(encoding="utf-8"))
    accepted = [r for r in records if r["accepted"] and r["prediction"] != "healthy"]
    hidden = [r for r in records if not r["accepted"] and r["prediction"] != "healthy"]
    with open("data/processed/gate-split.csv", encoding="utf-8") as stream:
        negatives = [
            r
            for r in csv.DictReader(stream)
            if r["split"] == "test" and r["label"] == "not_tomato_leaf"
        ]
    cases = {}
    for kind, rows in (("visible", accepted), ("hidden", hidden), ("rejected", negatives)):
        for row in rows:
            raw = Path(row["path"]).read_bytes()
            result = predictor.predict(open_and_normalize(raw))
            if kind == "rejected" and result.disease_key == "not_tomato_leaf":
                break
            if result.disease_key == "not_tomato_leaf":
                continue
            visible = result.heatmap is not None and has_visible_region(result.heatmap)
            if kind == "visible" and visible:
                break
            if kind == "hidden" and result.heatmap is None and result.disease_key != "healthy":
                break
        else:
            raise RuntimeError(f"Không tìm được ca {kind} bằng checkpoint thật")
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/diagnoses",
                data={"save": "false"},
                files=[("files", (f"image{i}.jpg", raw, "image/jpeg")) for i in range(3)],
            )
        payload = response.json()
        if kind == "rejected":
            assert response.status_code == 422, payload
        else:
            assert response.status_code == 201, payload
            if kind == "hidden":
                assert payload["overlay_path"] is None, payload
                assert all(image["overlay_path"] is None for image in payload["images"])
                assert "chụp lại" in payload["explanation"].lower(), payload
            else:
                assert payload["overlay_path"] is not None, payload
        cases[kind] = {"source": row["path"], "status": response.status_code, "response": payload}
    predictor.close()
    app.dependency_overrides.clear()
    write_json(root / "api-smoke.json", cases)
    print("POST thật: vùng rõ -> overlay; vùng không rõ -> null + chụp lại; ảnh âm -> 422")


if __name__ == "__main__":
    main()
