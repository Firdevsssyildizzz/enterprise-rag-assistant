
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_pdf_into_chunks(file_path):
    reader = PdfReader(file_path)

    # PDF sayfalarından metinleri al
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text and text.strip():
            pages.append((page_number, text))

    # Metinleri küçük parçalara ayır
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = []

    for page_number, text in pages:
        for chunk in splitter.split_text(text):
            chunks.append({
                "text": chunk,
                "page": page_number
            })

    print(f"Toplam oluşturulan parça sayısı: {len(chunks)}")

    for index, chunk in enumerate(chunks[:3], start=1):
        print(f"\n--- Parça {index} | Sayfa {chunk['page']} ---")
        print(chunk["text"][:300])

    return chunks


if __name__ == "__main__":
    pdf_path = Path("documents") / "sample.pdf"
    split_pdf_into_chunks(pdf_path)
