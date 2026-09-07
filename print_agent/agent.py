"""
Print Agent - runs on MacBook to manage printing via CUPS.

This agent:
- Connects to VPS server
- Receives print jobs
- Manages CUPS queue
- Reports printer status
- Handles errors (paper out, jam, ink)
"""
import asyncio
import logging
import os
import subprocess
import platform
from typing import Optional, Dict, Any
from datetime import datetime
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrintAgent:
    """Print Agent for macOS + CUPS + Canon G3020."""
    
    def __init__(
        self,
        server_url: str,
        agent_id: str,
        secret_key: str,
        printer_name: str = "Canon_G3020",
    ):
        self.server_url = server_url.rstrip("/")
        self.agent_id = agent_id
        self.secret_key = secret_key
        self.printer_name = printer_name
        self.running = False
        self.last_heartbeat = None
        self.current_job_id: Optional[int] = None
        self.processed_jobs: set = set()  # Idempotency tracking
    
    async def start(self):
        """Start the print agent."""
        logger.info(f"Starting Print Agent {self.agent_id}")
        logger.info(f"Server: {self.server_url}")
        logger.info(f"Printer: {self.printer_name}")
        
        # Verify system
        if not await self.verify_system():
            logger.error("System verification failed")
            return
        
        # Register with server
        if not await self.register():
            logger.error("Registration failed")
            return
        
        self.running = True
        
        # Start main loop
        await self.run_loop()
    
    async def verify_system(self) -> bool:
        """Verify running on macOS with CUPS."""
        system = platform.system()
        if system != "Darwin":
            logger.warning(f"Running on {system}, expected Darwin (macOS)")
        
        # Check CUPS
        try:
            result = subprocess.run(
                ["lpstat", "-p"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.error("CUPS not available")
                return False
            
            logger.info("CUPS available")
            return True
        except Exception as e:
            logger.error(f"CUPS check failed: {e}")
            return False
    
    async def register(self) -> bool:
        """Register agent with server."""
        payload = {
            "agent_id": self.agent_id,
            "hostname": platform.node(),
            "system": platform.system(),
            "printer": self.printer_name,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/agents/register",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.secret_key}"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        logger.info("Registered successfully")
                        return True
                    else:
                        logger.error(f"Registration failed: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    async def send_heartbeat(self, session: aiohttp.ClientSession):
        """Send heartbeat to server."""
        status = await self.get_printer_status()
        
        payload = {
            "agent_id": self.agent_id,
            "status": status["status"],
            "printer_status": status["printer_status"],
            "current_job": self.current_job_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            async with session.post(
                f"{self.server_url}/api/agents/heartbeat",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret_key}"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    self.last_heartbeat = datetime.utcnow()
        except Exception as e:
            logger.debug(f"Heartbeat error: {e}")
    
    async def get_printer_status(self) -> Dict[str, Any]:
        """Get current printer status via CUPS."""
        status = {
            "status": "unknown",
            "printer_status": "unknown",
            "queue_length": 0,
            "error": None,
        }
        
        try:
            # Get printer status
            result = subprocess.run(
                ["lpstat", "-p", self.printer_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if "enabled" in output and "idle" in output:
                    status["printer_status"] = "ready"
                    status["status"] = "online"
                elif "enabled" in output and "printing" in output:
                    status["printer_status"] = "printing"
                    status["status"] = "online"
                elif "disabled" in output:
                    status["printer_status"] = "offline"
                    status["status"] = "offline"
                else:
                    status["printer_status"] = "unknown"
            else:
                status["printer_status"] = "not_found"
                status["status"] = "offline"
            
            # Get queue length
            result = subprocess.run(
                ["lpq", "-P", self.printer_name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if l.strip()]
                status["queue_length"] = max(0, len(lines) - 2)  # Subtract header/footer
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            status["error"] = str(e)
        
        return status
    
    async def fetch_job(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """Fetch next print job from server."""
        try:
            async with session.get(
                f"{self.server_url}/api/jobs/fetch",
                params={"agent_id": self.agent_id},
                headers={"Authorization": f"Bearer {self.secret_key}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("job")
                elif resp.status == 204:
                    return None  # No jobs available
                else:
                    logger.error(f"Fetch job failed: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Fetch job error: {e}")
            return None
    
    async def process_job(self, job: Dict[str, Any]):
        """Process a print job."""
        job_id = job["id"]
        
        # Idempotency check
        if job_id in self.processed_jobs:
            logger.info(f"Job {job_id} already processed, skipping")
            return
        
        self.current_job_id = job_id
        logger.info(f"Processing job {job_id}")
        
        try:
            # Download PDF
            pdf_path = await self.download_job_file(job)
            
            # Print via CUPS
            success = await self.print_file(pdf_path, job)
            
            if success:
                await self.report_job_complete(job_id)
                self.processed_jobs.add(job_id)
            else:
                await self.report_job_error(job_id, "Print failed")
                
        except Exception as e:
            logger.error(f"Job {job_id} error: {e}")
            await self.report_job_error(job_id, str(e))
        
        finally:
            self.current_job_id = None
    
    async def download_job_file(self, job: Dict[str, Any]) -> str:
        """Download print job file."""
        async with aiohttp.ClientSession() as session:
            url = job.get("file_url") or f"{self.server_url}/files/{job['id']}.pdf"
            
            async with session.get(
                url,
                headers={"Authorization": f"Bearer {self.secret_key}"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to download file: {resp.status}")
                
                pdf_path = f"/tmp/job_{job['id']}.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(await resp.read())
                
                return pdf_path
    
    async def print_file(self, pdf_path: str, job: Dict[str, Any]) -> bool:
        """Print file via CUPS."""
        copies = job.get("copies", 1)
        
        cmd = [
            "lp",
            "-d", self.printer_name,
            "-n", str(copies),
            pdf_path,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0:
                logger.info(f"Print job submitted: {result.stdout}")
                return True
            else:
                logger.error(f"Print failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Print timed out")
            return False
        except Exception as e:
            logger.error(f"Print error: {e}")
            return False
    
    async def report_job_complete(self, job_id: int):
        """Report job completion to server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/jobs/{job_id}/complete",
                    headers={"Authorization": f"Bearer {self.secret_key}"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Job {job_id} reported complete")
        except Exception as e:
            logger.error(f"Report complete error: {e}")
    
    async def report_job_error(self, job_id: int, error: str):
        """Report job error to server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/api/jobs/{job_id}/error",
                    json={"error": error},
                    headers={"Authorization": f"Bearer {self.secret_key}"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Job {job_id} reported error: {error}")
        except Exception as e:
            logger.error(f"Report error error: {e}")
    
    async def run_loop(self):
        """Main agent loop."""
        async with aiohttp.ClientSession() as session:
            heartbeat_interval = 30  # seconds
            last_heartbeat = 0
            
            while self.running:
                now = datetime.utcnow().timestamp()
                
                # Send heartbeat
                if now - last_heartbeat >= heartbeat_interval:
                    await self.send_heartbeat(session)
                    last_heartbeat = now
                
                # Fetch and process job
                if not self.current_job_id:
                    job = await self.fetch_job(session)
                    if job:
                        await self.process_job(job)
                    else:
                        await asyncio.sleep(5)  # Wait before next poll
                else:
                    await asyncio.sleep(2)  # Wait for current job
    
    def stop(self):
        """Stop the agent."""
        logger.info("Stopping agent...")
        self.running = False


async def main():
    """Main entry point."""
    agent = PrintAgent(
        server_url=os.getenv("SERVER_URL", "http://localhost:8000"),
        agent_id=os.getenv("AGENT_ID", "agent_001"),
        secret_key=os.getenv("AGENT_SECRET", "secret_key"),
        printer_name=os.getenv("PRINTER_NAME", "Canon_G3020"),
    )
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
