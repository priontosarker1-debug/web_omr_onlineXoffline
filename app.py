from flask import Flask, render_template, request, redirect, url_for
import os
import csv
from omr_processor import grade_sheet

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- 1. MEMORY STORAGE ---
# master_results stores data for your secret admin table
master_results = []
submitted_ips = set()

# Hidden Master Key
master_ans = [0, 0, 1, 0, 1, 0, 0, 3, 1, 0, 0, 1, 0, 1, 2, 1, 3, 1, 0, 1, 0, 1, 3, 0, 1, 0, 1, 0, 1, 0]

@app.route('/')
def index():
    return render_template('index.html')

# --- 2. THE SECRET ADMIN PANEL ---
# Visit your-site.onrender.com/admin-portal-88 to see the table
@app.route('/admin-portal-88')
def admin_panel():
    return render_template('admin.html', results=master_results)

@app.route('/set_key', methods=['POST'])
def set_key():
    global master_ans
    raw_key = request.form['master_key']
    try:
        master_ans = [int(x.strip()) for x in raw_key.split(',')]
        return "<h1>Success! Master key updated.</h1><a href='/admin-portal-88'>Back to Admin</a>"
    except Exception as e:
        return f"<h1>Error!</h1><p>Check your commas and numbers.</p>"

@app.route('/upload', methods=['POST'])
def upload_file():
    # --- 3. IP BLOCKING ---
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if user_ip in submitted_ips:
        return """
        <div style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #e74c3c;">Access Denied</h1>
            <p>You have already submitted an exam from this connection.</p>
            <a href="/">Back to Home</a>
        </div>
        """, 403

    name = request.form['student_name']
    roll = request.form['student_number']
    uid = request.form['unique_id']
    file = request.files['omr_image']
    
    if file:
        raw_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uid}_raw.png")
        graded_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uid}_graded.png")
        file.save(raw_path)
        
        # Grading logic
        score, final_img_path = grade_sheet(raw_path, graded_path, master_ans)
        
        # Save to memory and local CSV
        result_entry = [uid, name, roll, f"{score}%", user_ip]
        master_results.append(result_entry)

        with open('results.csv', mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(result_entry)
        
        submitted_ips.add(user_ip)
        
        return f"""
        <div style="font-family: sans-serif; padding: 40px; text-align: center;">
            <h1 style="color: #27ae60;">Grading Successful!</h1>
            <h2>Score: {score}%</h2>
            <img src="/{final_img_path}" width="500" style="border: 5px solid #2ecc71; border-radius: 10px;">
            <br><br><a href="/">Finish</a>
        </div>
        """
    return "No file uploaded", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)