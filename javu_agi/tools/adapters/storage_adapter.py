from __future__ import annotations
import os, json, time, pathlib
from typing import Dict, Any, Optional

try:
    import boto3
except Exception:
    boto3 = None


class StorageAdapter:
    def __init__(self):
        self.backend = os.getenv("STORAGE_BACKEND", "local")  # "s3"|"minio"|"local"
        self.bucket = os.getenv("STORAGE_BUCKET", "")
        self.prefix = os.getenv("STORAGE_PREFIX", "artifacts/")
        self.local_dir = os.getenv("STORAGE_LOCAL_DIR", "artifacts")
        if self.backend != "local" and boto3:
            endpoint = os.getenv("STORAGE_ENDPOINT", "")
            session = boto3.session.Session()
            self.s3 = session.client(
                service_name="s3",
                endpoint_url=(endpoint or None),
                aws_access_key_id=os.getenv("STORAGE_ACCESS_KEY"),
                aws_secret_access_key=os.getenv("STORAGE_SECRET_KEY"),
                region_name=os.getenv("STORAGE_REGION", "us-east-1"),
            )
        else:
            self.s3 = None
        pathlib.Path(self.local_dir).mkdir(parents=True, exist_ok=True)

    def put_text(self, key: str, text: str) -> Dict[str, Any]:
        key = self.prefix + key if not key.startswith(self.prefix) else key
        if self.backend == "local" or not self.s3:
            p = pathlib.Path(self.local_dir) / key.replace(self.prefix, "", 1)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            return {"status": "ok", "path": str(p)}
        # s3/minio
        try:
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=text.encode("utf-8"))
            return {"status": "ok", "bucket": self.bucket, "key": key}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def get_text(self, key: str) -> Dict[str, Any]:
        key = self.prefix + key if not key.startswith(self.prefix) else key
        if self.backend == "local" or not self.s3:
            p = pathlib.Path(self.local_dir) / key.replace(self.prefix, "", 1)
            if not p.exists():
                return {"status": "error", "reason": "not_found"}
            return {"status": "ok", "text": p.read_text(encoding="utf-8")}
        try:
            obj = self.s3.get_object(Bucket=self.bucket, Key=key)
            return {"status": "ok", "text": obj["Body"].read().decode("utf-8")}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
