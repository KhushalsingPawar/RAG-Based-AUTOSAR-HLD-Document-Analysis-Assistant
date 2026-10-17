import requests
from typing import Dict, Any, List, Optional

BACKEND_URL = "http://127.0.0.1:8000/api"


class APIClient:
    def __init__(self, base_url: str = BACKEND_URL, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token  # JWT Bearer token set after login

    def _headers(self) -> Dict[str, str]:
        """Return Authorization header if a token is set."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    # ── Auth ─────────────────────────────────────────────────────────────────
    def register(self, username: str, password: str, full_name: str = "") -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "password": password, "full_name": full_name},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Returns dict with access_token on success, or detail on failure."""
        try:
            r = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": username, "password": password},
                timeout=10,
            )
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    def get_me(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/auth/me", headers=self._headers(), timeout=5)
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    # ── System Health ────────────────────────────────────────────────────────
    def get_health(self) -> Dict[str, Any]:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=3)
            return r.json() if r.status_code == 200 else {"status": "Error", "detail": r.text}
        except Exception as e:
            return {"status": "Backend Offline", "detail": str(e)}

    # ── Projects ─────────────────────────────────────────────────────────────
    def get_projects(self) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.base_url}/projects", headers=self._headers(), timeout=5)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def create_project(self, name: str, vehicle_program: str, description: str) -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/projects",
                headers=self._headers(),
                json={"name": name, "vehicle_program": vehicle_program, "description": description},
                timeout=5,
            )
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    # ── Documents ────────────────────────────────────────────────────────────
    def get_documents(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"project_id": project_id} if project_id else {}
        try:
            r = requests.get(f"{self.base_url}/documents", headers=self._headers(), params=params, timeout=5)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def get_document_chunks(self, document_id: int) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.base_url}/documents/{document_id}/chunks", headers=self._headers(), timeout=5)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def delete_document(self, document_id: int) -> Dict[str, Any]:
        try:
            r = requests.delete(f"{self.base_url}/documents/{document_id}", headers=self._headers(), timeout=10)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    # ── Upload & Ingestion ───────────────────────────────────────────────────
    def upload_pdf(self, file_bytes: bytes, filename: str, project_id: int, version: str) -> Dict[str, Any]:
        try:
            files = {"file": (filename, file_bytes, "application/pdf")}
            data = {"project_id": project_id, "version": version}
            r = requests.post(f"{self.base_url}/upload", headers=self._headers(), files=files, data=data, timeout=60)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    def load_sample_hld(self, sample_name: str, project_id: int, version: str) -> Dict[str, Any]:
        try:
            data = {"sample_name": sample_name, "project_id": project_id, "version": version}
            r = requests.post(f"{self.base_url}/upload/sample", headers=self._headers(), data=data, timeout=60)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    # ── RAG Query ────────────────────────────────────────────────────────────
    def query_rag(self, question: str, project_id: Optional[int], document_id: Optional[int], top_k: int = 4) -> Dict[str, Any]:
        try:
            payload = {
                "question": question,
                "project_id": project_id,
                "document_id": document_id,
                "top_k": top_k,
            }
            r = requests.post(f"{self.base_url}/query", headers=self._headers(), json=payload, timeout=90)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    # ── Architecture Entities ────────────────────────────────────────────────
    def get_entities(
        self,
        document_id: Optional[int] = None,
        project_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params = {}
        if document_id:
            params["document_id"] = document_id
        if project_id:
            params["project_id"] = project_id
        if entity_type:
            params["entity_type"] = entity_type
        if search:
            params["search"] = search
        try:
            r = requests.get(f"{self.base_url}/entities", headers=self._headers(), params=params, timeout=5)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    # ── Comparison & Validation ──────────────────────────────────────────────
    def compare_revisions(self, doc_a_id: int, doc_b_id: int) -> Dict[str, Any]:
        try:
            payload = {"doc_a_id": doc_a_id, "doc_b_id": doc_b_id}
            r = requests.post(f"{self.base_url}/compare", headers=self._headers(), json=payload, timeout=15)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}

    def validate_document(self, document_id: int) -> Dict[str, Any]:
        try:
            params = {"document_id": document_id}
            r = requests.post(f"{self.base_url}/validate", headers=self._headers(), params=params, timeout=15)
            return r.json()
        except Exception as e:
            return {"detail": str(e)}


client = APIClient()
