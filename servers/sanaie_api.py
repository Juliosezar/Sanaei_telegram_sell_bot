from binary import BinaryUnits, convert_units
import datetime
import requests
import json
from .models import Server




class ServerApi:
    @classmethod
    def create_session(cls, server_id):
        server_obj = Server.objects.get(ID=server_id)
        server_url = server_obj.url
        incound_id = server_obj.inbound_id
        login_payload = {"username": server_obj.username, "password": server_obj.password}
        login_url = server_url + "login/"
        header = {"Accept": "application/json"}
        try:
            session = requests.Session()
            login_response = session.post(login_url, headers=header, json=login_payload, timeout=15)
            if login_response.status_code == 200:
                if login_response.json()["success"]:
                    return session
            else:
                session.close()
                return False
        except Exception as e:
            return False

    @classmethod
    def get_list_configs(cls, server_id):
        try:
            server_obj = Server.objects.get(ID=server_id)
            session = cls.create_session(server_id)
            if not session:
                return False
            list_configs = session.get(server_obj.url + "panel/api/inbounds/list/", timeout=15)
            if list_configs.status_code != 200:
                session.close()
                return False
            joined_data = {}
            for respons in list_configs.json()["obj"]:
                if respons["id"] == server_obj.inbound_id:
                    for i in respons["clientStats"]:
                        expired = False
                        started = True
                        presentDate = datetime.datetime.now()
                        unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
                        time_expire = i["expiryTime"]
                        if time_expire > 0:
                            time_expire = (time_expire - unix_timestamp) / 86400000
                            if time_expire < 0:
                                expired = True

                        elif time_expire == 0:
                            if i['down'] + i["up"] == 0:
                                started = False
                        else:
                            time_expire = abs(int(time_expire / 86400000))
                            started = False

                        usage = round(convert_units(i["up"] + i["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                        started = True if usage > 0 else False
                        total_usage = int(convert_units(i['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                        total_usage = 0 if total_usage < 0 else total_usage
                        joined_data[i["email"]] = {
                            'ended': i["enable"],
                            'usage': usage,
                            'started': started,
                            'expire_time': time_expire,
                            'usage_limit': total_usage,
                            # 'inbound_id': i["inboundId"],
                            "expired": expired
                        }
                    for i in json.loads(respons["settings"])["clients"]:
                        joined_data[i["email"]]['uuid'] = i["id"]
                        joined_data[i["email"]]['ip_limit'] = i["limitIp"]
                        joined_data[i["email"]]['enable'] = i["enable"]
            session.close()
            return joined_data
        except Exception as e:
            return False

    @classmethod
    def create_config(cls, server_id, config_name, uid, usage_limit_GB, expire_DAY, ip_limit, enable):
        server_obj = Server.objects.get(ID=server_id)
        url = server_obj.url + "panel/api/inbounds/addClient"
        expire_time = int(expire_DAY) * 24 * 60 * 60 * 1000 * -1
        usage_limit = int(convert_units(usage_limit_GB, BinaryUnits.GB, BinaryUnits.BYTE)[0])
        setting = {
            'clients': [{
                'id': str(uid), 'alterId': 0, 'email': config_name,
                'limitIp': ip_limit, 'totalGB': usage_limit,
                'expiryTime': expire_time, 'enable': enable,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        try:
            session = cls.create_session(server_id)
            if not session:
                return False
            respons = session.post(url, headers=header, json=data1, timeout=6)
            if respons.status_code == 200:
                if respons.json()['success']:
                    session.close()
                    return True
            session.close()
            return False
        except Exception as e:
            return False

    @classmethod
    def renew_config(cls, server_id, config_uuid, config_name, expire_time, total_usage, ip_limit, reset=True):
        server_obj = Server.objects.get(ID=server_id)
        url = server_obj.url + "panel/api/inbounds"
        expire_time = (int(expire_time) * 24 * 60 * 60 * 1000 * -1)
        total_usage = (int(convert_units(int(total_usage), BinaryUnits.GB, BinaryUnits.BYTE)[0]))
        setting = {
            'clients': [{
                'id': str(config_uuid), 'alterId': 0, 'email': config_name,
                'limitIp': ip_limit, 'totalGB': total_usage,
                'expiryTime': expire_time, 'enable': True,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}

        try:
            session = cls.create_session(server_id)
            if not session:
                return False
            respons = session.post(url + f"/updateClient/{str(config_uuid)}/", headers=header, json=data1, timeout=6)
            if reset:
                respons2 = session.post(url + f"/{server_obj.inbound_id}/resetClientTraffic/{config_name}/", headers={},
                                        data={}, timeout=6)
                if not respons2.status_code == 200:
                    session.close()
                    return False
            if respons.status_code == 200:
                if respons.json()['success']:
                    session.close()
                    return True
            session.close()
            return False
        except Exception as e:
            return False

    @classmethod
    def get_config(cls, server_id, config_name):
        server_obj = Server.objects.get(ID=server_id)
        url = server_obj.url + f"panel/api/inbounds/getClientTraffics/{config_name}"
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.get(url)
        if respons.status_code == 200:
            if respons.json()['success']:
                obj = respons.json()["obj"]
                if obj:
                    expired = False
                    started = True
                    presentDate = datetime.datetime.now()
                    unix_timestamp = datetime.datetime.timestamp(presentDate) * 1000
                    time_expire = obj["expiryTime"]
                    if time_expire > 0:
                        time_expire = (time_expire - unix_timestamp) / 86400000
                        if time_expire < 0:
                            expired = True
                    elif time_expire == 0:
                        if obj['down'] + obj["up"] == 0:
                            started = False
                    else:
                        time_expire = abs(int(time_expire / 86400000))
                        started = False
                    usage = round(convert_units(obj["up"] + obj["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                    started = True if usage > 0 else False
                    total_usage = int(convert_units(obj['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                    total_usage = 0 if total_usage < 0 else total_usage
                    session.close()
                    return {
                        'ended': obj["enable"],
                        'time_expire': time_expire,
                        'usage': usage,
                        'usage_limit': total_usage,
                        'started': started,
                        'exp_time_sta': expired,
                        'inbound_id': int(obj["inboundId"]),
                        "expired": expired
                    }
        session.close()
        return False
