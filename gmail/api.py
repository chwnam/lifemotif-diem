from httplib2 import Http

# google oauth2client libraries
from apiclient import discovery
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'


def authorize(credential_file, storage_file):

    flow = flow_from_clientsecrets(credential_file, scope=GMAIL_SCOPE, redirect_uri=REDIRECT_URI)

    auth_uri = flow.step1_get_authorize_url()

    print(auth_uri)

    code = input('Please visit above url, and copy and paste code: ')

    Storage(storage_file).put(flow.step2_exchange(code))


def get_service(storage_file):

    credentials = Storage(storage_file).get()

    if not credentials:
        raise Exception('credentials are invalid. Please authorize first.')

    http = Http()

    if credentials.access_token_expired:
        credentials.refresh(http)

    return discovery.build(serviceName='gmail', version='v1', http=credentials.authorize(http))


def get_labels(service, email):
    """
    List your email labels. Returns a list that contains all of your email labels.
    Each label is a dictionary, and has at least these keys:
      - id
      - name
      - type
    Any other keys may be inserted, however the most important key is 'id', because you have to input this value
    when you want to fetch your emails.

    :param service:
    :param email:
    :return: list
    """

    from operator import itemgetter

    labels = service.users().labels().list(userId=email).execute()['labels']

    labels.sort(key=itemgetter('name'))

    return labels
