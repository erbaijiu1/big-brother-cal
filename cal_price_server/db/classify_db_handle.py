from db.db_models import GoodsClassification
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger

def get_classify_list():
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(GoodsClassification).filter(GoodsClassification.status == 1).all()
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying user conversation summary: {e}")
        raise

# 新增分类
def add_classify(name, description):
    Session = get_session_factory()
    try:
        with Session() as session:
            new_classify = GoodsClassification(name=name, description=description)
            session.add(new_classify)
            session.commit()
            return new_classify
    except Exception as e:
        logger.error(f"Error occurred while adding new classification: {e}")
        raise

# 修改分类
def update_classify(classify_id, name=None, description=None):
    Session = get_session_factory()
    try:
        with Session() as session:
            classify = session.query(GoodsClassification).filter_by(id=classify_id).first()
            if classify:
                if name:
                    classify.name = name
                if description:
                    classify.description = description
                session.commit()
                return classify
            else:
                raise ValueError(f"Classification with id {classify_id} not found")
    except Exception as e:
        logger.error(f"Error occurred while updating classification: {e}")
        raise

# 删除分类
def delete_classify(classify_id):
    Session = get_session_factory()
    try:
        with Session() as session:
            classify = session.query(GoodsClassification).filter_by(id=classify_id).first()
            if classify:
                session.delete(classify)
                session.commit()
                return True
            else:
                raise ValueError(f"Classification with id {classify_id} not found")
    except Exception as e:
        logger.error(f"Error occurred while deleting classification: {e}")
        raise

# 查询单个分类
def get_classify_by_id(classify_id):
    Session = get_session_factory()
    try:
        with Session() as session:
            classify = session.query(GoodsClassification).filter_by(id=classify_id).first()
            if classify:
                return classify
            else:
                raise ValueError(f"Classification with id {classify_id} not found")
    except Exception as e:
        logger.error(f"Error occurred while querying classification: {e}")
        raise