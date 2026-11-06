
from pathlib import Path
import chromadb

from embedding import create_embeddings
from text_chunker import split_pdf_into_chunks


def build_vector_database(pdf_path):
    # PDF metnini parçalara ayır
    chunks = split_pdf_into_chunks(pdf_path)

    if not chunks:
        print("PDF dosyasında işlenebilir metin bulunamadı.")
        return

    # Metin parçalarını embedding modeline gönder
    texts = [chunk["text"] for chunk in chunks]
    vectors = create_embeddings(texts)

    # Kalıcı ChromaDB veritabanını oluştur
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(
        name="enterprise_documents",
        metadata={"hnsw:space": "cosine"}
    )

    # Metinleri, vektörleri ve sayfa bilgilerini kaydet
    batch_size = 100

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size

        collection.upsert(
            ids=[
                f"sample_page_{chunk['page']}_chunk_{i}"
                for i, chunk in enumerate(chunks[start:end], start=start)
            ],
            documents=texts[start:end],
            embeddings=vectors[start:end].tolist(),
            metadatas=[
                {"page": chunk["page"], "source": pdf_path.name}
                for chunk in chunks[start:end]
            ]
        )

    print("Vektör veritabanı başarıyla oluşturuldu!")
    print("Kaydedilen toplam parça:", collection.count())


if __name__ == "__main__":
    pdf_path = Path("documents") / "sample.pdf"
    build_vector_database(pdf_path)
