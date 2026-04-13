# db.py
import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

# Initialize Firebase App
def init_firebase():
    if not firebase_admin._apps:
        # Check if the credentials file exists
        # In a real environment, you'd use an environment variable for the cert path
        # or load from a secrets manager. For this app we assume a local config or mock.
        # We will mock the database if no credentials are provided to allow the UI to run.
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase_key.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        else:
            print("Warning: Firebase credentials not found. Running in mock mode.")
            return MockFirestore()
    return firestore.client()

class MockFirestore:
    """A simple mock to allow the app to run without real Firebase credentials."""
    def __init__(self):
        self._storage_file = 'mock_db.json'
        if not os.path.exists(self._storage_file):
            with open(self._storage_file, 'w') as f:
                json.dump({"costeos": {}}, f)

    def collection(self, name):
        return MockCollection(name, self._storage_file)

class MockCollection:
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path

    def document(self, doc_id=None):
        return MockDocument(self.name, doc_id, self.file_path)

    def stream(self):
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        docs = []
        for k, v in data.get(self.name, {}).items():
            doc = MockDocumentSnapshot(k, v)
            docs.append(doc)
        return docs

class MockDocumentSnapshot:
    def __init__(self, id, data):
        self.id = id
        self._data = data
    def to_dict(self):
        return self._data

class MockDocument:
    def __init__(self, coll_name, doc_id, file_path):
        self.coll_name = coll_name
        self.id = doc_id if doc_id else str(datetime.now().timestamp())
        self.file_path = file_path

    def set(self, data):
        with open(self.file_path, 'r') as f:
            db_data = json.load(f)
        if self.coll_name not in db_data:
            db_data[self.coll_name] = {}
        # Ensure we don't save datetime objects directly in JSON mock
        data['id'] = self.id
        db_data[self.coll_name][self.id] = data
        with open(self.file_path, 'w') as f:
            json.dump(db_data, f, indent=4)

db = init_firebase()

class CosteosDB:
    COLLECTION_NAME = "costeos"

    @staticmethod
    def save_costeo(costeo_data: dict, doc_id: str = None) -> str:
        """
        Guarda o actualiza un documento de costeo en Firestore.
        Si no se proporciona doc_id, se crea un nuevo documento.
        """
        costeo_data['fecha_actualizacion'] = datetime.now().isoformat()

        if doc_id:
            doc_ref = db.collection(CosteosDB.COLLECTION_NAME).document(doc_id)
            doc_ref.set(costeo_data)
            return doc_id
        else:
            costeo_data['fecha_creacion'] = datetime.now().isoformat()
            # If using real firestore, this generates an ID. Our mock does too.
            doc_ref = db.collection(CosteosDB.COLLECTION_NAME).document()
            doc_ref.set(costeo_data)
            return doc_ref.id

    @staticmethod
    def get_all_costeos() -> list:
        """
        Recupera todos los documentos de costeo guardados.
        """
        costeos_ref = db.collection(CosteosDB.COLLECTION_NAME)
        docs = costeos_ref.stream()

        costeos = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            costeos.append(data)

        return costeos
