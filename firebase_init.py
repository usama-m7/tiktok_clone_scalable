import firebase_admin
from firebase_admin import credentials, firestore, storage

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'tiktok-web-clone-79191.firebasestorage.app'
})

# Get Firestore client and Storage bucket
db = firestore.client()
bucket = storage.bucket()
