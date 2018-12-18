import os
import logging
import logging.config as root_config

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

crawler_log = os.path.join(log_dir, "crawler.log")
parse_log = os.path.join(log_dir, "parse.log")
netio_log = os.path.join(log_dir, "netio.log")

logger_config = {
    'version': 1,
    'formatters': {
        'detail': {
            'format': '[%(asctime)s]-%(name)s-%(levelname)s-%(filename)s {%(module)s.%(funcName)s:%(lineno)d} - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detail'
        },
        'crawler_log': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 2,
            'backupCount': 5,
            'filename': crawler_log,
            'level': 'INFO',
            'formatter': 'detail',
            'encoding': 'utf-8',
        },
	    'parse_log': {
		    'class': 'logging.handlers.RotatingFileHandler',
		    'maxBytes': 1024 * 1024 * 5,
		    'backupCount': 10,
		    'filename': parse_log,
		    'level': 'INFO',
		    'formatter': 'detail',
		    'encoding': 'utf-8',
	    },
	    'netio_log': {
		    'class': 'logging.handlers.RotatingFileHandler',
		    'maxBytes': 1024 * 1024 * 5,
		    'backupCount': 10,
		    'filename': netio_log,
		    'level': 'INFO',
		    'formatter': 'detail',
		    'encoding': 'utf-8',
	    }
    },
    'loggers': {
        'crawler': {
            'handlers': ['console', 'crawler_log'],
            'level': 'INFO',
        },
        'parser': {
            'handlers': ['console', 'parse_log'],
            'level': 'INFO',
        },
	    'netio': {
		    'handlers': ['console', 'netio_log'],
		    'level': 'INFO',
	    },
    }
}

root_config.dictConfig(logger_config)

crawler = logging.getLogger('crawler')
parser = logging.getLogger('parser')
netio = logging.getLogger('netio')
