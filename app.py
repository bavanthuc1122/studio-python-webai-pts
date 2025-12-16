import os
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (nếu có)
load_dotenv()

app = Flask(__name__)

# --- DATABASE CONFIGURATION ---
# Lấy chuỗi kết nối MongoDB từ biến môi trường hoặc sử dụng mặc định
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017/studio_db')
client = MongoClient(MONGO_URL)
db = client.get_default_database()

# Collections trong MongoDB
messages_collection = db.messages
labels_collection = db.labels
config_collection = db.config

# Label công khai (không lưu trong DB)
PUBLIC_LABELS = ["Mới", "Đã xử lý", "Chờ phản hồi", "Hoàn thành"]

# --- DATABASE INITIALIZATION ---
def init_db():
    """Khởi tạo cơ sở dữ liệu với dữ liệu mặc định nếu chưa tồn tại"""
    # Kiểm tra và khởi tạo collection labels
    if labels_collection.count_documents({}) == 0:
        labels_collection.insert_one({"labels": PUBLIC_LABELS})
    
    # Kiểm tra và khởi tạo collection config
    if config_collection.count_documents({}) == 0:
        default_config = {
            "bg_image": "https://images.unsplash.com/photo-1557683316-973673baf926?q=80&w=2029",
            "text_color": "#ffffff",
            "glass_color": "rgba(255, 255, 255, 0.25)"
        }
        config_collection.insert_one(default_config)

# Gọi hàm khởi tạo DB khi ứng dụng khởi động
init_db()

# --- HELPER FUNCTIONS ---
def get_config():
    """Lấy cấu hình từ MongoDB"""
    config_doc = config_collection.find_one()
    if config_doc:
        # Loại bỏ _id để trả về dict sạch
        config_doc.pop('_id', None)
        return config_doc
    return {
        "bg_image": "https://images.unsplash.com/photo-1557683316-973673baf926?q=80&w=2029",
        "text_color": "#ffffff",
        "glass_color": "rgba(255, 255, 255, 0.25)"
    }

def update_config_in_db(new_config):
    """Cập nhật cấu hình trong MongoDB"""
    config_collection.update_one({}, {"$set": new_config}, upsert=True)

def get_labels():
    """Lấy danh sách labels từ MongoDB"""
    labels_doc = labels_collection.find_one()
    if labels_doc and 'labels' in labels_doc:
        return labels_doc['labels']
    return PUBLIC_LABELS

def update_labels_in_db(labels_list):
    """Cập nhật danh sách labels trong MongoDB"""
    labels_collection.update_one({}, {"$set": {"labels": labels_list}}, upsert=True)

# --- ROUTES ---
@app.route('/')
def client_view():
    # Truyền config sang file HTML
    conf = get_config()
    return render_template('client.html', config=conf)

# --- ADMIN API ---
@app.route('/api/admin/update_config', methods=['POST'])
def update_config():
    data = request.json or {}
    current_conf = get_config()
    
    # Cập nhật các trường mới
    if 'bg_image' in data: 
        current_conf['bg_image'] = data['bg_image']
    if 'text_color' in data: 
        current_conf['text_color'] = data['text_color']
    
    update_config_in_db(current_conf)
    return jsonify({'success': True, 'message': 'Đã cập nhật giao diện!'})

@app.route('/admin')
def admin_view(): 
    return render_template('admin.html')

