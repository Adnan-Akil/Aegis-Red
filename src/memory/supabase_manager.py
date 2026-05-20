import os
import logging
from uuid import UUID
from datetime import datetime
from supabase import create_client, Client
from src.config import ROOT_DIR

logger = logging.getLogger(__name__)

class SupabaseManager:
    """
    Manages all interactions with the Supabase backend for session tracking, 
    logging, and artifact storage.
    """
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        
        self.supabase: Client = create_client(url, key)
        self.session_id: str | None = None
        self.user_id: str | None = None

    def create_session(self, user_id: str, target_name: str, target_url: str, target_type: str = "unknown") -> str:
        """Creates a new attack session in the database."""
        self.user_id = user_id
        data = {
            "user_id": user_id,
            "target_name": target_name,
            "target_url": target_url,
            "target_type": target_type,
            "status": "running",
        }
        try:
            response = self.supabase.table("attack_sessions").insert(data).execute()
            if response.data:
                self.session_id = response.data[0]["id"]
                logger.info(f"Supabase: Created session {self.session_id}")
                return self.session_id
        except Exception as e:
            logger.warning(f"Failed to create attack session in Supabase (likely invalid user_id). Proceeding locally. Error: {e}")
            import uuid
            self.session_id = str(uuid.uuid4())
            return self.session_id
        raise Exception("Failed to create attack session in Supabase")

    def add_log(self, event: str, description: str, log_type: str = "info"):
        """Adds an execution log entry for the current session."""
        if not self.session_id:
            return
        
        data = {
            "session_id": self.session_id,
            "event": event,
            "description": description,
            "type": log_type
        }
        try:
            self.supabase.table("execution_logs").insert(data).execute()
        except Exception as e:
            logger.warning(f"Supabase add_log failed: {e}")

    def add_finding(self, finding_type: str, extracted_value: str):
        """Adds a critical finding to the current session."""
        if not self.session_id:
            return
        
        data = {
            "session_id": self.session_id,
            "type": finding_type,
            "extracted_value": extracted_value
        }
        try:
            self.supabase.table("findings").insert(data).execute()
        except Exception as e:
            logger.warning(f"Supabase add_finding failed: {e}")

    def complete_session(self, verdict: str, overall_score: float, payload_content: str = "", report_content: str = ""):
        """Finalizes the session and uploads the payload trace and formal report."""
        if not self.session_id:
            return

        payload_url = None
        if payload_content:
            try:
                # Format: user_id/session_id_trace.md
                file_path = f"{self.user_id}/{self.session_id}_trace.md"
                self.supabase.storage.from_("attack-artifacts").upload(
                    path=file_path,
                    file=payload_content.encode('utf-8'),
                    file_options={"content-type": "text/markdown"}
                )
                payload_url = file_path 
            except Exception as e:
                logger.error(f"Failed to upload payload trace to Supabase: {e}")

        report_url = None
        if report_content and not report_content.startswith("ERROR:"):
            try:
                # Format: user_id/session_id_report.md
                report_path = f"{self.user_id}/{self.session_id}_report.md"
                self.supabase.storage.from_("attack-artifacts").upload(
                    path=report_path,
                    file=report_content.encode('utf-8'),
                    file_options={"content-type": "text/markdown"}
                )
                report_url = report_path
            except Exception as e:
                logger.error(f"Failed to upload formal report to Supabase: {e}")

        update_data = {
            "status": "completed",
            "verdict": verdict,
            "overall_score": overall_score,
            "updated_at": datetime.now().isoformat()
        }
        
        if payload_url:
            update_data["payload_file_url"] = payload_url
            
        if report_url:
            # Note: The 'report_file_url' column must exist in the attack_sessions table!
            update_data["report_file_url"] = report_url

        try:
            self.supabase.table("attack_sessions").update(update_data).eq("id", self.session_id).execute()
            logger.info(f"Supabase: Session {self.session_id} completed with verdict {verdict}")
        except Exception as e:
            logger.warning(f"Supabase complete_session failed: {e}")
