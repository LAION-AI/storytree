import json, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
ZEN='https://opencode.ai/zen/v1/responses'
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); req=json.loads(self.rfile.read(n))
        inp='\n'.join(f"{m['role']}: {m['content']}" for m in req.get('messages',[]) if isinstance(m.get('content'),str))
        body=json.dumps({'model':req.get('model','muse-spark-1.2-contributor-free'),'input':inp}).encode()
        r=urllib.request.Request(ZEN,data=body,headers={'Content-Type':'application/json','User-Agent':'curl/8.5.0'})
        try:
            resp=json.loads(urllib.request.urlopen(r,timeout=600).read())
            txt=''
            for o in resp.get('output',[]):
                if o.get('type')=='message':
                    for c in o.get('content',[]):
                        if isinstance(c,dict) and c.get('text'): txt+=c['text']
        except Exception as e:
            txt=f'ERROR: {e}'
        out=json.dumps({'id':'shim','object':'chat.completion','model':req.get('model'),'choices':[{'index':0,'message':{'role':'assistant','content':txt},'finish_reason':'stop'}]}).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
HTTPServer(('127.0.0.1',8222),H).serve_forever()
