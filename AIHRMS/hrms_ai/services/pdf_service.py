"""
PDF Service - Extract text from PDF files
"""
import logging
import fitz  # PyMuPDF
from typing import Optional

logger = logging.getLogger(__name__)


class PDFService:
    """Service for extracting text from PDF files"""

    @staticmethod
    async def extract_text_from_pdf(file_content: bytes, filename: str) -> str:
        """
        Extract text from PDF file content.
        
        Args:
            file_content: Raw PDF file bytes
            filename: Original filename (for logging)
            
        Returns:
            Extracted text content as string
            
        Raises:
            ValueError: If PDF extraction fails
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=file_content, filetype="pdf")

            # Page Count
            page_count = len(doc)
            
            # Extract text from all pages
            text_content = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():  # Only add non-empty pages
                    text_content.append(text)
            
            doc.close()
            
            # Combine all pages
            full_text = "\n\n".join(text_content)
            
            if not full_text.strip():
                raise ValueError("PDF appears to be empty or contains no extractable text")
            
            logger.info(f"Successfully extracted {len(full_text)} characters from {filename} ({page_count} pages)")
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {filename}: {e}")
            raise ValueError(f"PDF extraction failed: {str(e)}")

    @staticmethod
    def validate_pdf(filename: str) -> bool:
        """Check if file has PDF extension"""
        return filename.lower().endswith('.pdf')
