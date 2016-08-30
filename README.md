# LifeMotif Diem
LifeMotif Diem is a simple CLI interface to fetch and to store Gmail emails.

## How to Use

### Download credentials
Login to google.com and access to [Google Cloud Platform](https://console.cloud.google.com/iam-admin/projects?pli=1). Choose your project and download your credentials as json.


### Prepare your profile
Before doing any jobs, diem requires a profile JSON file. Create a template using 'create-profile' subcommand.
  ```./run.py create-profile```
  
Edit the profile.


### Install and Setup DB
Diem uses SQLite3 db. Install and initialize with the commands below:

  ```./run.py create-tables --profile <profile_path>```

### Authorize
Authorize to gmail.

  ```./run.py authorize --profile <profile_path>```
  
A url will appear. Copy it and paste it to a web browser. Proceed to authorize. After authorization, a code will be displayed in the web browser. Past the code to console.

### List your mail boxes
Before fetching, you need to identify your email box id.

  ```./run.py list-label --profile <profile_path>```

Choose your email box and copy Label ID. It is like: Label_83.


### Fetch your email incrementally
  ```./run.py --fetch-incrementally --profile <profile_path>```

See ./run.py --help for help.
