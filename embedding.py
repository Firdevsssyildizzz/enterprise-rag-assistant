
from sentence_transformers import SentenceTransformer

# Türkçe dahil birden fazla dili destekleyen embedding modeli
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def create_embeddings(texts):
    model = SentenceTransformer(MODEL_NAME)

    # Metinleri sayısal vektörlere dönüştür
    vectors = model.encode(texts)

    return vectors


if __name__ == "__main__":
    example_texts = [
        "Yapay zeka teknolojileri hızla gelişiyor.",
        "Makine öğrenmesi, yapay zekanın bir alt alanıdır.",
        "Bugün hava oldukça güzel."
    ]

    embeddings = create_embeddings(example_texts)

    print("Oluşturulan vektör sayısı:", len(embeddings))
    print("Her vektörün boyutu:", len(embeddings[0]))
    print("İlk vektörün ilk 5 değeri:", embeddings[0][:5])
