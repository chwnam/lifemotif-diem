from datetime import datetime, date
from email import message_from_string, message_from_bytes
from email.utils import mktime_tz, parsedate_tz
from json import dumps
from copy import deepcopy


class DiaryTemplateFactory(object):
    @classmethod
    def get_template(cls):
        return {
            'diary-date': None,
            'email-date': None,
            'content': '',
            'content-type': 'text/plain',
            'attachments': {
            }
        }

    @classmethod
    def as_json(cls, obj, **kwargs):
        obj_copy = deepcopy(obj)
        for key in obj_copy:
            if type(obj_copy[key]) == datetime:
                obj_copy[key] = obj_copy[key].strftime('%Y-%m-%d %H:%M:%S %Z')
            elif type(obj_copy[key]) == date:
                obj_copy[key] = obj_copy[key].strftime('%Y-%m-%d')
        return dumps(obj_copy, **kwargs)


class DefaultJSONConverter(object):
    def __init__(self, message, diary_date, timezone):
        self.message = message
        self.diary_date = datetime.strptime(diary_date, '%Y-%m-%d').date()
        self.timezone = timezone

    @staticmethod
    def parse(message):
        if type(message) == bytes:
            return message_from_bytes(message)
        elif type(message) == str:
            return message_from_string(message)
        else:
            raise Exception('Parse failed!')

    def convert(self):
        parsed = self.parse(self.message)
        output_object = DiaryTemplateFactory.get_template()

        content_type, content = self.get_content(parsed)

        output_object['diary-date'] = self.diary_date
        output_object['email-date'] = self.get_email_date(parsed)
        output_object['content'] = content
        output_object['content-type'] = content_type

        return output_object

    def get_email_date(self, obj):

        date_text = parsedate_tz(obj['date'])
        timestamp = mktime_tz(date_text)
        email_date = datetime.fromtimestamp(timestamp, self.timezone)

        return email_date

    def get_content(self, obj):
        part = self.find_subpart(obj, 'text/html')
        content_type = 'text/html'

        if not part:
            part = self.find_subpart(obj, 'text/plain')
            content_type = 'text/plain'

        if part:
            return content_type, str(part.get_payload(decode=True), encoding=part.get_content_charset())

        return None, None

    @staticmethod
    def find_subpart(obj, content_type):
        for part in obj.walk():
            if part.get_content_type() == content_type:
                return part
