from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from email.message import EmailMessage
from dotenv import load_dotenv
from docx2pdf import convert
import json
import os
import smtplib

# Load reviewer email mappings
REVIEWER_FILE = 'reviewers.json'
if os.path.exists(REVIEWER_FILE):
    with open(REVIEWER_FILE, 'r') as f:
        REVIEWERS = json.load(f)
else:
    REVIEWERS = {}

# Folder setup
PDFS = 'uploads/pdfs'
ORIGINALS = 'uploads/originals'
DRAFTS = 'uploads/drafts'

os.makedirs(PDFS, exist_ok=True)
os.makedirs(ORIGINALS, exist_ok=True)
os.makedirs(DRAFTS, exist_ok=True)

# Flask setup
app = Flask(__name__)
CORS(app)
load_dotenv()

# Email setup
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

@app.route('/send-review', methods=['POST'])
def send_review():
    if 'files' not in request.files or 'email' not in request.form:
        return jsonify({'error': 'Missing files or email'}), 400

    files = request.files.getlist('files')
    reviewer_email = request.form['email']

    for file in files:
        filename = file.filename
        original_path = os.path.join(ORIGINALS, filename)
        file.save(original_path)

        REVIEWERS[filename] = reviewer_email

        msg = EmailMessage()
        msg['Subject'] = 'Please review the document'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = reviewer_email
        msg.set_content("Kindly review the attached document and reply.")

        with open(original_path, 'rb') as f:
             msg.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=filename)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
        except Exception as e:
            print(f"Failed to send email for {filename}: {e}")

    with open(REVIEWER_FILE, 'w') as f:
        json.dump(REVIEWERS, f)

    return jsonify({'message': 'All files sent for review!'}), 200


@app.route('/upload-draft', methods=['POST'])
def upload_draft():
    if 'file' not in request.files:
        return jsonify({'error': 'Missing file'}), 400

    file = request.files['file']
    filename = file.filename
    file.save(os.path.join(DRAFTS, filename))
    return jsonify({'message': 'Draft uploaded successfully!'}), 200

@app.route('/files', methods=['GET'])
def list_files():
    originals = os.listdir(ORIGINALS)
    drafts = os.listdir(DRAFTS)
    files = []

    for file in originals:
        files.append({
            'filename': file,
            'hasDraft': file in drafts,
            'approved': file not in drafts
        })
    return jsonify(files)

@app.route('/approve', methods=['POST'])
def approve_draft():
    data = request.json
    filename = data['filename']
    draft_path = os.path.join(DRAFTS, filename)
    original_path = os.path.join(ORIGINALS, filename)

    if not os.path.exists(draft_path):
        return jsonify({'error': 'Draft not found'}), 404

    os.replace(draft_path, original_path)
    return jsonify({'message': 'Draft approved and original file replaced'}), 200

@app.route('/download/<filetype>/<filename>', methods=['GET'])
def download_file(filetype, filename):
    folder = ORIGINALS if filetype == 'original' else DRAFTS
    return send_from_directory(folder, filename)

@app.route('/convert-pdf', methods=['POST'])
def convert_to_pdf():
    data = request.json
    filename = data.get('filename')
    original_path = os.path.join(ORIGINALS, filename)

    if not os.path.exists(original_path):
        return jsonify({'error': 'Original file not found'}), 404

    try:
        convert(original_path, PDFS)
        pdf_name = filename.rsplit('.', 1)[0] + ".pdf"
        print(f"Converted PDF saved at {os.path.join(PDFS, pdf_name)}")
        return jsonify({'message': 'Converted to PDF!', 'pdf': pdf_name}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'PDF conversion failed'}), 500

@app.route('/download/pdf/<filename>', methods=['GET'])
def download_pdf(filename):
    return send_from_directory(PDFS, filename)

@app.route('/send-final-policy', methods=['POST'])
def send_final_policy():
    data = request.json
    filename = data.get('filename')
    pdf_name = filename.rsplit('.', 1)[0] + '.pdf'
    pdf_path = os.path.join(PDFS, pdf_name)

    if not os.path.exists(pdf_path):
        return jsonify({'error': 'PDF not found'}), 404

    recipient = REVIEWERS.get(filename)
    if not recipient:
        return jsonify({'error': 'Reviewer email not found'}), 404

    msg = EmailMessage()
    msg['Subject'] = 'Final Policy Document'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient
    msg.set_content("Please find attached the final approved policy document in PDF format.")

    with open(pdf_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=pdf_name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return jsonify({'message': 'Final policy sent successfully!'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Failed to send final policy'}), 500

if __name__ == '__main__':
    app.run(debug=True)
