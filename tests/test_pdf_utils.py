import pytest
from services import pdf_utils

class DummyPage:
    def __init__(self, text):
        self._text = text
    def get_text(self):
        return self._text

class DummyDoc:
    def __init__(self, texts):
        self.texts = texts
    def __iter__(self):
        return (DummyPage(t) for t in self.texts)
    def __len__(self):
        return len(self.texts)

def test_extract_nonempty_text(monkeypatch):
    # Patch fitz.open to return dummy doc
    monkeypatch.setattr(pdf_utils, "fitz", type("fitz", (), {"open": lambda path: DummyDoc(["Hello world", "Second page text"])}) )
    result = pdf_utils.extract_text_from_pdf("dummy.pdf")
    assert isinstance(result, list)
    assert result[0]["text"] == "Hello world"
    assert result[1]["text"] == "Second page text"

def test_chunk_text_chunks_correctly():
    pages = [
        {"page": 1, "text": "word " * 600},
        {"page": 2, "text": "another " * 300}
    ]
    chunks = pdf_utils.chunk_text(pages, chunk_size_words=500)
    assert len(chunks) == 2  # 1 chunk for page 2, 2 for page 1
    assert chunks[0]["page"] == 1
    assert chunks[1]["page"] == 1 or chunks[1]["page"] == 2
