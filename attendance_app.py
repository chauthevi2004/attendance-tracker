# Hàm để trích xuất MSSV từ email đội trưởng (giả sử MSSV là phần trước dấu @)
def extract_mssv_from_email(email):
    # Tách chuỗi email bằng dấu '@' và lấy phần đầu
    mssv = email.split('@')[0]
    return mssv

# Streamlit app
st.title("ICPC Attendance Tracker")

# ID của Google Sheet - thay bằng ID của Google Sheet của bạn
sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"
sheet = connect_to_google_sheets_by_id(sheet_id)

# Tải dữ liệu từ Google Sheets
data = get_sheet_data(sheet)

# Nhập MSSV hoặc thông tin tìm kiếm từ người dùng
mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

# Thêm nút "Nhập" để thực hiện tìm kiếm
if st.button("Nhập"):
    if mssv_input:
        # Lưu thông tin tìm kiếm vào session_state
        st.session_state.query = mssv_input
        team_info = lookup_team(st.session_state.query, data)
        
        if not team_info.empty:
            st.write("### Thông tin đội:")
            team = team_info.iloc[0]
            
            # Trích xuất MSSV đội trưởng từ email
            mssv_team_leader = extract_mssv_from_email(team['Email Address'])
            
            # Hiển thị thông tin đội
            st.markdown(f"Tên đội: **{team['Tên đội (phải bắt đầu bằng UIT.)']}**")
            st.markdown(f"Email: {team['Email Address']}")
            
            # Hiển thị thông tin theo 3 cột: Họ và tên, MSSV, Vắng mặt
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("Họ và tên")
                st.write(f"{team['Họ và tên của đội trưởng']}")
                st.write(f"{team['Họ và tên của thành viên thứ 2']}")
                st.write(f"{team['Họ và tên của thành viên thứ 3']}")
            with col2:
                st.write("MSSV")
                st.write(f"{mssv_team_leader}")  # Hiển thị MSSV đội trưởng trích xuất từ email
                st.write(f"{team['MSSV thành viên thứ 2']}")
                st.write(f"{team['MSSV thành viên thứ 3']}")
            with col3:
                st.write("Vắng")
                v_team_leader = st.checkbox("Vắng đội trưởng", key="v_team_leader")
                v_member_2 = st.checkbox("Vắng thành viên thứ 2", key="v_member_2")
                v_member_3 = st.checkbox("Vắng thành viên thứ 3", key="v_member_3")
            
            # Khi nhấp vào nút "Điểm danh", cập nhật thông tin
            if st.button("Điểm danh"):
                # Tạo danh sách vắng mặt dựa trên lựa chọn của người dùng
                v_absent_list = []
                
                if v_team_leader:
                    v_absent_list.append(team['Họ và tên của đội trưởng'])
                if v_member_2:
                    v_absent_list.append(team['Họ và tên của thành viên thứ 2'])
                if v_member_3:
                    v_absent_list.append(team['Họ và tên của thành viên thứ 3'])
                
                # Chuyển danh sách vắng mặt thành chuỗi và cập nhật vào Google Sheets
                v_absent_str = ", ".join(v_absent_list)
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                data.loc[team_info.index, 'Vắng'] = v_absent_str
                
                # Cập nhật Google Sheet với dữ liệu mới
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                
                st.success(f"Đã điểm danh và cập nhật trạng thái vắng cho đội với MSSV: {st.session_state.query}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
