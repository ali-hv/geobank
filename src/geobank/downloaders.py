import urllib.request
import tempfile
import requests
import tqdm
import time
import socket
import logging
from urllib.error import URLError

logger = logging.getLogger(__name__)


def download_with_retry(url, timeout=10, retries=5):
    for attempt in range(retries):
        try:
            logger.info(f"Downloading {url} (Attempt {attempt + 1}/{retries})")
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read()
        except (URLError, socket.timeout) as e:
            logger.warning(f"Download failed: {e}. Retrying in 2 seconds...")
            if attempt == retries - 1:
                raise
            time.sleep(2)
    return None


def download_heavy_file(url, timeout=10, retries=5):
    for attempt in range(retries):
        try:
            logger.info(f"Downloading {url} (Attempt {attempt + 1}/{retries})")
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
            
                total = int(r.headers.get('content-length', 0))
                chunk_size = 10 * 1024 * 1024  # 2MB
            
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    # Use tqdm.tqdm if tqdm is imported as a module, or just tqdm if it's the class
                    # Assuming 'import tqdm' -> tqdm.tqdm
                    with tqdm.tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024) as bar:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                tmp_file.write(chunk)
                                bar.update(len(chunk))
            
                return tmp_file.name
        except (requests.RequestException, socket.timeout) as e:
            logger.warning(f"Download failed: {e}. Retrying in 2 seconds...")
            if attempt == retries - 1:
                raise
            time.sleep(2)
    return None