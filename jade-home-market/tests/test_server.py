import importlib.util
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
import json

spec=importlib.util.spec_from_file_location('jade_server',Path(__file__).resolve().parents[1]/'server.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)

def xml(items,code='000',total=None):
    return f'<response><header><resultCode>{code}</resultCode></header><body><totalCount>{len(items) if total is None else total}</totalCount><items>{"".join(items)}</items></body></response>'.encode()

def item(**values):
    record=dict(aptNm='테스트아파트',excluUseAr='84.9000',dealAmount='120,000',dealYear='2026',dealMonth='9',dealDay='2',floor='12',umdNm='잠실동',jibun='1',sggCd='11710',cdealType='',cdealDay='')
    record.update(values)
    return '<item>'+''.join(f'<{k}>{v}</{k}>' for k,v in record.items())+'</item>'

class AdapterTests(unittest.TestCase):
    def setUp(self): server.CACHE.clear()

    def test_parse_amount_area_dates_and_cancelled(self):
        total,trades=server.parse_xml(xml([item(),item(cdealType='O'),item(cdealDay='20261001')]))
        self.assertEqual(total,3);self.assertEqual(len(trades),1)
        self.assertEqual(trades[0]['amount'],120000)
        self.assertEqual(trades[0]['area'],'84.9')
        self.assertEqual(trades[0]['date'],'2026-09-02')

    def test_no_silent_bad_records_or_auth_success(self):
        for payload in [xml([item(dealAmount='bad')]), xml([],code='30'), b'not XML']:
            with self.assertRaises(server.UpstreamError):server.parse_xml(payload)

    def test_pagination_and_cache(self):
        with patch.object(server,'fetch_page',side_effect=[(1001,[{'date':'2026-09-02'}]*1000),(1001,[{'date':'2026-09-03'}])]) as fetch:
            self.assertEqual(len(server.load_month('11710','202609')),1001)
            self.assertEqual(len(server.load_month('11710','202609')),1001)
            self.assertEqual(fetch.call_count,2)

    def test_no_partial_cache_after_failure(self):
        with patch.object(server,'fetch_page',side_effect=[(1001,[]),server.UpstreamError('failure')]):
            with self.assertRaises(server.UpstreamError):server.load_month('11710','202609')
        self.assertFalse(server.CACHE)
        self.assertEqual(server.months_before('202601',3),['202511','202512','202601'])

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from functools import partial
        cls.httpd=server.ThreadingHTTPServer(('127.0.0.1',0),partial(server.Handler,directory=str(server.ROOT)))
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.httpd.server_port}'

    @classmethod
    def tearDownClass(cls):cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join()

    def test_valid_api_and_validation(self):
        with patch.object(server,'load_month',return_value=[]):
            with urllib.request.urlopen(self.base+'/api/trades?district=11710&month=202609&months=3') as response:
                data=json.load(response)
            self.assertEqual(data['months'],['202607','202608','202609'])
        for path in ['/api/trades?district=99999&month=202609','/api/trades?district=11710&month=202613','/api/trades?district=11710&month=202609&months=999']:
            with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(self.base+path)
            self.assertEqual(error.exception.code,400)

    def test_private_files_cannot_be_served(self):
        for path in ['/server.py','/.env','/tests/test_server.py','/../bot.py','/%2e%2e/bot.py','/']:
            if path=='/':
                with urllib.request.urlopen(self.base+path) as r:self.assertEqual(r.status,200)
            else:
                with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(self.base+path)
                self.assertEqual(error.exception.code,404)

if __name__=='__main__':unittest.main()
