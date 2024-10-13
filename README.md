
# ICPC Attendance Tracker

This is a **Streamlit** application that allows you to track attendance for ICPC teams using data from a Google Sheet. The application provides a way to mark attendance and update the status in the Google Sheet, ensuring that MSSV (student IDs) are handled correctly and that absences are recorded.

## Features

- **Google Sheets Integration**: Fetches and updates data directly from a Google Sheet.
- **Team Lookup**: Allows users to search for teams using various fields like MSSV, email, or team name.
- **Attendance Marking**: Enables marking team members as present or absent.
- **Automatic MSSV Extraction**: Extracts MSSV from email addresses.
- **Simple UI**: Provides a user-friendly interface for checking and updating team information.

## Requirements

To run this application, install the required packages listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

The required packages are:
- `streamlit`
- `gspread`
- `oauth2client`
- `pandas`
- `openpyxl`

## How to Run

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/icpc-attendance-tracker.git
   ```

2. Navigate into the project directory:
   ```bash
   cd icpc-attendance-tracker
   ```

3. Set up your Google Cloud credentials. In **Streamlit**, these credentials should be stored in `st.secrets`. You will need a **service account** with access to the Google Sheets API. Example `secrets.toml` configuration:

   ```toml
   [gcp_service_account]
   type = "service_account"
   project_id = "your_project_id"
   private_key_id = "your_private_key_id"
   private_key = "your_private_key"
   client_email = "your_client_email"
   client_id = "your_client_id"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "your_client_x509_cert_url"
   ```

4. Run the application:
   ```bash
   streamlit run attendance_app.py
   ```

5. Open the provided URL to view the app in your browser.

## Google Sheets Setup

- Ensure that the Google Sheet you are working with has the necessary fields such as:
  - Team Name
  - Team Leader Name
  - Member Names and MSSVs
  - Email Address

## Application Functionality

1. **Team Search**: Enter MSSV, team name, or email to search for a team.
2. **Attendance Marking**: Select team members who are absent and mark attendance by clicking the "Điểm danh" button.
3. **Update Google Sheets**: The sheet is automatically updated after marking attendance.

## Example

Below is an example of the application interface:

![Application Screenshot](https://path-to-your-image.png)

## Code Overview

The main Python script, `attendance_app.py`, implements the following key functions:

- **connect_to_google_sheets_by_id(sheet_id)**: Establishes a connection to a Google Sheet using its ID.
- **get_sheet_data(sheet)**: Retrieves data from the Google Sheet and converts it into a pandas DataFrame.
- **update_sheet(sheet, df)**: Updates the Google Sheet with new data.
- **format_mssv_columns(df)**: Formats specific MSSV columns to prevent commas from being inserted.
- **extract_mssv_from_email(email)**: Extracts MSSV from an email address using regular expressions.
- **lookup_team(query, data)**: Searches for teams based on multiple criteria.
- **mark_attendance(mssv, data, absent_members)**: Marks attendance and updates absence information.

### `attendance_app.py` Example Code Snippet:

```python
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

# Connect to Google Sheets
def connect_to_google_sheets_by_id(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(sheet_id).sheet1
        return sheet
    except gspread.SpreadsheetNotFound:
        st.error("Google Sheet not found. Please check the ID or sharing permissions.")
        return None

# Get data from Google Sheets
def get_sheet_data(sheet):
    if sheet is not None:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()

# Update Google Sheets
def update_sheet(sheet, df):
    if sheet is not None:
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
```

For the full source code, please refer to the `attendance_app.py` file.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- **Streamlit** for the web app framework.
- **Google Sheets API** for data management.
