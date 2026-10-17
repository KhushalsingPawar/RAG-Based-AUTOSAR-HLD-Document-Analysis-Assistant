import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from backend.app.config import settings
from backend.app.services.vector_store import vector_store


class RAGEngineService:
    """
    Retrieval-Augmented Generation (RAG) engine grounded in AUTOSAR HLD documents.
    Enforces strict source citations (Document, Section, Page number).
    """

    SYSTEM_PROMPT = """You are an expert AUTOSAR Automotive Systems Architecture Assistant.
Your task is to answer technical questions strictly using ONLY the provided High-Level Design (HLD) excerpts below.

GROUNDING RULES:
1. Every factual statement must cite the exact Section and Page number from the excerpts (e.g., "(Section 4.2, Page 2)").
2. Explicitly specify the Component, Port (Provide/Require), Interface, and Signal name wherever applicable.
3. If the provided context does not contain sufficient technical evidence to answer the question, state:
   "Insufficient architectural evidence in the provided HLD documentation."
4. Do not invent interfaces, data types, or connections not found in the context.
5. Be concise, rigorous, and technically precise.
"""

    def query(
        self,
        question: str,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None,
        allowed_document_ids: Optional[List[int]] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Retrieve top-k context chunks from ChromaDB
        citations = vector_store.search(
            query=question,
            project_id=project_id,
            document_id=document_id,
            allowed_document_ids=allowed_document_ids,
            top_k=top_k,
        )

        if not citations:
            return {
                "question": question,
                "answer": "No indexed HLD documentation found for this project or document. Please upload and index a PDF specification first.",
                "citations": [],
                "model_used": "None",
                "grounding_confidence": "Insufficient Evidence",
                "latency_seconds": round(time.time() - start_time, 3),
            }

        # 2. Assemble context with clear section and page tags
        context_blocks = []
        for idx, cit in enumerate(citations, 1):
            context_blocks.append(
                f"--- EXCERPT {idx} [Document: {cit['document_name']} (v{cit['version']}) | "
                f"Section: {cit['section_title']} | Page: {cit['page_number']}] ---\n"
                f"{cit['content']}\n"
            )
        combined_context = "\n".join(context_blocks)

        user_prompt = f"""CONTEXT EXCERPTS:
{combined_context}

QUESTION:
{question}

TECHNICAL ARCHITECTURE ANSWER (with explicit Section & Page citations):"""

        # 3. Call local Ollama LLM (llama3.2)
        llm_response, model_name = self._call_ollama(user_prompt)

        # 4. Determine grounding confidence
        grounding_confidence = "High"
        if "Insufficient architectural evidence" in llm_response:
            grounding_confidence = "Insufficient Evidence"
        elif citations[0]["score"] < 0.4:
            grounding_confidence = "Low"
        elif citations[0]["score"] < 0.65:
            grounding_confidence = "Medium"

        latency = round(time.time() - start_time, 2)

        return {
            "question": question,
            "answer": llm_response,
            "citations": citations,
            "model_used": model_name,
            "grounding_confidence": grounding_confidence,
            "latency_seconds": latency,
        }

    def _call_ollama(self, prompt: str) -> tuple[str, str]:
        endpoint = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": self.SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for deterministic engineering answers
                "top_p": 0.9,
            },
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=settings.OLLAMA_TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip(), settings.OLLAMA_MODEL
        except Exception as e:
            # Fallback to local heuristic answer generator when Ollama service is unavailable
            return self._heuristic_grounded_answer(prompt, str(e)), "Local Heuristic Fallback"

    def _heuristic_grounded_answer(self, prompt: str, error_msg: str) -> str:
        """
        Guarantees that queries still return cited engineering answers even if
        the Ollama service is temporarily unreachable or busy.
        """
        lines = prompt.splitlines()
        context_lines = [l for l in lines if not l.startswith("QUESTION:") and not l.startswith("TECHNICAL")]
        
        # Simple extraction of key relevant lines from excerpts
        relevant_excerpts = [l for l in context_lines if any(k in l.lower() for k in ["port", "interface", "signal", "swc", "received", "transmitted"])]
        
        fallback_text = (
            "**[Architectural Analysis (Local Fallback - Ollama connection notice: " + error_msg + ")]**\n\n"
            "Based on the indexed HLD document excerpts:\n"
        )
        if relevant_excerpts:
            fallback_text += "\n".join(f"- {line.strip()}" for line in relevant_excerpts[:6])
        else:
            fallback_text += "Refer to retrieved citations below for exact page and section references."
            
        return fallback_text


rag_engine = RAGEngineService()
