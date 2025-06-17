from db.db_models import PricingRule
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger

def get_pricing_rules():
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(PricingRule).all()
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying user conversation summary: {e}")
        raise


def get_pricing_rule_by_category_id(category_id):
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(PricingRule).filter(PricingRule.category_id == category_id).all()
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying user conversation summary: {e}")
        raise

