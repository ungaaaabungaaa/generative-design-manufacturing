from http.client import HTTPConnection
import threading
import unittest

from design_lab.server import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=make_server(port=0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def request(self,path,method='GET',host=None):
        connection=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5);self.addCleanup(connection.close)
        connection.request(method,path,headers={'Host':host}if host else{})
        response=connection.getresponse();return response.status,dict(response.getheaders()),response.read()
    def test_public_viewer_report_and_exports_are_served(self):
        for path in ['/', '/model.mjs','/app.mjs','/assets/report.json','/assets/designs/seed-7.dxf']:
            code,headers,body=self.request(path);self.assertEqual(code,200);self.assertTrue(body)
            self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
            self.assertIn("default-src 'self'",headers['Content-Security-Policy'])
    def test_source_paths_directories_and_wrong_host_are_denied(self):
        for path in ['/.git/config','/docs/contract.md','/design_lab/mechanics.py','/assets/designs/','/../README.md']:
            self.assertNotEqual(self.request(path)[0],200)
        self.assertEqual(self.request('/',host='evil.example')[0],403)
    def test_head_and_write_method_boundaries(self):
        code,headers,body=self.request('/assets/report.json','HEAD')
        self.assertEqual(code,200);self.assertEqual(body,b'');self.assertGreater(int(headers['Content-Length']),100)
        self.assertEqual(self.request('/','POST')[0],501)


if __name__=='__main__':unittest.main()
