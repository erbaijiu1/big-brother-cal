from db.db_models import ChannelConfig
from db.sqlalchemy_define import get_session_factory
from utils.logger_config import logger


def get_channel_config_by_channel(channel: str) -> ChannelConfig:
    Session = get_session_factory()
    try:
        with Session() as session:
            result = session.query(ChannelConfig).filter(ChannelConfig.channel_code== channel).first()
            return result
    except Exception as e:
        logger.error(f"Error occurred while querying user conversation summary: {e}")
        raise
