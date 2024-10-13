import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import pandas as pd

# Hàm lấy credentials từ biến môi trường
def get_credentials_from_env():
    google_credentials = os.getenv('GOOGLE_CREDENTIALS')  # Lấy biến môi trường GOOGLE_CREDENTIALS
    if google_credentials is None:
        st.error("GOOGLE_CREDENTIALS không được thiết lập.")
        return None
    try:
        creds_dict = json.loads(google_credentials)  # Chuyển chuỗi JSON thành dictionary
        return creds_dict
    except json.JSONDecodeError as e:
        st.error(f"Lỗi khi giải mã JSON: {e}")
        return None

# Kết nối với Google Sheets bằng credentials
def connect_to_google_sheets_by_id(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    creds_dict = get_credentials_from_env()
    if creds_dict:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(sheet_id).sheet1  # Kết nối tới Sheet đầu tiên
            return sheet
        except gspread.SpreadsheetNotFound:
            st.error("Không tìm thấy Google Sheet. Kiểm tra ID hoặc quyền chia sẻ.")
        except Exception as e:
            st.error(f"Lỗi khi kết nối Google Sheet: {e}")
    else:
        st.error("Không lấy được credentials.")
    return None

# Lấy dữ liệu từ Google Sheets và chuyển thành DataFrame
def get_sheet_data(sheet):
    if sheet is not None:
        try:
            data = sheet.get_all_records()  # Lấy toàn bộ dữ liệu từ Google Sheet
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            st.error(f"Lỗi khi lấy dữ liệu từ Google Sheet: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()  # Trả về DataFrame rỗng nếu không kết nối được

# Cập nhật dữ liệu trong Google Sheets
def update_sheet(sheet, df):
    if sheet is not None:
        try:
            sheet.update([df.columns.values.tolist()] + df.values.tolist())
        except Exception as e:
            st.error(f"Lỗi khi cập nhật Google Sheet: {e}")

# Chức năng tìm đội theo MSSV
def lookup_team_by_mssv(mssv, data):
    team_info = data[(data['MSSV thành viên thứ 2'].astype(str) == mssv) | 
                     (data['MSSV thành viên thứ 3'].astype(str) == mssv) |
                     (data['Email Address'].str.contains(mssv))]
    return team_info

# Chức năng điểm danh cho một MSSV
def mark_attendance(mssv, data):
    team_info = lookup_team_by_mssv(mssv, data)
    if not team_info.empty:
        data.loc[team_info.index, 'Điểm danh'] = 'Yes'
    return data

# Streamlit app
st.title("Student Attendance Tracker")

# Sử dụng Google Sheet ID do bạn cung cấp
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"

sheet = connect_to_google_sheets_by_id(sheet_id)

if sheet:
    # Tải dữ liệu từ Google Sheets
    data = get_sheet_data(sheet)

    if not data.empty:
        # Nhập MSSV từ người dùng
        mssv = st.text_input("Nhập MSSV để tìm kiếm đội:", "")

        if mssv:
            team_info = lookup_team_by_mssv(mssv, data)
            
            if not team_info.empty:
                st.write("### Thông tin đội:")
                st.dataframe(team_info)
                
                if st.button("Điểm danh"):
                    # Cập nhật điểm danh và lưu lại vào Google Sheets
                    data = mark_attendance(mssv, data)
                    update_sheet(sheet, data)
                    st.success(f"Đã điểm danh cho đội với MSSV: {mssv}")
            else:
                st.error("Không tìm thấy đội với MSSV đã cung cấp.")
    
        # Nút tải về file Excel với dữ liệu mới cập nhật
        if st.button("Tải dữ liệu điểm danh"):
            # Chuẩn bị file Excel để tải về
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                data.to_excel(writer, index=False)
            output.seek(0)

            # Cung cấp file tải về
            st.download_button(label="Tải file Excel", data=output, file_name="attendance_updated.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Không tải được dữ liệu từ Google Sheet.")
else:
    st.error("Không kết nối được với Google Sheet.")
