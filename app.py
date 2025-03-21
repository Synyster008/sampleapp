from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.storage.fileshare import ShareFileClient, ShareDirectoryClient
from azure.identity import DefaultAzureCredential
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,  # Set the log level to DEBUG for more detailed logs
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # Create a logger object for this module
# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Azure Storage Configuration
AZURE_CONNECTION_STRING = "https://teststorage0008.blob.core.windows.net/pycontainer?sp=racwdl&st=2025-03-18T07:18:56Z&se=2025-03-20T15:18:56Z&sv=2022-11-02&sr=c&sig=31C2Kby8M1j0hrDt2Fh6XwEgztYKGTCt5DtVrJ6Q66E%3D"
sas_token = "sp=racwdl&st=2025-03-18T07:18:56Z&se=2025-03-20T15:18:56Z&sv=2022-11-02&sr=c&sig=31C2Kby8M1j0hrDt2Fh6XwEgztYKGTCt5DtVrJ6Q66E%3D"
CONTAINER_NAME = "pycontainer"  # Blob container name
AZURE_FILE_STRING = "DefaultEndpointsProtocol=https;AccountName=teststorage0008;AccountKey=DkQdvs9p9DE65dYW2Cjc052+yiIVmjZFKTQ6K8endl4DWNUyFpDInnZ1Gye8k3r8vyhpEtdfQw8C+ASt7Crkdg==;EndpointSuffix=core.windows.net"
# Initialize BlobServiceClient and FileShareClient
blob_service_client = BlobServiceClient(account_url=AZURE_CONNECTION_STRING, credential=sas_token)
container_client = blob_service_client.get_container_client(CONTAINER_NAME)
file_share_client = ShareFileClient.from_connection_string(AZURE_FILE_STRING, share_name='sharedfiles', file_path='/')  # Replace 'yourfileshare' with your file share name
get_directory_client = ShareDirectoryClient.from_connection_string(AZURE_FILE_STRING, share_name='sharedfiles', directory_path= '')
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
                blob_client.upload_blob(file.read(), overwrite=True)
                flash('File uploaded successfully to Azure Blob Storage!')
                return redirect(url_for('upload'))
            except Exception as e:
                flash(f'Error uploading file: {e}')
        else:
            flash('Allowed file types are: txt, pdf, png, jpg, jpeg, gif')

    # List files from Azure File Share
    file_list = []
    try:

        file_list = get_directory_client.list_directories_and_files()
        files = [file['name'] for file in file_list]  # Extract file names

        logger.info(f"Retrieved file list from Azure File Share: {files}")


    except Exception as e:
        flash(f'Error retrieving file list: {e}')

    return render_template('upload.html', files=files)


@app.route('/download/<filename>')
def download(filename):
    try:
        # Get the file from Azure File Share
        file_client = get_directory_client.get_file_client(filename)
        download_stream = file_client.download_file()

        # Create a temporary file path to store the file temporarily
        temp_file_path = os.path.join(os.getcwd(), filename)
        with open(temp_file_path, 'wb') as f:
            f.write(download_stream.readall())

        # Send the file to the client
        return send_file(temp_file_path, as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {e}')
        return redirect(url_for('upload'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
