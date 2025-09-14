# sub_district_db_handle.py
from db.db_models import SubDistrict
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger
from typing import List, Optional
from datetime import datetime

# 缓存相关变量
_sub_district_cache = None
_sub_district_cache_timestamp = None
_CACHE_DURATION = 5  # 缓存5秒过期

def _get_all_sub_districts_from_cache() -> List[SubDistrict]:
    """
    获取所有SubDistrict记录，带缓存机制

    Returns:
        List[SubDistrict]: 所有SubDistrict对象列表
    """
    global _sub_district_cache, _sub_district_cache_timestamp
    current_time = datetime.now()

    # 检查缓存是否存在且未过期
    if _sub_district_cache is not None and _sub_district_cache_timestamp is not None:
        if (current_time - _sub_district_cache_timestamp).seconds < _CACHE_DURATION:
            logger.debug("Cache hit for all sub districts")
            return _sub_district_cache

    # 缓存未命中或已过期，查询数据库
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(SubDistrict).all()

            # 更新缓存
            _sub_district_cache = result
            _sub_district_cache_timestamp = current_time

            logger.debug(f"Queried all sub districts, cached for {_CACHE_DURATION} seconds")
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying all sub districts: {e}")
        raise

def get_sub_district_by_id(sub_district_id: int) -> Optional[SubDistrict]:
    """
    根据ID查询SubDistrict记录，从缓存中获取

    Args:
        sub_district_id: 子区域ID

    Returns:
        SubDistrict: SubDistrict对象或None
    """
    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        for sub_district in all_sub_districts:
            if sub_district.id == sub_district_id:
                return sub_district
        return None
    except Exception as e:
        logger.error(f"Error occurred while querying sub district by id: {e}")
        raise

def get_sub_district_by_name(name_cn: str) -> Optional[SubDistrict]:
    """
    根据中文名称查询SubDistrict记录，从缓存中获取

    Args:
        name_cn: 中文名称

    Returns:
        SubDistrict: SubDistrict对象或None
    """
    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        for sub_district in all_sub_districts:
            if sub_district.name_cn == name_cn:
                return sub_district
        return None
    except Exception as e:
        logger.error(f"Error occurred while querying sub district by name: {e}")
        raise

def get_all_sub_districts() -> List[SubDistrict]:
    """
    查询所有SubDistrict记录，从缓存中获取

    Returns:
        List[SubDistrict]: SubDistrict对象列表
    """
    try:
        return _get_all_sub_districts_from_cache()
    except Exception as e:
        logger.error(f"Error occurred while querying all sub districts: {e}")
        raise


def get_sub_district_names_by_ids(sub_district_ids: List[int]) -> List[str]:
    """
    通过ID列表查询SubDistrict记录的名称，从缓存中获取

    Args:
        sub_district_ids: 子区域ID列表

    Returns:
        List[str]: 子区域中文名称列表
    """
    if not sub_district_ids:
        return []

    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        id_set = set(sub_district_ids)
        result = [sub_district.name_cn for sub_district in all_sub_districts if sub_district.id in id_set]
        return result
    except Exception as e:
        logger.error(f"Error occurred while querying sub district names by ids: {e}")
        raise

def get_sub_districts_by_district_id(district_id: int) -> List[SubDistrict]:
    """
    根据district_id查询SubDistrict记录，从缓存中获取

    Args:
        district_id: 区域ID

    Returns:
        List[SubDistrict]: SubDistrict对象列表
    """
    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        result = [sub_district for sub_district in all_sub_districts if sub_district.district_id == district_id]
        return result
    except Exception as e:
        logger.error(f"Error occurred while querying sub districts by district id: {e}")
        raise

def get_sub_districts_by_district_ids(district_ids: List[int]) -> List[SubDistrict]:
    """
    根据district_id列表查询SubDistrict记录，从缓存中获取

    Args:
        district_ids: 区域ID列表

    Returns:
        List[SubDistrict]: SubDistrict对象列表
    """
    if not district_ids:
        return []

    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        district_id_set = set(district_ids)
        result = [sub_district for sub_district in all_sub_districts if sub_district.district_id in district_id_set]
        return result
    except Exception as e:
        logger.error(f"Error occurred while querying sub districts by district ids: {e}")
        raise

def get_remote_sub_districts() -> List[SubDistrict]:
    """
    获取所有偏远地区子区域，从缓存中获取

    Returns:
        List[SubDistrict]: 偏远地区SubDistrict对象列表
    """
    try:
        all_sub_districts = _get_all_sub_districts_from_cache()
        result = [sub_district for sub_district in all_sub_districts if sub_district.is_remote]
        return result
    except Exception as e:
        logger.error(f"Error occurred while querying remote sub districts: {e}")
        raise
