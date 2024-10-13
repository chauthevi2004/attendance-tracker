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

# Trích xuất MSSV từ email của đội trưởng
def extract_mssv_from_email(email):
    # Giả định rằng MSSV là một chuỗi số ở đầu email trước @
    try:
        mssv = email.split('@')[0]
        return mssv
    except IndexError:
        return "Không tìm thấy MSSV"

# Streamlit app
st.title("ICPC Attendance Tracker")

# ID của Google Sheet - thay bằng ID của Google Sheet của bạn
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"  # Thay thế bằng Google Sheet ID của bạn
sheet = connect_to_google_sheets_by_id(sheet_id)

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Nhập MSSV từ người dùng
mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

# Thiết lập trạng thái ban đầu cho các checkbox nếu chưa tồn tại trong session_state
if "leader_absent" not in st.session_state:
    st.session_state.leader_absent = False
if "member2_absent" not in st.session_state:
    st.session_state.member2_absent = False
if "member3_absent" not in st.session_state:
    st.session_state.member3_absent = False

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
            
            # Trích xuất MSSV của đội trưởng từ email
            leader_mssv = extract_mssv_from_email(team['Email Address'])
            
            # Hiển thị thông tin theo dạng bảng với ba cột
            st.markdown("#### Thông tin các thành viên")
            st.markdown("""
            <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            </style>
            """, unsafe_allow_html=True)

            # Bảng thành viên với tên, MSSV và checkbox để đánh dấu vắng mặt
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Họ và tên thành viên**")
                st.write(f"Đội trưởng: {team['Họ và tên của đội trưởng']}")
                st.write(f"Thành viên 2: {team['Họ và tên của thành viên thứ 2']}")
                st.write(f"Thành viên 3: {team['Họ và tên của thành viên thứ 3']}")

            with col2:
                st.write("**MSSV**")
                st.write(f"{leader_mssv}")
                st.write(f"{team['MSSV thành viên thứ 2']}")
                st.write(f"{team['MSSV thành viên thứ 3']}")

            with col3:
                st.write("**Vắng**")
                # Giữ trạng thái của checkbox bằng session_state
                st.session_state.leader_absent = st.checkbox("Đội trưởng vắng mặt", value=st.session_state.leader_absent)
                st.session_state.member2_absent = st.checkbox("Thành viên 2 vắng mặt", value=st.session_state.member2_absent)
                st.session_state.member3_absent = st.checkbox("Thành viên 3 vắng mặt", value=st.session_state.member3_absent)

            # Nút "Điểm danh"
            if st.button("Điểm danh"):
                # Cập nhật điểm danh và lưu lại vào Google Sheets
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                
                # Tạo danh sách các thành viên vắng mặt dựa trên trạng thái session_state
                absent_list = []
                if st.session_state.leader_absent:
                    absent_list.append(team['Họ và tên của đội trưởng'])
                if st.session_state.member2_absent:
                    absent_list.append(team['Họ và tên của thành viên thứ 2'])
                if st.session_state.member3_absent:
                    absent_list.append(team['Họ và tên của thành viên thứ 3'])

                # Cập nhật danh sách thành viên vắng mặt trong Google Sheets
                data.loc[team_info.index, 'Thành viên vắng mặt'] = ', '.join(absent_list)

                # Cập nhật vào Google Sheets
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                st.success(f"Đã điểm danh cho đội với MSSV: {st.session_state.query}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
