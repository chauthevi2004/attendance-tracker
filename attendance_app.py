import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Kết nối với Google Sheets API bằng ID của trang tính
def connect_to_google_sheets_by_id(sheet_id):
    # Phạm vi quyền truy cập
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Đọc thông tin credentials từ Streamlit secrets
    creds_dict = st.secrets["gcp_service_account"]
    
    # Tạo credentials từ từ điển
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # Ủy quyền kết nối
    client = gspread.authorize(creds)
    
    try:
        # Mở Google Sheet bằng ID
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

# Chức năng tìm kiếm đội dựa trên tất cả thông tin
def lookup_team(query, data):
    # Tìm kiếm dựa trên MSSV, tên đội, đội trưởng hoặc tên thành viên
    team_info = data[(data['MSSV thành viên thứ 2'].astype(str) == query) | 
                     (data['MSSV thành viên thứ 3'].astype(str) == query) |
                     (data['Email Address'].str.contains(query, case=False)) |
                     (data['Tên đội (phải bắt đầu bằng UIT.)'].str.contains(query, case=False)) |
                     (data['Họ và tên của đội trưởng'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 2'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 3'].str.contains(query, case=False))]
    return team_info

# Cập nhật thông tin thành viên vắng và điểm danh
def mark_attendance_and_absence(mssv, data, absences):
    team_info = lookup_team(mssv, data)
    if not team_info.empty:
        # Cập nhật trạng thái điểm danh
        data.loc[team_info.index, 'Điểm danh'] = 'Có'
        
        # Cập nhật danh sách thành viên vắng
        absent_names = ', '.join(absences)
        data.loc[team_info.index, 'Vắng'] = absent_names
    return data

# Chuyển đổi các cột MSSV thành chuỗi
def format_mssv_columns(df):
    mssv_columns = ['MSSV thành viên thứ 2', 'MSSV thành viên thứ 3', 'Email Address']
    for col in mssv_columns:
        if col in df.columns:
            df[col] = df[col].astype(str)
    return df

# ID của Google Sheet
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"
sheet = connect_to_google_sheets_by_id(sheet_id)

# Streamlit app
st.title("ICPC Attendance Tracker")

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Đảm bảo MSSV không có dấu phẩy
data = format_mssv_columns(data)

if not data.empty:
    # Nhập thông tin tìm kiếm từ người dùng
    query = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

    if query:
        team_info = lookup_team(query, data)
        
        if not team_info.empty:
            st.write("### Thông tin đội:")
            st.dataframe(team_info)
            
            # Biến lưu trạng thái của các thành viên vắng
            absences = []
            for index, row in team_info.iterrows():
                st.write(f"Đội trưởng: {row['Họ và tên của đội trưởng']}")
                
                # Checkbox vắng cho từng thành viên
                absent_member_2 = st.checkbox(f"Vắng {row['Họ và tên của thành viên thứ 2']} - MSSV: {row['MSSV thành viên thứ 2']}", key=f"{row['MSSV thành viên thứ 2']}")
                absent_member_3 = st.checkbox(f"Vắng {row['Họ và tên của thành viên thứ 3']} - MSSV: {row['MSSV thành viên thứ 3']}", key=f"{row['MSSV thành viên thứ 3']}")

                # Chỉ lưu tên thành viên nếu họ được đánh dấu vắng
                if absent_member_2:
                    absences.append(row['Họ và tên của thành viên thứ 2'])
                if absent_member_3:
                    absences.append(row['Họ và tên của thành viên thứ 3'])

            # Chỉ khi bấm nút "Điểm danh" mới thực hiện cập nhật
            if st.button("Điểm danh"):
                # Cập nhật điểm danh và vắng mặt vào Google Sheets
                data = mark_attendance_and_absence(query, data, absences)
                update_sheet(sheet, data)
                st.success(f"Đã điểm danh cho đội với thông tin: {query}. Thành viên vắng: {', '.join(absences)}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
else:
    st.error("Không tải được dữ liệu từ Google Sheet.")
