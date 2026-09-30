import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
import app
from test_engine import BASE

class API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.old_db=app.DB
        app.DB=Path(cls.temp.name)/'test.db'
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
        app.DB=cls.old_db;cls.temp.cleanup()
    def request(self,method,path,body=None,headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        conn.request(method,path,body=body,headers=headers or {})
        response=conn.getresponse();status=response.status;raw=response.read();conn.close()
        return status,raw
    def test_valid_request_and_trail(self):
        status,raw=self.request('POST','/api/evaluate',json.dumps(BASE))
        self.assertEqual(status,200);result=json.loads(raw)
        status,raw=self.request('GET','/api/history')
        self.assertEqual(status,200)
        record=next(r for r in json.loads(raw) if r['id']==result['id'])
        self.assertEqual(record['inputs'],BASE)
        self.assertEqual(record['result']['policy_version'],'demo-am-2.0')
    def test_invalid_json(self):
        self.assertEqual(self.request('POST','/api/evaluate','{')[0],400)
    def test_invalid_does_not_persist(self):
        _,before=self.request('GET','/api/history')
        self.assertEqual(self.request('POST','/api/evaluate',json.dumps(dict(BASE,income=0)))[0],400)
        _,after=self.request('GET','/api/history');self.assertEqual(before,after)
    def test_cross_origin(self):
        self.assertEqual(self.request('POST','/api/evaluate',json.dumps(BASE),{'Origin':'https://example.com'})[0],403)
    def test_path_traversal(self):
        self.assertEqual(self.request('GET','/../app.py')[0],404)
    def test_html(self):
        status,raw=self.request('GET','/');self.assertEqual(status,200);self.assertIn(b'CreditLens',raw)
    def test_body_limit(self):
        self.assertEqual(self.request('POST','/api/evaluate','x'*16385)[0],400)
