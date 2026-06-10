import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "khoa_2026_secret_key_super_secure"

# ==========================================
# CƠ SỞ DỮ LIỆU HỆ THỐNG
# ==========================================
system_info = {
    "title": "PROFILE CỦA MINH KHOA",
    "name": "Phạm Hoàng Minh Khoa",
    "subtitle_custom": "Chào mừng mọi người đến với profile cá nhân ! ",
    "version": "1.0.0 beta",
    "birthday": "12/05/2011",
    "hometown": "Hội An - Quảng Nam - Đà Nẵng",
    "hobbies": "no data",
    "target": "no data",
    "email_contact": "phamhoangminhkhoa0@gmail.com",
    "phone_contact": "private contact",
    "nv1": "THPT Thủ Đức",
    "nv2": "THPT Linh Trung",
    "nv3": "THPT Nguyễn Văn Tăng",
    "score_math": "",
    "score_literature": "",
    "score_english": "",
    "total_score": "",
    "site_locked": False,      
    "results_locked": False,
    "bg_url": "https://i.pinimg.com/736x/30/51/0d/30510d195488ce7dba3259c0c414170c.jpg",
    "avatar_url": "https://i.pinimg.com/736x/6a/04/b1/6a04b17c0ad19e4299ca8ce398b54c26.jpg",
    "family_input_data": "Chưa có dữ liệu thành viên. Hãy vào Admin để nhập mục gia đình phân dòng rõ ràng!",
    "school_conclusion": "Chưa có kết quả.",
}

comments_list = []

ADMIN_ACCOUNT = {"username": "MinhKhoaKENIE2026", "password": "MinhKhoa2011@@ken"}
SECURITY_CONFIG = {
    "admin_pin": "1205",              
    "family_gate_pin": "family2026happyandfunny"  
}

current_layer3_code = None

def log_login_activity(user_name, role, status="THÀNH CÔNG"):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "🔔" * 20)
    print(f" [BÁO CÁO TRUY CẬP HỆ THỐNG]")
    print(f" 📅 Thời gian: {time_str}")
    print(f" 👤 Tên định danh: {user_name}")
    print(f" 🔑 Quyền truy cập: {role}")
    print(f" ⚡ Trạng thái: {status}")
    print("🔔" * 20 + "\n")

@app.before_request
def check_site_status():
    if request.path.startswith('/static/'):
        return

    allowed_endpoints = ['closed_page', 'welcome', 'verify_admin_pin_api', 'login', 'logout']

    if system_info["site_locked"]:
        if session.get('is_admin') == True:
            return
        if request.endpoint not in allowed_endpoints:
            return redirect(url_for('closed_page'))

@app.route('/')
def welcome():
    return render_template('welcome.html', info=system_info)

@app.route('/api/verify-admin-pin', methods=['POST'])
def verify_admin_pin_api():
    data = request.json or {}
    pin = data.get('pin', '')
    if pin == SECURITY_CONFIG['admin_pin']:
        session['admin_pin_passed'] = True
        return jsonify({"status": "success", "redirect": url_for('login')})
    return jsonify({"status": "error", "message": "Mã PIN Admin không chính xác! Vui lòng thử lại."})

@app.route('/closed')
def closed_page():
    return render_template('closed.html', info=system_info)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin') == True:
        return redirect(url_for('admin_dashboard'))
    
    if not session.get('admin_pin_passed'):
        return redirect(url_for('welcome'))
        
    global_error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_ACCOUNT['username'] and password == ADMIN_ACCOUNT['password']:
            session['is_admin'] = True
            log_login_activity(username, "QUẢN TRỊ VIÊN (ADMIN)")
            return redirect(url_for('admin_dashboard'))
        else:
            global_error = "Tài khoản hoặc mật khẩu đăng nhập Admin không chính xác!"
            log_login_activity(username if username else "Ẩn danh", "QUẢN TRỊ VIÊN (ADMIN)", "THẤT BẠI (Sai mật khẩu)")
            
    return render_template('login.html', global_error=global_error, info=system_info)

@app.route('/family-gate', methods=['GET', 'POST'])
def family_gate():
    if 'family_verified' in session:
        return redirect(url_for('home'))
        
    global_error = None
    if request.method == 'POST':
        member_name = request.form.get('member_name', '').strip()
        shared_code = request.form.get('shared_code', '').strip()
        
        if shared_code == SECURITY_CONFIG['family_gate_pin'] and member_name:
            # Xóa triệt để quyền Admin cũ để không bị dính nút
            session.pop('is_admin', None)
            session.pop('admin_pin_passed', None)
            
            session['family_verified'] = True
            session['member_name'] = member_name
            log_login_activity(member_name, "THÀNH VIÊN GIA ĐÌNH")
            return redirect(url_for('home'))
            
        if not member_name:
            global_error = "Tên thành viên không được để trống!"
        elif shared_code != SECURITY_CONFIG['family_gate_pin']:
            global_error = "Mật mã PIN không chính xác!"
            log_login_activity(member_name if member_name else "Không tên", "THÀNH VIÊN GIA ĐÌNH", "THẤT BẠI (Sai mã PIN chung)")
            
    return render_template('family_gate.html', global_error=global_error, info=system_info)

