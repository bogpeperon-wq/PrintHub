"""
Document Processor - handles file analysis and conversion.
"""
import os
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from abc import ABC, abstractmethod

import fitz  # PyMuPDF
from PIL import Image


class DocumentProcessingError(Exception):
    """Error during document processing."""
    pass


class DocumentProcessor(ABC):
    """Abstract base class for document processors."""
    
    @abstractmethod
    async def get_page_count(self, file_path: str) -> int:
        """Get number of pages in document."""
        pass
    
    @abstractmethod
    async def can_process(self, mime_type: str, filename: str) -> bool:
        """Check if this processor can handle the file."""
        pass
    
    @abstractmethod
    async def convert_to_pdf(self, file_path: str, output_path: str) -> str:
        """Convert document to PDF, return output path."""
        pass


class PDFProcessor(DocumentProcessor):
    """Processor for PDF files."""
    
    async def get_page_count(self, file_path: str) -> int:
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            raise DocumentProcessingError(f"Failed to read PDF: {e}")
    
    async def can_process(self, mime_type: str, filename: str) -> bool:
        return mime_type == "application/pdf" or filename.lower().endswith(".pdf")
    
    async def convert_to_pdf(self, file_path: str, output_path: str) -> str:
        # Already PDF, just copy
        import shutil
        shutil.copy2(file_path, output_path)
        return output_path


class ImageProcessor(DocumentProcessor):
    """Processor for image files (JPG, PNG)."""
    
    SUPPORTED_MIMES = {"image/jpeg", "image/png", "image/jpg"}
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    
    async def get_page_count(self, file_path: str) -> int:
        # Each image is one page
        return 1
    
    async def can_process(self, mime_type: str, filename: str) -> bool:
        if mime_type in self.SUPPORTED_MIMES:
            return True
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    async def convert_to_pdf(self, file_path: str, output_path: str) -> str:
        try:
            # Open image and convert to PDF
            img = Image.open(file_path)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Save as PDF
            img.save(output_path, "PDF", resolution=100.0)
            return output_path
        except Exception as e:
            raise DocumentProcessingError(f"Failed to convert image to PDF: {e}")


class OfficeProcessor(DocumentProcessor):
    """
    Processor for Office documents (DOC, DOCX).
    
    NOTE: Requires LibreOffice installed on the system.
    Fallback: Return error if LibreOffice not available.
    """
    
    SUPPORTED_MIMES = {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    SUPPORTED_EXTENSIONS = {".doc", ".docx"}
    
    async def get_page_count(self, file_path: str) -> int:
        # For Office docs, we need to convert first then count
        # This will be called after conversion
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            await self.convert_to_pdf(file_path, tmp_path)
            doc = fitz.open(tmp_path)
            count = len(doc)
            doc.close()
            return count
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def can_process(self, mime_type: str, filename: str) -> bool:
        if mime_type in self.SUPPORTED_MIMES:
            return True
        ext = Path(filename).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    async def convert_to_pdf(self, file_path: str, output_path: str) -> str:
        """Convert Office document to PDF using LibreOffice."""
        import subprocess
        
        try:
            # Use LibreOffice headless conversion
            cmd = [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", os.path.dirname(output_path),
                file_path,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            if result.returncode != 0:
                raise DocumentProcessingError(
                    f"LibreOffice conversion failed: {result.stderr}"
                )
            
            # LibreOffice creates file with same name but .pdf extension
            expected_path = os.path.splitext(file_path)[0] + ".pdf"
            if os.path.exists(expected_path):
                os.rename(expected_path, output_path)
            
            if not os.path.exists(output_path):
                raise DocumentProcessingError("Conversion completed but output file not found")
            
            return output_path
            
        except FileNotFoundError:
            raise DocumentProcessingError(
                "LibreOffice not installed. Cannot process Office documents."
            )
        except subprocess.TimeoutExpired:
            raise DocumentProcessingError("Office document conversion timed out")


class DocumentProcessorService:
    """Main service for document processing."""
    
    def __init__(self):
        self.processors: list[DocumentProcessor] = [
            PDFProcessor(),
            ImageProcessor(),
            OfficeProcessor(),
        ]
    
    def get_processor(self, mime_type: str, filename: str) -> Optional[DocumentProcessor]:
        """Find appropriate processor for file."""
        for processor in self.processors:
            if asyncio_run(processor.can_process(mime_type, filename)):
                return processor
        return None
    
    async def analyze_file(
        self, 
        file_path: str, 
        mime_type: str, 
        filename: str
    ) -> Tuple[int, str]:
        """
        Analyze file and return page count and normalized PDF path.
        
        Returns:
            Tuple of (page_count, pdf_path)
        """
        processor = self.get_processor(mime_type, filename)
        if not processor:
            raise DocumentProcessingError(
                f"Unsupported file type: {mime_type} ({filename})"
            )
        
        # Get page count
        page_count = await processor.get_page_count(file_path)
        
        # Convert to PDF
        output_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        output_path = os.path.join(output_dir, f"{name_without_ext}_normalized.pdf")
        
        await processor.convert_to_pdf(file_path, output_path)
        
        return page_count, output_path
    
    async def create_service_page_pdf(
        self,
        username: str,
        filename: str,
        pages: int,
        copies: int,
        output_path: str,
    ) -> str:
        """Create a service page PDF with order information."""
        from datetime import datetime
        
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        
        # Add content
        title = "PRINT HUB"
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        text_content = f"""
        PRINT HUB
        ========================
        
        Пользователь: @{username}
        Дата: {date_str}
        
        Файл: {filename}
        Страниц: {pages}
        Копий: {copies}
        
        Всего физических страниц: {pages * copies + copies}
        (включая служебные страницы)
        
        ========================
        Спасибо за использование Print Hub!
        """
        
        # Insert text
        page.insert_text((50, 100), text_content, fontsize=12)
        
        # Save
        doc.save(output_path)
        doc.close()
        
        return output_path


# Helper for sync/async compatibility
def asyncio_run(coro):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
