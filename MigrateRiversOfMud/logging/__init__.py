import os
import logging


def setup_logger(object_name, log_dir):
    """
    Sets up a logger for the class.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(f'{object_name}')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(os.path.join(log_dir, object_name+'.log'))
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger
