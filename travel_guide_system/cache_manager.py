"""
缓存管理模块 - 避免重复搜索相同内容
"""

import json
import os
from datetime import datetime, timedelta
from hashlib import md5

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")


def get_cache_key(origin: str, destination: str, data_type: str) -> str:
    """生成缓存键"""
    key = f"{origin}_{destination}_{data_type}"
    return md5(key.encode()).hexdigest()


def get_cache(origin: str, destination: str, data_type: str) -> dict:
    """
    获取缓存数据
    
    Args:
        origin: 出发地
        destination: 目的地
        data_type: 数据类型 (web/reviews/analysis)
    
    Returns:
        dict: 缓存数据，如果不存在或过期返回 None
    """
    cache_key = get_cache_key(origin, destination, data_type)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        
        # 检查是否过期（24小时）
        cached_time = datetime.fromisoformat(cache_data.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=24):
            os.remove(cache_file)
            return None
        
        return cache_data.get("data")
    except Exception:
        return None


def set_cache(origin: str, destination: str, data_type: str, data: dict):
    """
    设置缓存数据
    
    Args:
        origin: 出发地
        destination: 目的地
        data_type: 数据类型
        data: 要缓存的数据
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    
    cache_key = get_cache_key(origin, destination, data_type)
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    cache_data = {
        "origin": origin,
        "destination": destination,
        "data_type": data_type,
        "cached_at": datetime.now().isoformat(),
        "data": data,
    }
    
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"缓存写入失败: {e}")


def clear_cache():
    """清除所有缓存"""
    if os.path.exists(CACHE_DIR):
        for file in os.listdir(CACHE_DIR):
            if file.endswith(".json"):
                os.remove(os.path.join(CACHE_DIR, file))
