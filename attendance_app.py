import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"  # Thay thế bằng Google Sheet ID của bạn
sheet = connect_to_google_sheets_by_id(sheet_id)
data = get_sheet_data(sheet)

mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

if st.button("Nhập"):
    if mssv_input:
        st.session_state.query = mssv_input
        team_info = lookup_team(st.session_state.query, data)

        if not team_info.empty:
            st.write("### Thông tin đội:")
            team = team_info.iloc[0]
            
            # Sử dụng cột để hiển thị 3 thành viên với checkbox "Vắng"
            cols = st.columns(3)
            with cols[0]:
                st.markdown(f"**Họ và tên**")
                st.markdown(team['Họ và tên của đội trưởng'])
                st.markdown(team['Họ và tên của thành viên thứ 2'])
                st.markdown(team['Họ và tên của thành viên thứ 3'])
            with cols[1]:
                st.markdown(f"**MSSV**")
                st.markdown(team['MSSV đội trưởng'])
                st.markdown(team['MSSV thành viên thứ 2'])
                st.markdown(team['MSSV thành viên thứ 3'])
            with cols[2]:
                st.markdown(f"**Vắng**")
                # Checkbox để chọn vắng cho từng thành viên
                st.session_state.absent_leader = st.checkbox("Vắng", key="absent_leader")
                st.session_state.absent_member_2 = st.checkbox("Vắng", key="absent_member_2")
                st.session_state.absent_member_3 = st.checkbox("Vắng", key="absent_member_3")
            
            if st.button("Điểm danh"):
                # Tạo danh sách thành viên vắng
                absentees = []
                if st.session_state.absent_leader:
                    absentees.append(team['Họ và tên của đội trưởng'])
                if st.session_state.absent_member_2:
                    absentees.append(team['Họ và tên của thành viên thứ 2'])
                if st.session_state.absent_member_3:
                    absentees.append(team['Họ và tên của thành viên thứ 3'])

                # Cập nhật cột "Điểm danh" và cột "Vắng"
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                data.loc[team_info.index, 'Vắng'] = ", ".join(absentees) if absentees else 'Không'

                # Lưu cập nhật vào Google Sheet
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                st.success("Đã điểm danh và cập nhật trạng thái vắng.")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
