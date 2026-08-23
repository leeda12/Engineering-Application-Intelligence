"""Serve an exported frontend and reverse-proxy /api/v1 to local FastAPI for visual QA."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/"frontend/out"),**kwargs)
    def _proxy(self):
        length=int(self.headers.get("Content-Length","0")); body=self.rfile.read(length) if length else None
        headers={k:v for k,v in self.headers.items() if k.lower() in {"content-type","idempotency-key"}}
        request=Request("http://127.0.0.1:8000"+self.path,data=body,headers=headers,method=self.command)
        try: response=urlopen(request,timeout=30); status=response.status; payload=response.read(); response_headers=response.headers
        except HTTPError as exc: status=exc.code; payload=exc.read(); response_headers=exc.headers
        self.send_response(status); self.send_header("Content-Type",response_headers.get("Content-Type","application/json")); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(payload)
    def do_GET(self):
        if self.path.startswith("/api/v1/"): self._proxy()
        else: super().do_GET()
    def do_POST(self):
        if self.path.startswith("/api/v1/"): self._proxy()
        else: self.send_error(405)

if __name__=="__main__": ThreadingHTTPServer(("127.0.0.1",3000),Handler).serve_forever()
