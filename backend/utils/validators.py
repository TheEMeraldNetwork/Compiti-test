"""
Content Validators for Automated Math Solver
FOR TESTING PURPOSES ONLY

Validates mathematical content and implements security guardrails
to ensure only appropriate mathematical problems are processed.
"""

import os
import re
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import mimetypes

import pytesseract
from PIL import Image
import PyPDF2
from loguru import logger


class ContentValidator:
    """
    Validates content to ensure it's mathematical in nature and safe to process.
    
    Implements security guardrails and content filtering.
    """
    
    def __init__(self):
        """Initialize content validator with mathematical keywords."""
        self.mathematical_keywords = [
            # Basic math terms
            'solve', 'equation', 'calculate', 'find', 'prove', 'show',
            'determine', 'compute', 'evaluate', 'simplify',
            
            # Algebra
            'algebra', 'polynomial', 'quadratic', 'linear', 'variable',
            'coefficient', 'factor', 'expand', 'expression',
            
            # Calculus
            'calculus', 'derivative', 'integral', 'limit', 'continuity',
            'differentiate', 'integrate', 'optimization', 'chain rule',
            
            # Geometry
            'geometry', 'triangle', 'circle', 'angle', 'area', 'volume',
            'perimeter', 'theorem', 'proof', 'coordinate', 'vector',
            
            # Trigonometry
            'trigonometry', 'sin', 'cos', 'tan', 'sine', 'cosine', 'tangent',
            'radian', 'degree', 'amplitude', 'period', 'frequency',
            
            # Statistics and Probability
            'statistics', 'probability', 'mean', 'median', 'mode', 'variance',
            'standard deviation', 'distribution', 'sample', 'population',
            'correlation', 'regression', 'hypothesis',
            
            # Advanced math
            'matrix', 'determinant', 'eigenvalue', 'eigenvector', 'linear algebra',
            'differential equation', 'partial derivative', 'series', 'sequence',
            'convergence', 'divergence', 'fourier', 'laplace',
            
            # Mathematical symbols and operations
            '∫', '∑', '∏', '∂', '∇', '∆', 'lim', 'max', 'min', 'log', 'ln',
            '√', '∞', '≤', '≥', '≠', '≈', '∈', '∉', '⊂', '⊆', '∪', '∩',
            
            # Units and measurements
            'meter', 'centimeter', 'kilometer', 'gram', 'kilogram', 'second',
            'minute', 'hour', 'degree celsius', 'fahrenheit', 'kelvin'
        ]
        
        # Extended list for Italian mathematical terms
        self.italian_math_keywords = [
            'risolvere', 'equazione', 'calcolare', 'trovare', 'dimostrare',
            'determinare', 'semplificare', 'algebra', 'geometria', 'calcolo',
            'derivata', 'integrale', 'limite', 'funzione', 'grafico',
            'triangolo', 'cerchio', 'angolo', 'area', 'volume', 'perimetro',
            'statistica', 'probabilità', 'media', 'mediana', 'varianza',
            'matrice', 'determinante', 'vettore', 'polinomio', 'radice'
        ]
        
        self.all_keywords = self.mathematical_keywords + self.italian_math_keywords
        
        # Forbidden topics/keywords that should not be processed
        self.forbidden_keywords = [
            'hack', 'crack', 'exploit', 'malware', 'virus', 'password',
            'personal', 'private', 'confidential', 'secret', 'illegal',
            'violence', 'weapon', 'drug', 'adult', 'explicit'
        ]
        
        # Supported file types
        self.supported_image_types = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        self.supported_text_types = ['.txt', '.md', '.tex']
        self.supported_pdf_types = ['.pdf']
        
    def validate_mathematical_content(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if file contains mathematical content.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if file_size > 50:  # 50MB limit
                return False, f"File too large: {file_size:.1f}MB (max 50MB)"
            
            # Get file extension
            file_ext = Path(file_path).suffix.lower()
            
            # Extract text content based on file type
            text_content = self._extract_text_content(file_path, file_ext)
            if not text_content:
                return False, "Could not extract text content from file"
            
            # Check for forbidden content
            if self._contains_forbidden_content(text_content):
                return False, "File contains inappropriate content"
            
            # Check for mathematical content
            math_score = self._calculate_mathematical_score(text_content)
            
            if math_score < 0.1:  # Minimum 10% mathematical content
                return False, f"Insufficient mathematical content (score: {math_score:.2f})"
            
            logger.info(f"File validated successfully: {Path(file_path).name} (math score: {math_score:.2f})")
            return True, f"Valid mathematical content (score: {math_score:.2f})"
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _extract_text_content(self, file_path: str, file_ext: str) -> Optional[str]:
        """
        Extract text content from file based on type.
        
        Args:
            file_path: Path to file
            file_ext: File extension
            
        Returns:
            Extracted text content or None if failed
        """
        try:
            if file_ext in self.supported_text_types:
                return self._extract_from_text_file(file_path)
            elif file_ext in self.supported_image_types:
                return self._extract_from_image(file_path)
            elif file_ext in self.supported_pdf_types:
                return self._extract_from_pdf(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def _extract_from_text_file(self, file_path: str) -> str:
        """Extract text from text-based files."""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Could not decode text file with any supported encoding")
    
    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            # Open and preprocess image
            image = Image.open(file_path)
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Use Tesseract OCR with multiple languages
            custom_config = r'--oem 3 --psm 6 -l eng+ita'
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text_content = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Limit to first 10 pages for performance
                max_pages = min(len(pdf_reader.pages), 10)
                
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return ""
    
    def _contains_forbidden_content(self, text: str) -> bool:
        """
        Check if text contains forbidden content.
        
        Args:
            text: Text to check
            
        Returns:
            True if forbidden content found
        """
        text_lower = text.lower()
        
        for keyword in self.forbidden_keywords:
            if keyword in text_lower:
                logger.warning(f"Forbidden keyword found: {keyword}")
                return True
        
        return False
    
    def _calculate_mathematical_score(self, text: str) -> float:
        """
        Calculate mathematical content score (0.0 to 1.0).
        
        Args:
            text: Text to analyze
            
        Returns:
            Mathematical content score
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        if not words:
            return 0.0
        
        # Count mathematical keywords
        math_word_count = 0
        for keyword in self.all_keywords:
            # Count exact matches and partial matches
            if keyword in text_lower:
                # Weight longer keywords higher
                weight = len(keyword) / 10.0 + 1.0
                math_word_count += text_lower.count(keyword) * weight
        
        # Count mathematical symbols and patterns
        math_symbols = [
            r'\d+\s*[+\-*/=]\s*\d+',  # Basic arithmetic
            r'[xy]\s*[+\-]\s*\d+',    # Variables with numbers
            r'\b\d+x\b',              # Coefficient notation
            r'[a-z]\(\w+\)',          # Function notation
            r'\b\d+/\d+\b',           # Fractions
            r'\^\d+',                 # Exponents
            r'√\d+',                  # Square roots
            r'∫|∑|∏|∂|∇|∆',          # Mathematical symbols
            r'[≤≥≠≈∈∉⊂⊆∪∩]',         # Mathematical operators
        ]
        
        symbol_count = 0
        for pattern in math_symbols:
            matches = re.findall(pattern, text)
            symbol_count += len(matches) * 2  # Weight symbols higher
        
        # Calculate score
        total_score = math_word_count + symbol_count
        max_possible_score = len(words) * 0.5  # Theoretical maximum
        
        score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        return score
    
    def validate_file_safety(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate file for security and safety.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Tuple of (is_safe, reason)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file permissions
            if not os.access(file_path, os.R_OK):
                return False, "File is not readable"
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            safe_mime_types = [
                'text/plain', 'text/markdown', 'application/pdf',
                'image/jpeg', 'image/png', 'image/bmp', 'image/tiff'
            ]
            
            if mime_type and mime_type not in safe_mime_types:
                return False, f"Unsafe MIME type: {mime_type}"
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            safe_extensions = (
                self.supported_image_types + 
                self.supported_text_types + 
                self.supported_pdf_types
            )
            
            if file_ext not in safe_extensions:
                return False, f"Unsafe file extension: {file_ext}"
            
            return True, "File is safe to process"
            
        except Exception as e:
            return False, f"Safety validation error: {str(e)}"
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        try:
            path_obj = Path(file_path)
            stat = os.stat(file_path)
            
            return {
                'name': path_obj.name,
                'extension': path_obj.suffix.lower(),
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'mime_type': mimetypes.guess_type(file_path)[0],
                'is_readable': os.access(file_path, os.R_OK),
                'absolute_path': path_obj.absolute()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
