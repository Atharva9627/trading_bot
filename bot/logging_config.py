import logging

def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("TradingBot")

logger = setup_logging()