@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'family_verified' not in session and session.get('is_admin') != True:
        return redirect(url_for('welcome'))
        
    if request.method == 'POST' and request.form.get('submit_comment'):
        c_name = request.form.get('c_name')
        c_message = request.form.get('c_message')
        is_anonymous = request.form.get('is_anonymous')
        
        if is_anonymous:
            c_name = "Người nhà ẩn danh"
            
        if c_name and c_message:
            new_id = len(comments_list) + 1
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            comments_list.append({"id": new_id, "name": c_name, "message": c_message, "date": now_str})
        return redirect(url_for('home'))
        
    # Trả trạng thái Admin về dạng chuỗi "true"/"false" để Javascript bên dưới xử lý an toàn
    is_admin_status = "true" if ( 'is_admin' in session and session.get('is_admin') == True ) else "false"
        
    return render_template('index.html', info=system_info, comments=comments_list, is_admin_flag=is_admin_status)

@app.route('/get-layer3-code', methods=['POST'])
def get_layer3_code():
    if session.get('is_admin') != True:
        return jsonify({"status": "denied"}), 403
    global current_layer3_code
    current_layer3_code = "".join(random.choices(string.digits, k=6))
    print(f"\n 🛡️ [MÃ BẢO MẬT LỚP 3 CỦA KHOA]: {current_layer3_code}\n")
    return jsonify({"status": "success"})

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_pin_passed') or session.get('is_admin') != True:
        session.clear() 
        return redirect(url_for('welcome'))
        
    global current_layer3_code
    success_msg = None
    error_msg = None
    active_tab = request.args.get('current_tab', 'tab-profile')
    
    if request.method == 'POST':
        user_l3_code = request.form.get('layer3_code_input')
        active_tab = request.form.get('current_tab', 'tab-profile')
        
        if not current_layer3_code or user_l3_code != current_layer3_code:
            error_msg = "Thực thi thất bại! Mã xác thực lớp 3 trong Terminal không chính xác."
            current_layer3_code = None
            return render_template('admin.html', info=system_info, comments=comments_list, success_msg=success_msg, error_msg=error_msg, active_tab=active_tab)
            
        current_layer3_code = None
        
        if request.form.get('update_info'):
            system_info['site_locked'] = 'site_locked' in request.form
            system_info['results_locked'] = 'results_locked' in request.form
            system_info['title'] = request.form.get('title')
            system_info['name'] = request.form.get('name')
            system_info['subtitle_custom'] = request.form.get('subtitle_custom')
            system_info['birthday'] = request.form.get('birthday')
            system_info['hometown'] = request.form.get('hometown')
            system_info['hobbies'] = request.form.get('hobbies')
            system_info['email_contact'] = request.form.get('email_contact')
            system_info['phone_contact'] = request.form.get('phone_contact')
            system_info['target'] = request.form.get('target')
            system_info['nv1'] = request.form.get('nv1')
            system_info['nv2'] = request.form.get('nv2')
            system_info['nv3'] = request.form.get('nv3')
            system_info['avatar_url'] = request.form.get('avatar_url')
            system_info['bg_url'] = request.form.get('bg_url')
            
            system_info['family_input_data'] = request.form.get('family_input_data')
            system_info['school_conclusion'] = request.form.get('school_conclusion')
            system_info['score_math'] = request.form.get('score_math')
            system_info['score_literature'] = request.form.get('score_literature')
            system_info['score_english'] = request.form.get('score_english')
            
            try:
                total = float(system_info['score_math']) + float(system_info['score_literature']) + float(system_info['score_english'])
                system_info['total_score'] = f"{total:.2f}".rstrip('0').rstrip('.')
            except ValueError:
                system_info['total_score'] = "Lỗi tính điểm"
                
            success_msg = "Cập nhật dữ liệu hệ thống cá nhân thành công!"
            
        elif request.form.get('change_password'):
            active_tab = 'tab-password'
            change_type = request.form.get('change_type')
            
            if change_type == "family_pin":
                new_fam_pin = request.form.get('new_family_pin', '').strip()
                conf_fam_pin = request.form.get('confirm_family_pin', '').strip()
                
                if not new_fam_pin:
                    error_msg = "Mã PIN gia đình mới không được để trống!"
                elif new_fam_pin != conf_fam_pin:
                    error_msg = "Xác nhận mã PIN gia đình mới không trùng khớp!"
                else:
                    SECURITY_CONFIG['family_gate_pin'] = new_fam_pin
                    success_msg = f"Thay đổi mã PIN cổng Gia đình thành công thành: {new_fam_pin}!"
            else:
                old_p = request.form.get('old_password')
                new_p = request.form.get('new_password')
                conf_p = request.form.get('confirm_password')
                
                if old_p != ADMIN_ACCOUNT['password']:
                    error_msg = "Mật khẩu quản trị cũ không chính xác!"
                elif new_p != conf_p:
                    error_msg = "Mật khẩu xác nhận mới không trùng khớp!"
                else:
                    ADMIN_ACCOUNT['password'] = new_p
                    success_msg = "Thay đổi mật khẩu điều hành Admin thành công!"
                
    return render_template('admin.html', info=system_info, comments=comments_list, success_msg=success_msg, error_msg=error_msg, active_tab=active_tab)

@app.route('/delete-comment/<int:comment_id>')
def delete_comment(comment_id):
    if session.get('is_admin') != True:
        return redirect(url_for('login'))
    global comments_list
    comments_list = [c for c in comments_list if c['id'] != comment_id]
    return redirect(url_for('admin_dashboard', current_tab='tab-comments'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
