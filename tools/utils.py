from __future__ import print_function
import json, os, re
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


file_name = "utils.json"
pwd = os.getcwd()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def write_day(day):
    with open(file_name, "w") as jsf:
        json.dump({"day": day}, jsf)

def read_day(default):
    try:
        with open(file_name, "r") as jsf:
            return json.loads(jsf.read())["day"]
    except:
        return default
    
class Google_Sheets:
    
    def __init__(self, pwd, SPREADSHEET_ID, RANGE) -> None:
        self.pwd = pwd
        self.token_path = os.path.join(self.pwd, 'token.json')
        self.cred_path = os.path.join(self.pwd, 'credentials.json')

        self.SPREADSHEET_ID = SPREADSHEET_ID
        self.RANGE = RANGE

    def O2Auth(self):
        """Shows basic usage of the Sheets API.
        Prints values from a sample spreadsheet.
        """
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.cred_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

    def parse_data_by_day(self, day=1):
        payload = []
        errors = []
        try:
            service = build('sheets', 'v4', credentials=self.creds)

            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID,
                                        range=f'{day}!{self.RANGE}').execute()
            values = result.get('values', [])

            for row in values:
                if not row: continue
                elif len(row) != 3: 
                    print("Size row is not 3")
                    continue
                
                vars = []
                ans = -1
                try: 
                    vars = re.sub('["\]\[]', '', row[1]).split(",")
                    ans = int(row[2])
                except Exception as err:
                    print(err)
                    errors.append(err)

                if ans -1  > len(vars):
                    errors.append(f"Некоторый ответ не подходит, проверь таблицу [{row[0]}]")
                    continue

                payload.append({
                    "ask": row[0],
                    "vars": [v.strip() for v in vars],
                    "ans": ans
                })
        except HttpError as err:
            errors.append(err)
        return payload, errors
