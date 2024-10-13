# Hàm để trích xuất MSSV từ email
def extract_mssv_from_email(email):
    # Giả sử MSSV là phần đầu của email trước dấu '@'
    mssv = email.split('@')[0]
    return mssv

# Hàm để trích xuất MSSV từ email
def extract_mssv_from_email(email):
    # Giả sử MSSV là phần đầu của email trước dấu '@'
    mssv = email.split('@')[0]
    return mssv

# Streamlit app
st.title("ICPC Attendance Tracker")

sheet_id = "18sSJDh7vBKdapozCpv4qUrRFP9ZZOOs8z3XOVqIGJDU"  # Thay thế bằng Google Sheet ID của bạn
sheet = connect_to_google_sheets_by_id(sheet_id)
data = get_sheet_data(sheet)

# Nhập MSSV từ người dùng
mssv_input = st.text_input("Nhập thông tin để tìm kiếm đội:", "")

if st.button("Nhập"):
    if mssv_input:
        st.session_state.query = mssv_input
        team_info = lookup_team(st.session_state.query, data)
        
        if not team_info.empty:
            st.write("### Thông tin đội:")
            team = team_info.iloc[0]
            
            # Trích xuất MSSV đội trưởng từ email
            mssv_team_leader = extract_mssv_from_email(team['Email Address'])
            
            st.markdown(f"Tên đội: **{team['Tên đội (phải bắt đầu bằng UIT.)']}**")
            st.markdown(f"Email: {team['Email Address']}")
            
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
            
            if st.button("Điểm danh"):
                v_absent_list = []
                
                if v_team_leader:
                    v_absent_list.append(team['Họ và tên của đội trưởng'])
                if v_member_2:
                    v_absent_list.append(team['Họ và tên của thành viên thứ 2'])
                if v_member_3:
                    v_absent_list.append(team['Họ và tên của thành viên thứ 3'])
                
                v_absent_str = ", ".join(v_absent_list)
                
                # Cập nhật dữ liệu điểm danh và vắng mặt
                data.loc[team_info.index, 'Điểm danh'] = 'Có'
                data.loc[team_info.index, 'Vắng'] = v_absent_str
                
                # Cập nhật lại Google Sheet
                sheet.update([data.columns.values.tolist()] + data.values.tolist())
                
                st.success(f"Đã điểm danh và cập nhật trạng thái vắng cho đội với MSSV: {st.session_state.query}")
        else:
            st.error("Không tìm thấy đội với thông tin đã cung cấp.")
    else:
        st.error("Vui lòng nhập thông tin tìm kiếm.")
