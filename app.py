from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential
import os
import base64



credential = DefaultAzureCredential()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Azure Storage Configuration
AZURE_CONNECTION_STRING = "https://teststorage0008.blob.core.windows.net/pycontainer?sp=racwdl&st=2025-03-17T06:00:47Z&se=2025-03-17T14:00:47Z&sv=2022-11-02&sr=c&sig=jh5ApfP%2BLs5%2BtlkR%2BFRbjYP52CqcoJncsdIr388SFaI%3D"
sas_token = "sp=racwdl&st=2025-03-17T06:00:47Z&se=2025-03-17T14:00:47Z&sv=2022-11-02&sr=c&sig=jh5ApfP%2BLs5%2BtlkR%2BFRbjYP52CqcoJncsdIr388SFaI%3D"
# Replace with your Azure Storage connection string
CONTAINER_NAME = "pycontainer"  # Replace with your Blob container name

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient(account_url=AZURE_CONNECTION_STRING, credential=sas_token)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)

# Utility function to check allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple mock-up for login logic
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "password":
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials. Please try again.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                # Upload to Azure Blob Storage
                blob_client = container_client.get_blob_client(filename)
                blob_client.upload_blob(filename, overwrite=True)
                flash('File uploaded successfully to Azure Blob Storage!')
                return redirect(url_for('upload'))
            except Exception as e:
                flash(f'Error uploading file: {e}')
        else:
            flash('Allowed file types are: txt, pdf, png, jpg, jpeg, gif')

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
