import json

import redis

# 创建 Redis 客户端连接
r = redis.Redis(host='172.18.9.66', port=6081, db=0, password='dahantc.com')

# 要查询的 key
key = 'CHANNEL_CACHE_69187'

# 使用 exists() 方法检查 key 是否存在
if r.exists(key):
    print(f"Key '{key}' exists in Redis.")
    # 使用 get() 方法获取 key 的值
    value = r.get(key)
    result = value.decode('utf-8')
    channel_stats = None
    strs_for_search = ['>Z', '>[']
    str_position = None
    for str in strs_for_search:
        if str in result:
            str_position = result.find(str) + 2
            break
    if str_position is not None:
        try:
            channel_stats = json.loads(value.decode('utf-8')[str_position:])
        except:
            print(f"获取redis中的通道状态失败: {result}")
        else:
            print(channel_stats['active'])
else:
    print(f"Key '{key}' does not exist in Redis.")
