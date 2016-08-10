# LifeMotif Diem
LifeMotif Diem is a simple CLI interface to fetch and store Gmail emails.

## How to Use

### Download credentials
Login to google.com and access to [Google Cloud Platform](https://console.cloud.google.com/iam-admin/projects?pli=1). Choose your project and download your credentials as json.


### Install and Setup DB
Diem uses SQLite3 db. Install and initialize with the commands below:

  ```./diem-cli.py --create-tables --database <database_path>```

### Authorize
Authorize to gmail.

  ```./diem-cli.py --authorize --storage <storage_path>```
  
A url will appear. Copy it and paste it to a web browser. Proceed to authorize. After authorization, a code will be displayed in the web browser. Past the code to console.

### List your mail boxes
Before fetching, check your authorization status and decide a target mail box.

  ```./diem-cli.py --list-label --storage <storage_path> --credential <credential_path> --email <your_email_address>```

Choose your email box and copy Label ID. It is like Label_83.


### Fetch your email     
  ```./diem-cli.py --fetch --database <database_path> --storage <storage_path> --credential <credential_path> --email <your_email_address> --label-id <label_id> --dest-dir <destination_directory>```
    
You can limit your fetch by using --latest-tid argument. 

Please do not stop the program while fetching.