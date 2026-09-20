"""Download the benchmark model using the operating system certificate store."""
import ssl
import httpx
from huggingface_hub import set_client_factory, snapshot_download

set_client_factory(lambda: httpx.Client(verify=ssl.create_default_context(), follow_redirects=True))
print(snapshot_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                        allow_patterns=['*.json', '*.safetensors', '*.txt', '*.model'],
                        ignore_patterns=['onnx/*', 'openvino/*']), flush=True)
