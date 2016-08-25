# LifeMotif Diem
LifeMotif Diem is a simple CLI interface to fetch and to store Gmail emails.

## How to Use

### Download credentials
Login to google.com and access to [Google Cloud Platform](https://console.cloud.google.com/iam-admin/projects?pli=1). Choose your project and download your credentials as json.


### Install and Setup DB
Diem uses SQLite3 db. Install and initialize with the commands below:

  ```./run.py create-tables --database <database_path>```

### Authorize
Authorize to gmail.

  ```./run.py authorize --credential <credential_path> --storage <storage_path>```
  
A url will appear. Copy it and paste it to a web browser. Proceed to authorize. After authorization, a code will be displayed in the web browser. Past the code to console.

### List your mail boxes
Before fetching, you need to identify your email box id.

  ```./run.py list-label --storage <storage_path> --email <your_email_address>```

Choose your email box and copy Label ID. It is like Label_83.


### Fetch your email incrementally
  ```./run.py --fetch-incrementally --database <database_path> --storage <storage_path> --email <your_email_address> --label-id <label_id> --archive-path <archive_path>```

See ./run.py --help for help.
