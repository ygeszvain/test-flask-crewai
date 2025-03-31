import os
import requests
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Azure Credentials
AZURE_FACE_API_KEY = os.getenv("AZURE_FACE_API_KEY")
AZURE_FACE_ENDPOINT = os.getenv("AZURE_FACE_ENDPOINT")
AZURE_DOCUMENT_INTELLIGENCE_URL = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_URL")
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
AZURE_BLOB_CONNECTION_STRING = os.getenv("AZURE_BLOB_CONNECTION_STRING")
CONTAINER_NAME = "face-verification"

# Initialize Azure Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)


def upload_to_blob(image_data, file_name):
    """Uploads image data to Azure Blob Storage and returns the URL."""
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file_name)
    blob_client.upload_blob(image_data, overwrite=True)
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{file_name}"


def extract_face_from_license(image_url):
    """Calls Azure Document Intelligence API to extract the face from the driver's license."""
    headers = {"Ocp-Apim-Subscription-Key": AZURE_DOCUMENT_INTELLIGENCE_KEY}
    json_data = {"urlSource": image_url}

    response = requests.post(AZURE_DOCUMENT_INTELLIGENCE_URL, headers=headers, json=json_data)
    response.raise_for_status()
    data = response.json()

    # Extracting the face image URL (assuming Azure Document Intelligence returns it)
    return data.get("face_image_url")


def compare_faces(face1_url, face2_url):
    """Calls Azure Face API to compare two faces and return similarity score."""
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_FACE_API_KEY,
        "Content-Type": "application/json",
    }
    json_data = {"url1": face1_url, "url2": face2_url}

    response = requests.post(f"{AZURE_FACE_ENDPOINT}/face/v1.0/verify", headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


@app.route("/verify", methods=["POST"])
def verify_identity():
    """Handles driver’s license and live image verification."""
    if "license" not in request.files or "webcam" not in request.files:
        return jsonify({"error": "Both driver's license and webcam images are required"}), 400

    license_file = request.files["license"]
    webcam_file = request.files["webcam"]

    # Upload images to Blob Storage
    license_url = upload_to_blob(license_file.read(), f"license_{license_file.filename}")
    webcam_url = upload_to_blob(webcam_file.read(), f"webcam_{webcam_file.filename}")

    # Extract face from driver's license
    extracted_face_url = extract_face_from_license(license_url)
    if not extracted_face_url:
        return jsonify({"error": "Failed to extract face from driver's license"}), 500

    # Compare faces
    comparison_result = compare_faces(extracted_face_url, webcam_url)

    return jsonify({"match": comparison_result.get("isIdentical"), "confidence": comparison_result.get("confidence")})


if __name__ == "__main__":
    app.run(debug=True)
