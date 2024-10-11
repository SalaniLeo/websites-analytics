from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import load_config
from connect import connect
import os
from cryptography.fernet import Fernet
import ipinfo
from key import *
import time
from pprint import pprint
from pathlib import Path
env_path = Path('endpoints.env')

load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)
config = load_config()
handler = ipinfo.getHandler(os.getenv('IPINFO_TOKEN'))

valid_key = os.environ.get("API_KEY_UNCRYPTED")
key_string = os.getenv("ENCRYPTION_KEY")
key = generate_key(key_string)

def verify_api_key():
    api_key = request.headers.get('x-api-key')
    if decrypt_string(key, api_key) != valid_key or not api_key:
        return jsonify({"error": "Unauthorized: Invalid API key"}), 401

@app.before_request
def before_request_func():
    if request.path in PROTECTED_ENDPOINTS:
        return verify_api_key()

@app.route(os.environ.get('ENTERED_URL'), methods=['POST'])
def user_entered():
    data = request.json
    response = Database.check_if_exist(data.get('ip'))
    check_if_exists = response

    if check_if_exists['status'] == 200 and check_if_exists['exists'] == False:
        Database.upload_new_user(data)
    elif check_if_exists['exists'] == True:
        Database.add_new_visit(data)
    return check_if_exists

@app.route('/api/alive', methods=['POST'])
def is_alive():
    return {
        'response': True,
        'status': 200
    }

class Database():
    @staticmethod
    def check_if_exist(ip):
        try:
            conn = connect(config)
            cur = conn.cursor()
            cur.execute("SELECT * FROM analytics WHERE ip = %s", (ip,))
            row = cur.fetchone()
            response_data = {
                "exists": True if row else False,
                "status": 200
            }
        except Exception as e:
            response_data = {
                "response": False,
                "status": 500,
                "error": str(e)
            }
        finally:
            cur.close()
            conn.close()
        return response_data

    @staticmethod
    def upload_new_user(data):
        try:
            conn = connect(config)
            cur = conn.cursor()
            ip_data = handler.getDetails()
            cur.execute("INSERT INTO analytics (website, ip, country, region, provider, os, browser, visits, time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                        (data.get('website'), data.get('ip'), ip_data.country, ip_data.region, ip_data.org, data.get('os'), data.get('browser'), 1, time.time()))
            conn.commit()
        except Exception as e:
            print(e)

    def add_new_visit(data):
        sql = """ UPDATE analytics
                SET visits = %s
                WHERE ip = %s"""
        select_sql = "SELECT * FROM analytics WHERE ip = %s"

        try:
            conn = connect(config)
            cur = conn.cursor()
            cur.execute(select_sql, (data.get('ip'),))
            row = cur.fetchone()

            if row is not None:
                new_visits = row[7] + 1
                cur.execute(sql, (new_visits, data.get('ip')))
                conn.commit()
                print(row[:7] + (new_visits,) + row[8:])
            else:
                print("No record found for IP:", data.get('ip'))

        except Exception as e:
            print("Error:", e)

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)