import re
import time
import json
import sqlite3
import subprocess
import urllib.request
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from DrissionPage import ChromiumPage

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mydata.db')
CHROME_PATH = '/data/data/com.termux/files/usr/bin/chromium-browser'
PROFILE_PATH = os.path.expanduser('~/pdd_profile')
ORDER_URL = 'https://mobile.pinduoduo.com/orders.html?type=0&combine_orders=1&main_orders=1'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS tracking_numbers (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT UNIQUE, create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def save_to_db(numbers):
    if not numbers: return
    conn = sqlite3.connect(DB_PATH)
    for num in numbers:
        conn.execute("INSERT OR IGNORE INTO tracking_numbers (number) VALUES (?)", (num,))
    conn.commit()
    conn.close()

def get_all_from_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT number FROM tracking_numbers ORDER BY id DESC").fetchall()
        return [{"number": row[0], "product_name": None} for row in rows]
    except:
        return []
    finally:
        conn.close()

def check_and_start_environment():
    try:
        urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=2)
        return
    except:
        pass
    subprocess.Popen("pkill -9 -f termux-x11; pkill -9 -f chromium", shell=True)
    time.sleep(2)
    subprocess.Popen("nohup termux-x11 :0 > /dev/null 2>&1 &", shell=True)
    time.sleep(2)
    subprocess.Popen("(am start -n com.termux.x11/.MainActivity > /dev/null 2>&1) || (termux-open --view 'com.termux.x11' > /dev/null 2>&1)", shell=True)
    time.sleep(1)
    cmd = f"export DISPLAY=:0; nohup {CHROME_PATH} --no-sandbox --no-first-run --no-default-browser-check --remote-debugging-port=9222 --user-data-dir={PROFILE_PATH} --user-agent='Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36' 'https://mobile.pinduoduo.com' > /dev/null 2>&1 &"
    subprocess.Popen(cmd, shell=True)
    time.sleep(8)

def is_valid_tracking_number(num):
    num = str(num).strip().upper()
    if re.match(r'^(SF|JD|JT|YT|ZT|STO|YD)\d{10,20}$', num): return True
    if num.isdigit():
        if num.startswith(('179', '202', '100', '79', '98', '93', '82', '99', '83', '67')): return False
        if re.match(r'^77\d{13}$', num): return True
        if re.match(r'^(78|73|61)\d{8,10}$', num): return True
        if re.match(r'^[68]\d{11,12}$', num): return True
    return False

init_db()

class PDDHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/get_orders':
            try:
                check_and_start_environment()
                page = ChromiumPage(addr_or_opts='127.0.0.1:9222')
                
                print("🚀 跳转订单列表...")
                page.get(ORDER_URL)
                time.sleep(6)
                
                print("📜 自动滑动加载...")
                for i in range(20):
                    page.run_js("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.5)
                    
                html = page.html
                
                order_sns = set(re.findall(r'"order_sn"\s*:\s*"([^"]+)"', html))
                if not order_sns:
                    order_sns = set(re.findall(r'order_sn=([0-9\-]+)', html))
                
                print(f"✅ 提取到 {len(order_sns)} 个订单号，开始后台轰炸详情页！")
                latest_list = set()
                
                for i, sn in enumerate(list(order_sns)[:60]):
                    detail_url = f"https://mobile.pinduoduo.com/goods_express.html?order_sn={sn}"
                    js_fetch = f"""
                    return fetch('{detail_url}', {{ headers: {{'Accept': 'text/html'}} }}).then(res => res.text()).then(text => text).catch(e => "FETCH_ERROR");
                    """
                    res_html = page.run_js(js_fetch)
                    
                    if res_html and "FETCH_ERROR" not in res_html:
                        raw_nums = re.findall(r'[A-Za-z0-9]{10,20}', res_html)
                        for n in raw_nums:
                            if is_valid_tracking_number(n):
                                latest_list.add(n)
                                
                    time.sleep(0.8)

                print(f"\n🎉 轰炸完毕！提取到 {len(latest_list)} 个纯净单号！")

                if latest_list: 
                    save_to_db(list(latest_list))
                    
                all_data = get_all_from_db()
                response_data = {"status": "success", "count": len(all_data), "tracking_numbers": [item["number"] for item in all_data]}
                    
            except Exception as e:
                response_data = {"status": "error", "message": str(e)}
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', 8000), PDDHandler)
    print("✅ 纯净版服务已启动，监听 8000 端口")
    server.serve_forever()
