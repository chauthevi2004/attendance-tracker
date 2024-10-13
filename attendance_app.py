import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Kết nối với Google Sheets API bằng ID của trang tính
def connect_to_google_sheets_by_id(sheet_id):
    # Phạm vi quyền truy cập
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Đọc thông tin credentials từ Streamlit secrets (không cần json.loads)
    creds_dict = st.secrets["gcp_service_account"]  # Sử dụng trực tiếp secrets
    
    # Tạo credentials từ từ điển
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
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

# Chức năng tìm đội theo MSSV
def lookup_team(query, data):
    # Tìm kiếm dựa trên MSSV, tên đội, đội trưởng hoặc tên thành viên
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
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"  # Thay thế bằng Google Sheet ID của bạn
sheet = connect_to_google_sheets_by_id(sheet_id)

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Nhập MSSV từ người dùng
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

            # Khởi tạo session_state cho các checkbox nếu chưa có
            if 'absent_leader' not in st.session_state:
                st.session_state.absent_leader = False
            if 'absent_member2' not in st.session_state:
                st.session_state.absent_member2 = False
            if 'absent_member3' not in st.session_state:
                st.session_state.absent_member3 = False

            # Hiển thị 3 cột: Họ và tên, MSSV, Vắng
            st.write("### Điền trạng thái vắng mặt:")
            col1, col2, col3 = st.columns(3)
            
            # Hàng 1: Đội trưởng
            with col1:
                st.markdown(f"**Đội trưởng:** {team['Họ và tên của đội trưởng']}")
            with col2:
                st.markdown(f"**MSSV:** {team['MSSV thành viên thứ 2']}")
            with col3:
                st.session_state.absent_leader = st.checkbox("Vắng", key="absent_leader", value=st.session_state.absent_leader)
            
            # Hàng 2: Thành viên 2
            with col1:
                st.markdown(f"**Thành viên thứ 2:** {team['Họ và tên của thành viên thứ 2']}")
            with col2:
                st.markdown(f"**MSSV:** {team['MSSV thành viên thứ 2']}")
            with col3:
                st.session_state.absent_member2 = st.checkbox("Vắng", key="absent_member2", value=st.session_state.absent_member2)
            
            # Hàng 3: Thành viên 3
            with col1:
                st.markdown(f"**Thành viên thứ 3:** {team['Họ và tên của thành viên thứ 3']}")
            with col2:
                st.markdown(f"**MSSV:** {team['MSSV thành viên thứ 3']}")
            with col3:
                st.session_state.absent_member3 = st.checkbox("Vắng", key="absent_member3", value=st.session_state.absent_member3)

            # Nút điểm danh
            if st.button("Điểm danh"):
                # Cập nhật trạng thái "Vắng"
                absentees = []
                if st.session_state.absent_leader:
                    absentees.append(team['Họ và tên của đội trưởng'])
                if st.session_state.absent_member2:
                    absentees.append(team['Họ và tên của thành viên thứ 2'])
                if st.session_state.absent_member3:
                    absentees.append(team['Họ và tên của thành viên thứ 3'])

                # Ghi vào cột "Vắng"
                data.loc[team_info.index, 'Vắng'] = ', '.join(absentees) if absentees else 'Không'
                # Ghi vào cột "Điểm danh"
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                
                # Cập nhật Google Sheets
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                
                st.success(f"Đã cập nhật điểm danh và thông tin vắng mặt cho đội: {team['Tên đội (phải bắt đầu bằng UIT.)']}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
