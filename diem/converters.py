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
            'attachments': []
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

    @classmethod
    def get_message_structure(cls, message_object):
        return cls._get_message_structure_recursively(message_object, {})

    @classmethod
    def _get_message_structure_recursively(cls, message_object, current_node):
        if message_object.is_multipart():

            current_node['content-type'] = message_object.get_content_type()
            current_node['parts'] = []

            for subpart in message_object.get_payload():
                entry = cls._get_message_structure_recursively(subpart, {})
                current_node['parts'].append(entry)

            return current_node

        else:
            content_type = message_object.get_content_type()
            file_name = message_object.get_filename()
            if file_name:
                attachment_id = message_object.get('X-Attachment-Id') or message_object.get('Content-ID').strip('<>')
            else:
                attachment_id = None

            return {
                'content-type': content_type,
                'file-name': file_name,
                'attachment-id': attachment_id
            }

    def convert(self):
        parsed = self.parse(self.message)
        output_object = DiaryTemplateFactory.get_template()

        content_type, content = self.get_content(parsed)
        attachments = self.get_attachments(parsed)

        output_object['diary-date'] = self.diary_date
        output_object['email-date'] = self.get_email_date(parsed)
        output_object['content'] = content
        output_object['content-type'] = content_type
        output_object['attachments'] = attachments

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
    def get_attachments(obj):
        attachments = []
        for part in obj.walk():
            file_name = part.get_filename()
            if file_name:
                attachments.append({
                    'file-name': file_name,
                    'content-type': part.get_content_type(),
                    'content-id': part.get('X-Attachment-Id') or part.get('Content-ID')
                })
        return attachments

    @staticmethod
    def find_subpart(obj, content_type):
        for part in obj.walk():
            if part.get_content_type() == content_type:
                return part
