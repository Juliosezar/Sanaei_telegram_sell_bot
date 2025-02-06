from binary import BinaryUnits, convert_units
import datetime
import requests
import json

from configs.models import Service
from .models import Server




class ServerApi:
    @classmethod
    def create_session(cls, server_id):
        server_obj = Server.objects.get(id=server_id)
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
            print(e)
            return False

    @classmethod
    def get_list_configs(cls, server_id):
        try:
            server_obj = Server.objects.get(id=server_id)
            session = cls.create_session(server_id)
            if not session:
                return False
            list_configs = session.get(server_obj.url + "panel/api/inbounds/list/", timeout=10)
            if list_configs.status_code != 200:
                session.close()
                return False
            joined_data = {}
            for respons in list_configs.json()["obj"]:
                if respons["id"] == server_obj.inbound_id:
                    for i in respons["clientStats"]:
                        usage = round(convert_units(i["up"] + i["down"], BinaryUnits.BYTE, BinaryUnits.GB)[0], 2)
                        total_usage = int(convert_units(i['total'], BinaryUnits.BYTE, BinaryUnits.GB)[0])
                        total_usage = 0 if total_usage < 0 else total_usage
                        time_expire = i["expiryTime"]
                        joined_data[i["email"]] = {
                            'usage': usage,
                            'usage_limit': total_usage,
                            'expire_time': time_expire,
                        }
                    for i in json.loads(respons["settings"])["clients"]:

                        joined_data[i["email"]]['uuid'] = i["id"]
                        joined_data[i["email"]]['enable'] = i["enable"]
            session.close()
            return joined_data
        except Exception as e:
            print(e)
            return False

    @classmethod
    def create_config(cls, server_id, config_name, uid, enable=True):
        server_obj = Server.objects.get(id=server_id)
        url = server_obj.url + "panel/api/inbounds/addClient"
        setting = {
            'clients': [{
                'id': str(uid), 'alterId': 0, 'email': config_name,
                'limitIp': 0, 'totalGB': 0,
                'expiryTime': 0, 'enable': enable,
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
            print(e)
            return False

    @classmethod
    def renew_config(cls, server_id, config_uuid, config_name, expire_time, total_usage, ip_limit, reset=True):
        server_obj = Server.objects.get(id=server_id)
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
            print(e)
            return False

    @classmethod
    def get_config(cls, server_id, config_name):
        server_obj = Server.objects.get(id=server_id)
        url = server_obj.url + f"panel/api/inbounds/getClientTraffics/{config_name}"
        session = cls.create_session(server_id)
        if not session:
            return False
        respons = session.get(url, timeout=6)
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


    @classmethod
    def delete_config(cls, server_id, config_uuid):
        server_obj = Server.objects.get(id=server_id)
        url = server_obj.url + f"panel/api/inbounds/{server_obj.inbound_id}/delClient/{config_uuid}"
        session = cls.create_session(server_id)
        if not session:
            return False
        response = session.post(url, timeout=6)
        if response.status_code == 200:
            if response.json()['success']:
                session.close()
                return True
        return False

    @classmethod
    def disable_config(cls, server_id, config_uuid, enable):
        session = cls.create_session(server_id)
        server_obj = Server.objects.get(id=server_id)
        service_obj = Service.objects.get(uuid=config_uuid)
        url = server_obj.url + f"panel/api/inbounds/updateClient/{config_uuid}"

        setting = {
            'clients': [{
                'id': str(config_uuid), 'alterId': 0, 'email': service_obj.name,
                'limitIp': 0, 'totalGB': 0,
                'expiryTime': 0, 'enable': enable,
                "tgId": '', 'subId': ''
            }]
        }
        data1 = {
            "id": int(server_obj.inbound_id),
            "settings": json.dumps(setting)
        }
        header = {"Accept": "application/json"}
        try:
            respons = session.post(url, headers=header, json=data1, timeout=6)
            if respons.status_code == 200:
                if respons.json()['success']:
                    return True
            return False
        except Exception as e:
            print(e)
            return False

    @classmethod
    def reset_usage(cls, server_id, config_name):
        try:
            server_obj = Server.objects.get(id=server_id)
            session = cls.create_session(server_id)
            url = server_obj.url + "panel/api/inbounds"
            response = session.post(url + f"/{server_obj.inbound_id}/resetClientTraffic/{config_name}/", headers={},
                                    data={}, timeout=6)
            if response.status_code == 200:
                if response.json()['success']:
                    session.close()
                    return True
                return False
        except Exception as e:
            print(e)
            return False

    @classmethod
    def get_online_users(cls, server_id):
        try:
            server_obj = Server.objects.get(id=server_id)
            session = cls.create_session(server_id)
            url = server_obj.url + "panel/api/inbounds"
            response = session.post(url + f"/onlines", headers={},data={}, timeout=6)
            if response.status_code == 200:
                if response.json()['success']:
                    session.close()
                    return len(response.json()["obj"])
                return False
        except Exception as e:
            print(e)
            return False