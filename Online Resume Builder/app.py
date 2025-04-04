from flask import Flask, render_template, request, redirect, url_for, session, send_file
import mysql.connector
import os
from werkzeug.utils import secure_filename
from fpdf import FPDF
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Tekina11",
    database="resume_builder"
)
cursor = db.cursor()

# Welcome Page
@app.route('/')
def home():
    return render_template('welcome.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        if user:
            session['email'] = email
            return redirect(url_for('resume_form'))
    return render_template('login.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Resume Form
@app.route('/resume_form', methods=['GET', 'POST'])
def resume_form():
    if request.method == 'POST':
        data = {field: request.form[field] for field in request.form}
        linkedin = data['linkedin']
        github = data['github']

        if not re.match(r'https://(www\.)?linkedin\.com/in/.+', linkedin):
            return 'Invalid LinkedIn URL'
        if not re.match(r'https://(www\.)?github\.com/.+', github):
            return 'Invalid GitHub URL'

        cert_file = request.files['certificate']
        cert_filename = secure_filename(cert_file.filename)
        cert_path = os.path.join(app.config['UPLOAD_FOLDER'], cert_filename)
        cert_file.save(cert_path)

        cursor.execute("""
        INSERT INTO resumes (name, contact, email, objective, education, skills, experience, activities,
            achievements, projects, certificate_path, linkedin, github, template)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['name'], data['contact'], data['email'], data['objective'], data['education'],
            data['skills'], data['experience'], data['activities'], data['achievements'],
            data['projects'], cert_path, data['linkedin'], data['github'], data['template']
        ))
        db.commit()
        session['resume_data'] = data
        session['cert_path'] = cert_path
        return render_template(f"resume_templates/{data['template']}.html", data=data, cert_path=cert_path)
    return render_template('resume_form.html')

# Download PDF
@app.route('/download')
def download():
    data = session.get('resume_data')
    cert_path = session.get('cert_path')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key.capitalize()}: {value}", ln=True)
    pdf.output("static/resume.pdf")
    return send_file("static/resume.pdf", as_attachment=True)

# Exit to Home
@app.route('/exit')
def exit():
    session.clear()
    return redirect(url_for('home'))

# Run Server
if __name__ == '__main__':
    app.run(debug=True)