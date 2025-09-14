from db.db_models import District
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger
from typing import List, Optional
from datetime import datetime
import functools

# 缓存相关变量
_district_cache = None
_district_cache_timestamp = None
_CACHE_DURATION = 5  # 缓存5秒过期

def _get_all_districts_from_cache() -> List[District]:
    """
    获取所有District记录，带缓存机制

    Returns:
        List[District]: 所有District对象列表
    """
    global _district_cache, _district_cache_timestamp
    current_time = datetime.now()

    # 检查缓存是否存在且未过期
    if _district_cache is not None and _district_cache_timestamp is not None:
        if (current_time - _district_cache_timestamp).seconds < _CACHE_DURATION:
            logger.debug("Cache hit for all districts")
            return _district_cache

    # 缓存未命中或已过期，查询数据库
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(District).all()

            # 更新缓存
            _district_cache = result
            _district_cache_timestamp = current_time

            logger.debug(f"Queried all districts, cached for {_CACHE_DURATION} seconds")
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying all districts: {e}")
        raise

def get_district_by_id(district_id: int) -> Optional[District]:
    """
    根据ID查询District记录，从缓存中获取

    Args:
        district_id: 区域ID

    Returns:
        District: District对象或None
    """
    try:
        all_districts = _get_all_districts_from_cache()
        for district in all_districts:
            if district.id == district_id:
                return district
        return None
    except Exception as e:
        logger.error(f"Error occurred while querying district by id: {e}")
        raise

def get_district_by_name(name_cn: str) -> Optional[District]:
    """
    根据中文名称查询District记录，从缓存中获取

    Args:
        name_cn: 中文名称

    Returns:
        District: District对象或None
    """
    try:
        all_districts = _get_all_districts_from_cache()
        for district in all_districts:
            if district.name_cn == name_cn:
                return district
        return None
    except Exception as e:
        logger.error(f"Error occurred while querying district by name: {e}")
        raise

def get_all_districts() -> List[District]:
    """
    查询所有District记录，从缓存中获取

    Returns:
        List[District]: District对象列表
    """
    try:
        return _get_all_districts_from_cache()
    except Exception as e:
        logger.error(f"Error occurred while querying all districts: {e}")
        raise

def get_districts_by_ids(district_ids: List[int]) -> List[District]:
    """
    通过ID列表查询District记录，从缓存中获取

    Args:
        district_ids: 区域ID列表

    Returns:
        List[District]: District对象列表
    """
    if not district_ids:
        return []

    try:
        all_districts = _get_all_districts_from_cache()
        id_set = set(district_ids)
        result = [district for district in all_districts if district.id in id_set]
        return result
    except Exception as e:
        logger.error(f"Error occurred while querying districts by ids: {e}")
        raise

def get_district_list() -> List[District]:
    """
    获取所有District列表，从缓存中获取
    """
    try:
        return _get_all_districts_from_cache()
    except Exception as e:
        logger.error(f"Error occurred while querying district list: {e}")
        raise
