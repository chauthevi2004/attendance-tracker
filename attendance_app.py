import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

# Kết nối với Google Sheets API bằng ID của trang tính
def connect_to_google_sheets_by_id(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open_by_key(sheet_id).sheet1
        return sheet
    except gspread.SpreadsheetNotFound:
        st.error("Không tìm thấy Google Sheet. Kiểm tra ID hoặc quyền chia sẻ.")
        return None
    except Exception as e:
        st.error(f"Lỗi khi kết nối Google Sheet: {e}")
        return None

# Lấy dữ liệu từ Google Sheets và chuyển thành DataFrame
def get_sheet_data(sheet):
    if sheet is not None:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()

# Cập nhật dữ liệu trong Google Sheets
def update_sheet(sheet, df):
    if sheet is not None:
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

# Chuyển đổi các cột MSSV thành chuỗi để đảm bảo không có dấu phẩy phân cách
def format_mssv_columns(df):
    mssv_columns = ['MSSV thành viên thứ 2', 'MSSV thành viên thứ 3', 'Email Address']
    for col in mssv_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df

# Hàm trích xuất MSSV từ email
def extract_mssv_from_email(email):
    match = re.search(r'\b\d{8,9}\b', email)
    if match:
        return match.group(0)  # Trả về MSSV đầu tiên tìm thấy
    return None

# Hàm tìm kiếm đội dựa trên nhiều tiêu chí
def lookup_team(query, data):
    team_info = data[(data['MSSV thành viên thứ 2'].astype(str) == query) | 
                     (data['MSSV thành viên thứ 3'].astype(str) == query) |
                     (data['Email Address'].str.contains(query)) |
                     (data['Tên đội (phải bắt đầu bằng UIT.)'].str.contains(query, case=False)) |
                     (data['Họ và tên của đội trưởng'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 2'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 3'].str.contains(query, case=False))]
    
    if not team_info.empty:
        team_info['MSSV Đội trưởng'] = team_info['Email Address'].apply(extract_mssv_from_email)
    
    return team_info

# Hàm xử lý điểm danh và vắng mặt
def mark_attendance(mssv, data, absent_members):
    team_info = lookup_team(mssv, data)
    if not team_info.empty:
        data.loc[team_info.index, 'Điểm danh'] = 'Có'
        data.loc[team_info.index, 'Vắng'] = ', '.join(absent_members)  # Cập nhật cột 'Vắng'
    return data

# ID của Google Sheet
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"
sheet = connect_to_google_sheets_by_id(sheet_id)

# Streamlit app
st.title("ICPC Attendance Tracker")

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Đảm bảo MSSV không có dấu phẩy
data = format_mssv_columns(data)

# Nhập thông tin từ người dùng
mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")


# Thêm nút "Nhập"
if st.button("Nhập"):
    if mssv_input:
        # Lưu MSSV vào session state
        st.session_state.query = mssv_input  # Lưu MSSV vào session_state
        team_info = lookup_team(st.session_state.query, data)
        
        if not team_info.empty:
            st.write("### Thông tin đội:")
            
            # Lấy hàng đầu tiên của team_info để hiển thị các thông tin
            team = team_info.iloc[0]
            st.markdown(f"<span style='color: yellow; font-weight: bold;'>Tên đội:</span> **{team['Tên đội (phải bắt đầu bằng UIT.)']}**", unsafe_allow_html=True)
            st.write(f"Email: {team['Email Address']}")

            # Hiển thị các cột: Họ và tên, MSSV, checkbox Vắng mặt
            absent_members = []  # Danh sách thành viên vắng mặt
            col1, col2, col3 = st.columns(3)

            # Hiển thị đội trưởng
            with col1:
                st.write(f"Đội trưởng: {team_info['Họ và tên của đội trưởng'].values[0]}")
            with col2:
                st.write(f"MSSV: {team_info['MSSV Đội trưởng'].values[0]}")
            with col3:
                if st.checkbox(f"Vắng mặt - Đội trưởng"):
                    absent_members.append(team_info['Họ và tên của đội trưởng'].values[0])

            # Hiển thị thành viên thứ 2
            with col1:
                st.write(f"Thành viên 2: {team_info['Họ và tên của thành viên thứ 2'].values[0]}")
            with col2:
                st.write(f"MSSV: {team_info['MSSV thành viên thứ 2'].values[0]}")
            with col3:
                if st.checkbox(f"Vắng mặt - Thành viên 2"):
                    absent_members.append(team_info['Họ và tên của thành viên thứ 2'].values[0])

            # Hiển thị thành viên thứ 3
            with col1:
                st.write(f"Thành viên 3: {team_info['Họ và tên của thành viên thứ 3'].values[0]}")
            with col2:
                st.write(f"MSSV: {team_info['MSSV thành viên thứ 3'].values[0]}")
            with col3:
                if st.checkbox(f"Vắng mặt - Thành viên 3"):
                    absent_members.append(team_info['Họ và tên của thành viên thứ 3'].values[0])

            if st.button("Điểm danh"):
                # Cập nhật điểm danh và vắng mặt
                data = mark_attendance(query, data, absent_members)
                update_sheet(sheet, data)
                st.success("Đã cập nhật điểm danh.")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
else:
    st.error("Không tải được dữ liệu từ Google Sheet.")
