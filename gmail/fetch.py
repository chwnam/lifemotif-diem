from base64 import urlsafe_b64decode
from datetime import datetime
from email.utils import mktime_tz, parsedate_tz
from gzip import open as gzip_open
from pytz import timezone
from os import getcwd
from os.path import isabs as path_isabs
from os.path import expanduser, realpath, join as path_join
from logging import getLogger

from googleapiclient.errors import HttpError

import re

date_expr = re.compile(r'^Date: (.+?)$', re.DOTALL | re.MULTILINE)

logger = getLogger(__name__)

TIMEZONE = 'Asia/Seoul'


def fetch_structure(service, email, label_id, latest_mid):
    """
    Fetch message_id, thread_id of message box.

    :param service:
    :param email:
    :param label_id:
    :param latest_mid:
    :return: list of tuples: (message_id, thread_id)
    """
    page_token = ''
    first_loop = True
    output = []

    logger.info(
        'fetch_structure started. email: %s, label_id: %s, latest_mid: %d (0x%x)' % (
            email, label_id, latest_mid, latest_mid
        )
    )

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

            if message_id <= latest_mid:
                logger.debug('latest_mid reached.')
                page_token = ''
                break

            output.append((message_id, thread_id))

    logger.info('fetch_structure completed. Total %s items' % len(output))

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
    try:
        response = service.users().messages().get(id='%x' % message_id, userId=email, format='raw').execute()
        logger.debug('fetch_mail: %s, mid %d (0x%x)' % (email, message_id, message_id))

    except HttpError:
        logger.error('Email address \'%s\', message id: %d (0x%x) not found.' % (email, message_id, message_id))
        response = None

    return response


def extract_diary_dates(service, email, structure):

    logger.info(
        'extract_diary_dates started. email: %s, structure: %d item(s).' %
        (email, len(structure))
    )

    # Please be patient!
    # It may take minutes because every alarm mail in the structure is going to be fetched
    #  to extract its date field within.

    output = {}

    for message_id, thread_id in structure:

        if message_id != thread_id:
            continue

        # you have to fetch every single message to get date header field.
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

        logger.debug('Message id %x, diary date %s extracted.' % (message_id, date))

        output[message_id] = date

    logger.info('extract_diary_dates completed. %d date(s).' % len(output))

    return output


def fetch_and_archive(service, email, archive_path, mid_list):

    logger.info(
        'fetch_and_archive started. email: %s, archive_path: %s, mid_list: %d message(s)' %
        (email, archive_path, len(mid_list))
    )

    if path_isabs(archive_path):
        output_dir = realpath(archive_path)
    else:
        output_dir = realpath(expanduser(path_join(getcwd(), archive_path)))

    count = 0
    error = 0

    for mid in mid_list:

        file_name = path_join(output_dir, ('%x.gz' % mid))
        message = fetch_mail(service, email, mid)

        if not message:
            error += 1
            continue

        with gzip_open(file_name, 'wb') as f:
            f.write(urlsafe_b64decode(message['raw']))
            logger.debug('Message id %x gzipped to %s.' % (mid, file_name))

        count += 1

    logger.info('fetch_and_archive completed. Total %d item(s) saved. Error %d item(s).' % (count, error))


def get_archive(mid, archive_path):

    if path_isabs(archive_path):
        archive_dir = realpath(archive_path)
    else:
        archive_dir = realpath(expanduser(path_join(getcwd(), archive_path)))

    path = path_join(archive_dir, '%x.gz' % mid)

    with gzip_open(path, 'rb') as f:
        mime = f.read()

    logger.debug('Archive \'%s\' extracted successfully. %d bytes' % (path, len(mime)))

    return mime