# --- API CLIENT ---
@app.route('/api/submit', methods=['POST'])
def submit_info():
    data = request.json or {}
    
    # Kiểm tra trùng image_link trong DB trước khi Insert
    image_link = data.get('image_link', '')
    if not image_link:
        return jsonify({'success': False, 'message': 'Vui lòng nhập Link ảnh!'}), 400
        
    existing_message = messages_collection.find_one({"image_link": image_link})
    if existing_message:
        return jsonify({'success': False, 'message': 'Link ảnh đã tồn tại!'}), 400

    # Random Avatar (1.png -> 5.png)
    avatar_id = random.randint(1, 5) 

    new_record = {
        'customer_name': data.get('customer_name', ''),
        'shoot_date': data.get('shoot_date', ''),
        'image_link': image_link,
        'note': data.get('note', ''),
        'status': 'new',
        'label': 'Mới',
        'avatar': f'/static/avatars/{avatar_id}.png', # Đường dẫn avatar
        'result_link': '',    # Link trả ảnh (khi hoàn thành)
        'result_content': '', # Lời nhắn (khi hoàn thành)
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    messages_collection.insert_one(new_record)
    return jsonify({'success': True, 'message': 'Đã gửi thông tin!'})

@app.route('/api/check', methods=['POST'])
def check_info():
    data = request.json or {}
    link = data.get('image_link', '')
    if not link:
        return jsonify({'success': False, 'message': 'Vui lòng nhập Link ảnh!'}), 400
        
    record = messages_collection.find_one({"image_link": link})
    
    if record:
        # Chuyển ObjectId thành string để có thể serialize
        record['_id'] = str(record['_id'])
        
        # LOGIC ẨN LABEL NỘI BỘ
        display_record = record.copy()
        if display_record['label'] not in PUBLIC_LABELS:
            display_record['label'] = "Đang xử lý" # Khách chỉ thấy dòng này nếu Admin dùng label lạ
            
        return jsonify({'success': True, 'data': display_record})
    return jsonify({'success': False, 'message': 'Không tìm thấy thông tin.'}), 404

# --- API ADMIN ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '')
    password = data.get('password', '')
    if username == 'admin' and password == 'studio123':
        return jsonify({'success': True})
    return jsonify({'success': False}), 401

@app.route('/api/admin/data', methods=['GET'])
def get_admin_data():
    # Lấy toàn bộ danh sách tin nhắn (sort theo ngày mới nhất)
    messages = list(messages_collection.find().sort("created_at", -1))
    # Chuyển ObjectId thành string để có thể serialize
    for msg in messages:
        msg['_id'] = str(msg['_id'])
    
    return jsonify({'messages': messages, 'labels': get_labels()})

@app.route('/api/admin/manage_label', methods=['POST'])
def manage_label():
    data = request.json or {}
    action = data.get('action') # 'add' or 'delete'
    label_name = data.get('label', '')
    
    if not label_name:
        return jsonify({'success': False, 'message': 'Vui lòng nhập tên Label!'}), 400
        
    current_labels = get_labels()

    if action == 'add':
        if label_name not in current_labels:
            current_labels.append(label_name)
    elif action == 'delete':
        if label_name in current_labels and label_name not in PUBLIC_LABELS: # Không cho xóa Label cứng
            current_labels.remove(label_name)
        else:
            return jsonify({'success': False, 'message': 'Không thể xóa Label mặc định!'})

    update_labels_in_db(current_labels)
    return jsonify({'success': True, 'labels': current_labels})

@app.route('/api/admin/update_ticket', methods=['POST'])
def update_ticket():
    data = request.json or {}
    image_link = data.get('image_link', '')
    if not image_link:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp Link ảnh!'}), 400
        
    query = {"image_link": image_link}
    
    # Tạo bản cập nhật
    update_data = {}
    if 'customer_name' in data: 
        update_data['customer_name'] = data['customer_name']
    if 'note' in data: 
        update_data['note'] = data['note']
    if 'label' in data: 
        update_data['label'] = data['label']
    
    # Cập nhật kết quả trả về (nếu có)
    if 'result_link' in data: 
        update_data['result_link'] = data['result_link']
    if 'result_content' in data: 
        update_data['result_content'] = data['result_content']
    
    result = messages_collection.update_one(query, {"$set": update_data})
    
    if result.matched_count > 0:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Không tìm thấy bản ghi để cập nhật!'}), 404

@app.route('/api/admin/delete_ticket', methods=['POST'])
def delete_ticket():
    data = request.json or {}
    link_to_delete = data.get('image_link', '')
    if not link_to_delete:
        return jsonify({'success': False, 'message': 'Vui lòng cung cấp Link ảnh!'}), 400
        
    result = messages_collection.delete_one({"image_link": link_to_delete})
    
    if result.deleted_count > 0:
        return jsonify({'success': True, 'message': 'Đã xóa thành công!'})
    return jsonify({'success': False, 'message': 'Không tìm thấy dữ liệu để xóa'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)