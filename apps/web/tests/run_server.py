import sys
import tempfile
from pathlib import Path
import uvicorn
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'server'))
from app.main import create_app
with tempfile.TemporaryDirectory(prefix='style-explorer-browser-') as data:
    uvicorn.run(create_app(data, origin='http://127.0.0.1:8766', bootstrap_secret='browser-test'), host='127.0.0.1', port=8766, log_level='warning')
