import logging
import os
from datetime import datetime

from supabase import Client, create_client

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

    def _upload_with_retry(self, bucket: str, path: str, file_bytes: bytes, content_type: str, max_retries: int = 3):
        import time
        for attempt in range(max_retries):
            try:
                self.supabase.storage.from_(bucket).upload(
                    path=path,
                    file=file_bytes,
                    file_options={"content-type": content_type}
                )
                return
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

    def complete_session(self, verdict: str, overall_score: float, payload_content: str = "", report_content: str = ""):
        """Finalizes the session and uploads the payload trace and formal report."""
        if not self.session_id:
            return

        payload_url = None
        if payload_content:
            try:
                # Format: user_id/session_id_trace.md
                file_path = f"{self.user_id}/{self.session_id}_trace.md"
                self._upload_with_retry("attack-artifacts", file_path, payload_content.encode('utf-8'), "text/markdown")
                payload_url = file_path 
            except Exception as e:
                logger.error(f"Failed to upload payload trace to Supabase: {e}")

        report_url = None
        html_report_url = None
        if report_content and not report_content.startswith("ERROR:"):
            try:
                # Format: user_id/session_id_report.md
                report_path = f"{self.user_id}/{self.session_id}_report.md"
                self._upload_with_retry("attack-artifacts", report_path, report_content.encode('utf-8'), "text/markdown")
                report_url = report_path
                
                # Convert to HTML and upload
                import re

                import markdown
                from jinja2 import Environment, FileSystemLoader
                
                html_content = markdown.markdown(
                    report_content,
                    extensions=['extra', 'fenced_code', 'tables']
                )
                
                html_content = re.sub(
                    r'<em>(Figure\b[^<]*)</em>',
                    r'<em class="figure-caption">\1</em>',
                    html_content
                )
                
                template_dir = ROOT_DIR / "backend" / "templates"
                env = Environment(loader=FileSystemLoader(str(template_dir)))
                template = env.get_template("report.html")
                rendered_html = template.render(content=html_content)
                
                html_report_path = f"{self.user_id}/{self.session_id}_report.html"
                self._upload_with_retry("attack-artifacts", html_report_path, rendered_html.encode('utf-8'), "text/html")
                html_report_url = html_report_path

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
            
        if html_report_url:
            # Update the HTML report URL if the column exists
            try:
                # Just add to update_data, if it fails below, we can catch it
                update_data["html_report_url"] = html_report_url
            except Exception:
                pass

        try:
            self.supabase.table("attack_sessions").update(update_data).eq("id", self.session_id).execute()
            logger.info(f"Supabase: Session {self.session_id} completed with verdict {verdict}")
        except Exception as e:
            if "html_report_url" in str(e):
                # Try again without html_report_url if the column doesn't exist
                update_data.pop("html_report_url", None)
                try:
                    self.supabase.table("attack_sessions").update(update_data).eq("id", self.session_id).execute()
                    logger.info(f"Supabase: Session {self.session_id} completed with verdict {verdict} (without html_report_url)")
                except Exception as e2:
                    logger.warning(f"Supabase complete_session failed: {e2}")
            else:
                logger.warning(f"Supabase complete_session failed: {e}")

    def upload_chart(self, chart_name: str, image_bytes: bytes) -> str:
        """Uploads a generated chart image to Supabase and returns the public URL."""
        if not self.session_id or not self.user_id:
            logger.warning("Cannot upload chart without an active session.")
            return ""
            
        file_path = f"{self.user_id}/{self.session_id}_{chart_name}.png"
        try:
            self._upload_with_retry("attack-charts", file_path, image_bytes, "image/png")
        except Exception as e:
            logger.error(f"Failed to upload chart {chart_name} to Supabase: {e}")
            
        # Always return the URL (even if it already existed and threw an error above)
        return self.supabase.storage.from_("attack-charts").get_public_url(file_path)
