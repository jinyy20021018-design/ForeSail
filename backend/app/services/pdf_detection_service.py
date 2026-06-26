import re
import zlib
from pathlib import Path


def detect_pdf(path: Path) -> dict:
    try:
        content = path.read_bytes()
        text = extract_pdf_text(path)
        page_count = _page_count(content)
        text_char_count = len(text.strip())
        if text_char_count > 200:
            pdf_type = "TEXT_PDF"
        elif page_count > 0 and text_char_count < 50:
            pdf_type = "SCANNED_PDF"
        else:
            pdf_type = "UNKNOWN_PDF"
        return {
            "pdf_type": pdf_type,
            "text_char_count": text_char_count,
            "page_count": page_count,
            "requires_vision": pdf_type == "SCANNED_PDF",
            "warnings": [] if pdf_type != "SCANNED_PDF" else ["Document appears to be scanned or image-based."],
            "text": text,
        }
    except Exception as error:
        return {
            "pdf_type": "UNKNOWN_PDF",
            "text_char_count": 0,
            "page_count": 0,
            "requires_vision": False,
            "warnings": [f"PDF detection failed: {error}"],
            "text": "",
        }


def extract_pdf_text(path: Path) -> str:
    content = path.read_bytes()
    chunks = [_extract_text_operators(content)]
    for stream in _streams(content):
        chunks.append(_extract_text_operators(stream))
    return "\n".join(chunk for chunk in chunks if chunk).strip()


def _streams(content: bytes) -> list[bytes]:
    streams: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", content, re.DOTALL):
        raw = match.group(1).strip(b"\r\n")
        prefix = content[max(0, match.start() - 500):match.start()]
        if b"FlateDecode" in prefix:
            try:
                streams.append(zlib.decompress(raw))
                continue
            except zlib.error:
                pass
        streams.append(raw)
    return streams


def _extract_text_operators(content: bytes) -> str:
    text = content.decode("latin-1", errors="ignore")
    values: list[str] = []
    for match in re.finditer(r"\((.*?)\)\s*Tj", text, re.DOTALL):
        values.append(_clean_pdf_string(match.group(1)))
    for array_match in re.finditer(r"\[(.*?)\]\s*TJ", text, re.DOTALL):
        values.extend(_clean_pdf_string(value) for value in re.findall(r"\((.*?)\)", array_match.group(1), re.DOTALL))
    readable = "\n".join(value for value in values if value.strip())
    readable = re.sub(r"\s+", " ", readable).strip()
    return readable


def _clean_pdf_string(value: str) -> str:
    value = value.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
    value = re.sub(r"\\[0-7]{1,3}", " ", value)
    return value.strip()


def _page_count(content: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", content))
