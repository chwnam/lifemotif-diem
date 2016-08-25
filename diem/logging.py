import logging
import logging.config

from sys import stdout


log_format = '%(asctime)s [%(levelname)s] %(name)s (%(lineno)s): %(message)s'

log_config = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': log_format,
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)-8s %(message)s',
        }
    },
    'filters': {
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
            'filters': [],
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': None,  # Set this!
            'formatter': 'verbose',
            'filters': [],
            'level': 'DEBUG',
            'maxBytes': 512 * 1024,  # 512KiB
            'backupCount': 10,  #
            'encoding': 'utf-8',
        },
        'null': {
            'class': 'logging.NullHandler',
            'level': 'DEBUG',
        }
    },
    'loggers': {
        '__main__': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'diem': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'gmail': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'googleapiclient': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
        }
    }
}


def get_log_level_value(log_level):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level %s' % log_level)

    return numeric_level


def get_log_stream(log_file):
    if log_file == '-':
        log_stream = stdout
    else:
        log_stream = open(log_file, 'a')

    return log_stream


def set_basic_config(log_level, log_file):
    log_stream = get_log_stream(log_file)
    numeric_level = get_log_level_value(log_level)
    logging.basicConfig(format=log_format, stream=log_stream, level=numeric_level)


def set_dict_config(log_level, log_file):

    log_config['handlers']['console']['level'] = log_level

    log_config['handlers']['file']['level'] = log_level
    log_config['handlers']['file']['filename'] = log_file

    logging.config.dictConfig(log_config)
