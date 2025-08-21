import os
from typing import Optional
import PyPDF2
from docx import Document
import markdown
from bs4 import BeautifulSoup

# TODO: add embeddings + vector store persistence; connect to retriever

def extract_text_from_file(filepath: str, content_type: str) -> Optional[str]:
    """
    Extract text from various file types
    """
    try:
        if content_type == "application/pdf" or filepath.endswith('.pdf'):
            return extract_pdf_text(filepath)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filepath.endswith('.docx'):
            return extract_docx_text(filepath)
        elif content_type == "text/plain" or filepath.endswith('.txt'):
            return extract_txt_text(filepath)
        elif content_type == "text/markdown" or filepath.endswith('.md'):
            return extract_md_text(filepath)
        else:
            return None
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        return None

def extract_pdf_text(filepath: str) -> str:
    """Extract text from PDF using PyPDF2"""
    text = ""
    with open(filepath, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_docx_text(filepath: str) -> str:
    """Extract text from DOCX using python-docx"""
    doc = Document(filepath)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text.strip()

def extract_txt_text(filepath: str) -> str:
    """Extract text from plain text file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read().strip()

def extract_md_text(filepath: str) -> str:
    """Extract text from Markdown file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        md_content = file.read()
        # Convert markdown to HTML, then strip HTML tags
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text().strip()
