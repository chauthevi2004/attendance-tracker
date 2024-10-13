import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import io

# Kết nối với Google Sheets API bằng ID của trang tính
def connect_to_google_sheets_by_id(sheet_id):
    # Phạm vi quyền truy cập
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Đọc file credentials.json chứa thông tin tài khoản dịch vụ
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    
    # Ủy quyền kết nối
    client = gspread.authorize(creds)
    
    try:
        # Mở Google Sheet bằng ID thay vì tên
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
        data = sheet.get_all_records()  # Lấy toàn bộ dữ liệu từ Google Sheet
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()  # Trả về DataFrame rỗng nếu không kết nối được

# Cập nhật dữ liệu trong Google Sheets
def update_sheet(sheet, df):
    if sheet is not None:
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

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

# Chuyển đổi các cột MSSV thành chuỗi để đảm bảo không có dấu phẩy phân cách
def format_mssv_columns(df):
    mssv_columns = ['MSSV thành viên thứ 2', 'MSSV thành viên thứ 3', 'Email Address']
    for col in mssv_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)  # Chuyển các cột MSSV thành kiểu chuỗi
    return df

# ID của Google Sheet - thay bằng ID của Google Sheet của bạn
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"  # Thay thế bằng Google Sheet ID của bạn
sheet = connect_to_google_sheets_by_id(sheet_id)

# Streamlit app
st.title("Student Attendance Tracker")

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Đảm bảo MSSV không có dấu phẩy
data = format_mssv_columns(data)

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
