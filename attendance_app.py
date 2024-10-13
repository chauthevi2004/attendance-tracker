import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Kết nối với Google Sheets API bằng ID của trang tính
def connect_to_google_sheets_by_id(sheet_id):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]  # Sử dụng trực tiếp secrets
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
        data = sheet.get_all_records()  # Lấy toàn bộ dữ liệu từ Google Sheet
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()  # Trả về DataFrame rỗng nếu không kết nối được

# Chức năng tìm đội theo MSSV
def lookup_team(query, data):
    team_info = data[(data['MSSV thành viên thứ 2'].astype(str) == query) | 
                     (data['MSSV thành viên thứ 3'].astype(str) == query) |
                     (data['Email Address'].str.contains(query)) |
                     (data['Tên đội (phải bắt đầu bằng UIT.)'].str.contains(query, case=False)) |
                     (data['Họ và tên của đội trưởng'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 2'].str.contains(query, case=False)) |
                     (data['Họ và tên của thành viên thứ 3'].str.contains(query, case=False))]
    return team_info

# Streamlit app
st.title("ICPC Attendance Tracker")

# ID của Google Sheet - thay bằng ID của Google Sheet của bạn
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"
sheet = connect_to_google_sheets_by_id(sheet_id)

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Debug: print column names to check if they match
if not data.empty:
    st.write("### Debug: Available columns in the data")
    st.write(data.columns.tolist())  # This will print the column names in the Streamlit app

# Nhập MSSV từ người dùng
mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

# Thêm nút "Nhập"
if st.button("Nhập"):
    if mssv_input:
        st.session_state.query = mssv_input
        team_info = lookup_team(st.session_state.query, data)
        
        if not team_info.empty:
            st.write("### Thông tin đội:")
            team = team_info.iloc[0]
            
            # Hiển thị thông tin đội theo hàng với 3 cột
            col1, col2, col3 = st.columns(3)

            # Tạo checkbox để đánh dấu thành viên vắng mặt
            absent_leader = col3.checkbox(f"Vắng", key="leader_absent")
            absent_member2 = col3.checkbox(f"Vắng", key="member2_absent")
            absent_member3 = col3.checkbox(f"Vắng", key="member3_absent")

            # Ensure the correct column names are used here
            col1.markdown(f"Đội trưởng: {team['Họ và tên của đội trưởng']}")
            col2.markdown(f"MSSV: {team.get('MSSV đội trưởng', 'N/A')}")  # Fallback in case the column doesn't exist

            col1.markdown(f"Thành viên thứ 2: {team['Họ và tên của thành viên thứ 2']}")
            col2.markdown(f"MSSV: {team.get('MSSV thành viên thứ 2', 'N/A')}")  # Fallback in case the column doesn't exist

            col1.markdown(f"Thành viên thứ 3: {team['Họ và tên của thành viên thứ 3']}")
            col2.markdown(f"MSSV: {team.get('MSSV thành viên thứ 3', 'N/A')}")  # Fallback in case the column doesn't exist

            if st.button("Điểm danh"):
                # Cập nhật danh sách vắng mặt
                absent_members = []
                if absent_leader:
                    absent_members.append(team['Họ và tên của đội trưởng'])
                if absent_member2:
                    absent_members.append(team['Họ và tên của thành viên thứ 2'])
                if absent_member3:
                    absent_members.append(team['Họ và tên của thành viên thứ 3'])
                
                absent_str = ", ".join(absent_members)
                
                # Cập nhật dữ liệu trên Google Sheets
                data.loc[team_info.index, 'Vắng'] = absent_str
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                
                # Cập nhật lại Google Sheet
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                st.success(f"Đã cập nhật điểm danh và vắng mặt: {absent_str}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
