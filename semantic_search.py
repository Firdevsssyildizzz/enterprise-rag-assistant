
import re
import chromadb
from embedding import create_embeddings


def generate_queries(question):
    """Soruyu farklı arama ifadeleriyle genişlet."""
    question = question.strip()
    queries = [question]

    normalized = question.casefold()

    # Yaşama ve aile ilişkileriyle ilgili soruları genişlet
    if (
        "kiminle yaş" in normalized
        or "kimlerle yaş" in normalized
        or "kimin yanında kal" in normalized
    ):
        queries.extend([
            "Çocuğun yaşadığı yer ve ona bakan aile üyeleri",
            "Çocuk kimin yanında kalıyor ve kim tarafından büyütülüyor?",
            "Anne ve babası ayrıldıktan sonra çocuk kime bırakıldı?",
            "Çocuğun annesi onu kimin yanına bıraktı?",
            "Çocuğun ailesi ve birlikte yaşadığı kişiler"
        ])

    # Tekrarlanan sorguları kaldır
    return list(dict.fromkeys(queries))


def semantic_search(
    question,
    top_k=5,
    verbose=False,
    document_id=None
):
    # Veritabanına bağlan
    client = chromadb.PersistentClient(
        path="./chroma_db"
    )

    collection = client.get_collection(
        name="enterprise_documents"
    )

    # Yalnızca seçilen belgeyi ara
    where_filter = None

    if document_id is not None:
        where_filter = {
            "document_id": document_id
        }

    # Alternatif sorgular oluştur
    queries = generate_queries(question)

    # Sorguları embedding vektörlerine dönüştür
    query_vectors = create_embeddings(queries)

    # Her sorgu için daha fazla aday getir
    results = collection.query(
        query_embeddings=query_vectors.tolist(),
        n_results=15,
        where=where_filter,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    # Farklı sorguların sonuçlarını birleştir
    candidates = {}
    rrf_k = 60

    for query_index, documents in enumerate(
        results["documents"]
    ):
        for rank, document in enumerate(
            documents, start=1
        ):
            metadata = results["metadatas"][query_index][rank - 1]
            distance = results["distances"][query_index][rank - 1]

            # Aynı içeriği tekrar kullanma
            text_key = re.sub(
                r"\s+", " ", document
            ).strip()

            if text_key not in candidates:
                candidates[text_key] = {
                    "document": document,
                    "metadata": metadata,
                    "distance": distance,
                    "score": 0.0
                }

            # Reciprocal Rank Fusion
            candidates[text_key]["score"] += (
                1.0 / (rrf_k + rank)
            )

            # En iyi distance değerini sakla
            if distance < candidates[text_key]["distance"]:
                candidates[text_key]["distance"] = distance
                candidates[text_key]["metadata"] = metadata

    # Sonuçları birleşik sıralama puanına göre sırala
    ranked = sorted(
        candidates.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    selected = ranked[:top_k]

    final_results = {
        "documents": [[
            item["document"] for item in selected
        ]],
        "metadatas": [[
            item["metadata"] for item in selected
        ]],
        "distances": [[
            item["distance"] for item in selected
        ]]
    }

    # Test modunda sonuçları göster
    if verbose:
        print("\nKullanılan arama sorguları:")

        for query in queries:
            print("-", query)

        for index, item in enumerate(
            selected, start=1
        ):
            metadata = item["metadata"]

            print(f"\n--- Sonuç {index} ---")
            print(f"Kaynak: {metadata.get('source')}")
            print(f"Sayfa: {metadata.get('page')}")
            print(
                f"Cosine distance: "
                f"{item['distance']:.4f}"
            )
            print(
                f"Birleşik puan: "
                f"{item['score']:.4f}"
            )
            print(f"Metin: {item['document'][:700]}")

    return final_results


if __name__ == "__main__":
    question = (
        "Beyaz Gemi hikâyesindeki çocuk "
        "kiminle yaşamaktadır?"
    )

    semantic_search(
        question,
        top_k=10,
        verbose=True,
        document_id="f0ad658657a344b1"
    )
