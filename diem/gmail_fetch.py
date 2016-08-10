from base64 import urlsafe_b64decode
from datetime import datetime
from email.utils import mktime_tz, parsedate_tz
from gzip import open as gzip_open
from pytz import timezone
from os import getcwd
from os.path import isabs as path_isabs
from os.path import expanduser, realpath, join as path_join
from logging import getLogger

import re

date_expr = re.compile(r'^Date: (.+?)$', re.DOTALL|re.MULTILINE)

logger = getLogger(__name__)

TIMEZONE = 'Asia/Seoul'


def fetch_structure(service, email, label_id, latest_tid):
    """
    Fetch message_id, thread_id of message box.

    :param service:
    :param email:
    :param label_id:
    :param latest_tid:
    :return: list of tuples: (message_id, thread_id)
    """
    page_token = ''
    first_loop = True
    output = []

    logger.info('Structure fetching started. email: %s, label_id: %s, latest_tid: %x' % (email, label_id, latest_tid))

    while page_token or first_loop:

        first_loop = False

        # Expected keys
        #   messages[]
        #   nextPageToken
        #   resultSizeEstimate
        response = service.users().messages().list(
            userId=email,
            labelIds=label_id,
            includeSpamTrash=False,
            pageToken=page_token
        ).execute()

        messages = response['messages'] if 'messages' in response else []
        page_token = response['nextPageToken'] if 'nextPageToken' in response else ''

        for message in messages:
            message_id = int(message['id'], 16)
            thread_id = int(message['threadId'], 16)

            logger.debug('message id: %s, thread id: %s' % (message['id'], message['threadId']))

            if thread_id <= latest_tid:
                logger.debug('latest_tid reached.')
                page_token = ''
                break

            output.append((message_id, thread_id))

    logger.info('Structure fetching completed. Total %s items' % len(output))

    return output


def get_default_timezone():
    return timezone(TIMEZONE)


def fetch_mail(service, email, message_id):
    """
    response has below keys:
        id
        threadId
        labelIds[]
        snippet
        historyId
        internalDate
        sizeEstimate
        raw

    :param service:
    :param email:
    :param message_id:
    :return:
    """
    logger.debug('Fetching message id %x from %s' % (message_id, email, ))
    response = service.users().messages().get(id='%x' % message_id, userId=email, format='raw').execute()

    return response


def fetch_diary_dates(service, email, structure):

    output = {}

    for message_id, thread_id in structure:

        if message_id != thread_id:
            continue

        message = fetch_mail(service, email, message_id)
        raw_message = urlsafe_b64decode(message['raw']).decode('ascii')

        date = None

        searched = date_expr.search(raw_message)
        if searched:
            date_text = searched.group(1)
            date = parsedate_tz(date_text)
            timestamp = mktime_tz(date)
            date = datetime.fromtimestamp(timestamp, get_default_timezone()).date()

        assert date is not None

        logger.debug('Message id %x, diary date extracted: %s.' % (message_id, date))

        output[message_id] = date

    return output


def fetch_reply_mails(service, email, structure, dest_dir):

    if path_isabs(dest_dir):
        output_dir = realpath(dest_dir)
    else:
        output_dir = realpath(expanduser(path_join(getcwd(), dest_dir)))

    count = 0

    for message_id, thread_id in structure:
        if message_id == thread_id:
            continue

        file_name = path_join(output_dir, ('%x.gz' % message_id))
        message = fetch_mail(service, email, message_id)

        with gzip_open(file_name, 'wb') as f:
            f.write(urlsafe_b64decode(message['raw']))
            logger.debug('Message id %x gzipped to %s.' % (message_id, file_name))

        count += 1

    logger.info('Fetching reply mails completed. Total %d items saved.' % count)
