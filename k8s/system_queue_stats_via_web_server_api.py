import requests
import json


def get_system_queue_stats():
    api_url = 'http://172.18.9.69:8081/appQueue/readPages?page=1&limit=10&serverName=&ip=&port'
    headers = {
        "TOKEN": "eyJraWQiOiI4YTA4ZmJiMWNiYTA0ZGMwOTVmMjUyOWM3NDVmN2NjMSIsInR5cCI6IkpXVCIsImFsZyI6IkhTMjU2In0.eyJzdWIiOiIyYzkyODljNThhMDMyMTllMDE4YTAzMjVhNTdmMDAwNyIsImlzcyI6IkVNQTgtV0VCIiwiaWF0IjoxNzEyNjI0NjA5fQ.WFmoLPmlss0Up3a7Xznddj5QXjotfmd8u9NtJZKAaiQ"
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        system_queue_stats = json.loads(response.text)['data']['data']
        print(f"系统队列状态: {system_queue_stats}")
    else:
        print(f"获取系统队列状态失败: \n{response.text}")


if __name__ == "__main__":
    get_system_queue_stats()
