"""Same-origin static site and MOLIT apartment trade adapter (Python 3.12+)."""
import argparse
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
ENDPOINT = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade'
# Explicit administrative codes: no arbitrary upstream URLs accepted.
DISTRICTS = dict(zip(
    '11110 11140 11170 11200 11215 11230 11260 11290 11305 11320 11350 11380 11410 11440 11470 11500 11530 11545 11560 11590 11620 11650 11680 11710 11740'.split(),
    ['서울 '+n for n in '종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split()]))
DISTRICTS.update({'41111':'경기 수원시 장안구','41113':'경기 수원시 권선구','41115':'경기 수원시 팔달구','41117':'경기 수원시 영통구','41131':'경기 성남시 수정구','41133':'경기 성남시 중원구','41135':'경기 성남시 분당구','41150':'경기 의정부시','41171':'경기 안양시 만안구','41173':'경기 안양시 동안구','41192':'경기 부천시 원미구','41194':'경기 부천시 소사구','41196':'경기 부천시 오정구','41210':'경기 광명시','41220':'경기 평택시','41250':'경기 동두천시','41271':'경기 안산시 상록구','41273':'경기 안산시 단원구','41281':'경기 고양시 덕양구','41285':'경기 고양시 일산동구','41287':'경기 고양시 일산서구','41290':'경기 과천시','41310':'경기 구리시','41360':'경기 남양주시','41370':'경기 오산시','41390':'경기 시흥시','41410':'경기 군포시','41430':'경기 의왕시','41450':'경기 하남시','41461':'경기 용인시 처인구','41463':'경기 용인시 기흥구','41465':'경기 용인시 수지구','41480':'경기 파주시','41500':'경기 이천시','41550':'경기 안성시','41570':'경기 김포시','41590':'경기 화성시 (행정구역 개편 전 코드)','41610':'경기 광주시','41630':'경기 양주시','41650':'경기 포천시','41670':'경기 여주시','41800':'경기 연천군','41820':'경기 가평군','41830':'경기 양평군','28110':'인천 중구','28140':'인천 동구','28177':'인천 미추홀구','28185':'인천 연수구','28200':'인천 남동구','28237':'인천 부평구','28245':'인천 계양구','28260':'인천 서구','28710':'인천 강화군','28720':'인천 옹진군'})
CACHE = {}
LOCK = threading.Lock()

class UpstreamError(Exception):
    pass

def parse_xml(payload):
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        raise UpstreamError('국토부 응답이 XML 형식이 아닙니다.') from None
    code = root.findtext('.//resultCode')
    if code not in ('000', '00', '0'):
        reason = root.findtext('.//returnReasonCode') or code or 'unknown'
        reason = reason if re.fullmatch(r'[A-Za-z0-9_]{1,30}', reason) else 'unknown'
        raise UpstreamError(f'국토부 API 오류 코드 {reason}. 인증키·활용 승인·요청 조건을 확인하세요.')
    try:
        total = int(root.findtext('.//totalCount'))
    except (ValueError, TypeError):
        raise UpstreamError('국토부 전체 거래 건수를 해석하지 못했습니다.') from None
    trades = []
    for item in root.findall('.//item'):
        field = lambda name: (item.findtext(name) or '').strip()
        if field('cdealDay') or field('cdealType') in ('O', 'Y', '1'):
            continue
        try:
            amount = int(field('dealAmount').replace(',', '').replace(' ', ''))
            area = format(Decimal(field('excluUseAr')).normalize(), 'f')
            day = date(int(field('dealYear')), int(field('dealMonth')), int(field('dealDay'))).isoformat()
            if amount <= 0 or Decimal(area) <= 0 or not field('aptNm'):
                raise ValueError()
        except (ValueError, InvalidOperation):
            raise UpstreamError('거래 필수 항목을 해석하지 못했습니다. 불완전한 집계는 표시하지 않습니다.') from None
        trades.append(dict(name=field('aptNm'), area=area, date=day, amount=amount,
                           floor=field('floor'), dong=field('umdNm'), jibun=field('jibun'),
                           district=field('sggCd')))
    return total, trades

def fetch_page(district, month, page):
    key = os.getenv('DATA_GO_KR_SERVICE_KEY', '').strip()
    if not key:
        raise UpstreamError('서버에 DATA_GO_KR_SERVICE_KEY가 등록되지 않았습니다.')
    query = urllib.parse.urlencode(dict(LAWD_CD=district, DEAL_YMD=month, pageNo=page, numOfRows=1000))
    # Keep proxy placeholders literal; percent-encode real decoded portal keys once.
    encoded = key if key.startswith(('secret_', 'proxy_', 'codex_')) else urllib.parse.quote(urllib.parse.unquote(key), safe='')
    request = urllib.request.Request(ENDPOINT+'?'+query+'&serviceKey='+encoded)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return parse_xml(response.read(16 * 1024 * 1024))
    except urllib.error.HTTPError as error:
        # Never return exception URLs, headers, or credential-bearing request details.
        try:
            return parse_xml(error.read(16384))
        except UpstreamError as parsed:
            raise UpstreamError(f'국토부 HTTP {error.code}: {parsed}') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise UpstreamError('국토부 API에 연결하지 못했습니다. 네트워크와 잠시 후 재시도를 확인하세요.') from None

def load_month(district, month):
    cache_key = (district, month)
    with LOCK:
        cached = CACHE.get(cache_key)
        if cached and time.monotonic() - cached[0] < 900:
            return cached[1]
    total, trades = fetch_page(district, month, 1)
    pages = (total + 999) // 1000
    if pages > 20:
        raise UpstreamError('월별 조회 한도를 초과했습니다. 전체 조회 없이 부분 집계하지 않습니다.')
    for page in range(2, pages + 1):
        next_total, rows = fetch_page(district, month, page)
        if next_total != total:
            raise UpstreamError('조회 중 거래 건수가 변경됐습니다. 잠시 후 다시 조회하세요.')
        trades.extend(rows)
    with LOCK:
        if len(CACHE) >= 200:
            CACHE.pop(next(iter(CACHE)))
        CACHE[cache_key] = (time.monotonic(), trades)
    return trades

def months_before(month, count):
    year, number = int(month[:4]), int(month[4:])
    return [f'{(year*12+number-1-i)//12:04d}{(year*12+number-1-i)%12+1:02d}' for i in range(count)][::-1]

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Request paths may contain sensitive data; do not log them.

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == '/api/config':
            today = date.today()
            month = months_before(today.strftime('%Y%m'), 2)[0]
            return self.send_json(200, dict(districts=DISTRICTS, defaultMonth=month))
        if parsed.path == '/api/trades':
            args = urllib.parse.parse_qs(parsed.query)
            district = args.get('district', ['11710'])[0]
            month = args.get('month', [''])[0]
            try:
                count = int(args.get('months', ['3'])[0])
                valid_month = re.fullmatch(r'\d{6}', month) and 1 <= int(month[4:]) <= 12 and '200601' <= month <= date.today().strftime('%Y%m')
                if district not in DISTRICTS or not valid_month or not 2 <= count <= 12 or months_before(month, count)[0] < '200601':
                    raise ValueError()
            except ValueError:
                return self.send_json(400, dict(error='지원하는 시·구와 2006년 이후 조회월, 2~12개월을 선택하세요.'))
            try:
                months = months_before(month, count)
                trades = [dict(t, district=district) for m in months for t in load_month(district, m)]
                return self.send_json(200, dict(source='국토교통부 아파트 매매 실거래가', district=DISTRICTS[district], months=months, trades=trades, fetchedAt=datetime.now().astimezone().isoformat()))
            except UpstreamError as error:
                return self.send_json(502, dict(error=str(error)))
        # Explicit public-file allowlist: never expose .env, source, .git or tests.
        if parsed.path not in ('/', '/index.html', '/style.css', '/app.js', '/live.js', '/data.js', '/desktop.png', '/mobile.png', '/mobile-chart.png'):
            return self.send_json(404, dict(error='Not found'))
        super().do_GET()

    def do_HEAD(self):
        if urllib.parse.urlsplit(self.path).path not in ('/', '/index.html', '/style.css', '/app.js', '/live.js', '/data.js', '/desktop.png', '/mobile.png', '/mobile-chart.png'):
            return self.send_json(404, dict(error='Not found'))
        super().do_HEAD()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=4173)
    options = parser.parse_args()
    httpd = ThreadingHTTPServer((options.host, options.port), partial(Handler, directory=str(ROOT)))
    print(f'Jade server listening on port {options.port}', flush=True)
    httpd.serve_forever()
