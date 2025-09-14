# area_category_query_handler.py
from db.db_models import SubDistrict, AreaCategory, AreaCategoryMap
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger
from typing import List, Dict, DefaultDict
from collections import defaultdict
from datetime import datetime

# 缓存相关变量
_area_category_cache = None
_area_category_cache_timestamp = None
_CACHE_DURATION = 5  # 缓存5秒过期


def _get_joined_data_from_cache() -> Dict[int, List[Dict]]:
    """
    获取区域分类关联数据，带缓存机制
    返回以category_id为键的映射数据

    Returns:
        Dict[int, List[Dict]]: 以category_id为键，包含area_category.id, area_category.name,
                               SubDistrict.id, SubDistrict.name_cn的列表为值的字典
    """
    global _area_category_cache, _area_category_cache_timestamp
    current_time = datetime.now()

    # 检查缓存是否存在且未过期
    if _area_category_cache is not None and _area_category_cache_timestamp is not None:
        if (current_time - _area_category_cache_timestamp).seconds < _CACHE_DURATION:
            logger.debug("Cache hit for area category joined data")
            return _area_category_cache

    # 缓存未命中或已过期，查询数据库
    Session = get_session_factory()
    try:
        with Session() as session:
            # 分别查询所有数据（全表查询）
            categories = session.query(AreaCategory).all()
            sub_districts = session.query(SubDistrict).all()
            mappings = session.query(AreaCategoryMap).all()

            # 在内存中进行关联处理
            # 创建映射字典以提高查找效率
            category_dict = {cat.id: cat for cat in categories}
            sub_district_dict = {sd.id: sd for sd in sub_districts}

            # 使用defaultdict组织数据，以category_id为键
            result_map = defaultdict(list)

            # 关联三张表的数据
            for mapping in mappings:
                category = category_dict.get(mapping.category_id)
                sub_district = sub_district_dict.get(mapping.sub_district_id)

                # 只有当两个关联对象都存在时才添加到结果中
                if category and sub_district:
                    result_map[category.id].append({
                        'category_id': category.id,
                        'category_name': category.name,
                        'sub_district_id': sub_district.id,
                        'sub_district_name': sub_district.name_cn
                    })

            # 转换为普通字典
            result_dict = dict(result_map)

            # 更新缓存
            _area_category_cache = result_dict
            _area_category_cache_timestamp = current_time

            logger.debug(f"Queried area category joined data, cached for {_CACHE_DURATION} seconds")
            return result_dict
    except Exception as e:
        logger.error(f"Error occurred while querying area category joined data: {e}")
        raise


def get_sub_district_names_by_category_ids(category_ids: List[int] = None) -> List[str]:
    """
    根据分类ID列表获取子区域名称列表

    Args:
        category_ids: 分类ID列表，如果为None则返回所有分类的子区域名称

    Returns:
        List[str]: 子区域名称列表
    """
    try:
        # 获取缓存的数据
        all_data = _get_joined_data_from_cache()

        # 用于存储所有子区域名称，使用set避免重复
        sub_district_names = set()

        # 如果传入了category_ids，则只处理指定的分类
        if category_ids is not None:
            for cat_id in category_ids:
                if cat_id in all_data:
                    for item in all_data[cat_id]:
                        sub_district_names.add(item['sub_district_name'])
        else:
            # 如果没有指定分类ID，则处理所有分类
            for items in all_data.values():
                for item in items:
                    sub_district_names.add(item['sub_district_name'])

        # 转换为列表并返回
        return list(sub_district_names)
    except Exception as e:
        logger.error(f"Error occurred while getting sub district names by category ids: {e}")
        raise


def get_sub_districts_by_category_id(category_id: int) -> List[Dict]:
    """
    根据分类ID获取子区域信息

    Args:
        category_id: 分类ID

    Returns:
        List[Dict]: 子区域信息列表，包含分类ID、分类名称、子区域ID和子区域名称
    """
    try:
        # 获取缓存的数据
        all_data = _get_joined_data_from_cache()

        # 返回指定分类ID的数据
        return all_data.get(category_id, [])
    except Exception as e:
        logger.error(f"Error occurred while getting sub districts by category id: {e}")
        raise


def get_all_category_sub_districts() -> Dict[int, List[Dict]]:
    """
    获取所有分类和子区域的映射关系

    Returns:
        Dict[int, List[Dict]]: 以category_id为键的字典，值为包含分类和子区域信息的字典列表
    """
    try:
        # 获取缓存的数据
        return _get_joined_data_from_cache()
    except Exception as e:
        logger.error(f"Error occurred while getting all category sub districts: {e}")
        raise
