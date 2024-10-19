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
sheet_id = "1aeDicvTqd6KwvIRU_gcueX2QICfeumv4BxY5mOyZBMg"
sheet = connect_to_google_sheets_by_id(sheet_id)

# Streamlit app
st.title("ICPC Attendance Tracker")

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Đảm bảo MSSV không có dấu phẩy
data = format_mssv_columns(data)

if not data.empty:
    # Nhập MSSV hoặc thông tin tìm kiếm
    query = st.text_input("Nhập MSSV hoặc thông tin để tìm kiếm đội:", "")

    if query:
        team_info = lookup_team(query, data)

        if not team_info.empty:
            team = team_info.iloc[0]
            
            st.write("### Thông tin đội")
            st.markdown(f"Tên đội: <span style='color: yellow; font-weight: bold;'>{team['Tên đội (phải bắt đầu bằng UIT.)']}</span>", unsafe_allow_html=True)
            st.markdown(f"Email: {team['Email Address']}", unsafe_allow_html=True)
            st.markdown(f"Điểm danh: <span style='color: green; font-weight: bold;'>{team['Điểm danh']}</span>", unsafe_allow_html=True)

            st.write("### Thông tin thành viên")
            header_col1, header_col2, header_col3 = st.columns(3)

            # Tiêu đề cho mỗi cột
            with header_col1:
                st.write("**Họ và tên**")
            with header_col2:
                st.write("**MSSV**")
            with header_col3:
                st.write("**Vắng mặt**")

            absent_members = []  # Danh sách thành viên vắng mặt
            col1, col2, col3 = st.columns(3)

            # Hiển thị đội trưởng
            with col1:
                st.write(f"{team_info['Họ và tên của đội trưởng'].values[0]}")
            with col2:
                st.write(f"{team_info['MSSV Đội trưởng'].values[0]}")
            with col3:
                if st.checkbox(f"Đội trưởng"):
                    absent_members.append(team_info['Họ và tên của đội trưởng'].values[0])

            # Hiển thị thành viên thứ 2
            with col1:
                st.write(f"{team_info['Họ và tên của thành viên thứ 2'].values[0]}")
            with col2:
                st.write(f"{team_info['MSSV thành viên thứ 2'].values[0]}")
            with col3:
                if st.checkbox(f"Thành viên 2"):
                    absent_members.append(team_info['Họ và tên của thành viên thứ 2'].values[0])

            # Hiển thị thành viên thứ 3
            with col1:
                st.write(f"{team_info['Họ và tên của thành viên thứ 3'].values[0]}")
            with col2:
                st.write(f"{team_info['MSSV thành viên thứ 3'].values[0]}")
            with col3:
                if st.checkbox(f"Thành viên 3"):
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
