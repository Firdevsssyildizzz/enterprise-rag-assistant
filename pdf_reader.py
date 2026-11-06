
from pathlib import Path
from pypdf import PdfReader


def read_pdf(file_path):
    """PDF dosyasındaki metinleri sayfa sayfa okur."""
    reader = PdfReader(file_path)

    print(f"Toplam sayfa sayısı: {len(reader.pages)}")

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        print(f"\n--- Sayfa {page_number} ---")
        print(text[:500] if text else "Bu sayfada okunabilir metin yok.")


if __name__ == "__main__":
    pdf_path = Path("documents") / "sample.pdf"

    if pdf_path.exists():
        read_pdf(pdf_path)
    else:
        print(f"PDF dosyası bulunamadı: {pdf_path}")
