"""Upload data/exports/*.json to S3.

Run from scripts/:
    export DATA_BUCKET_NAME=nbajinni-dev-data-exports
    poetry run python upload_to_s3.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from nbajinni_shared.logging import configure_logging, get_logger

load_dotenv()
configure_logging()
logger = get_logger("upload")

EXPORTS_DIR = Path(__file__).parent.parent / "data" / "exports"
S3_PREFIX = "exports"


def main():
    bucket = os.environ["DATA_BUCKET_NAME"]
    s3 = boto3.client("s3")

    json_files = sorted(EXPORTS_DIR.glob("*.json"))
    if not json_files:
        logger.warning("no_files_found", path=str(EXPORTS_DIR))
        return

    for path in json_files:
        key = f"{S3_PREFIX}/{path.name}"
        try:
            s3.upload_file(str(path), bucket, key)
        except (BotoCoreError, ClientError) as e:
            logger.error("upload_failed", file=path.name, bucket=bucket, error=str(e))
            raise
        logger.info("file_uploaded", file=path.name, bucket=bucket, key=key)

    logger.info("upload_complete", files=len(json_files))


if __name__ == "__main__":
    main()
