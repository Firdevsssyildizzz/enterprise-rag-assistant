
import hashlib
import tempfile
from pathlib import Path

import chromadb
import streamlit as st

from embedding import create_embeddings
from rag_assistant import ask_rag
from text_chunker import split_pdf_into_chunks


# Uygulama ayarları
st.set_page_config(
    page_title="Enterprise RAG Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Enterprise RAG Assistant")

st.write(
    "PDF belgelerinizi yükleyin ve yerel yapay zekâ "
    "modelimizle belgeleriniz hakkında sorular sorun."
)

DB_PATH = "./chroma_db"


# ChromaDB bağlantısı
def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)

    return client.get_or_create_collection(
        name="enterprise_documents",
        metadata={"hnsw:space": "cosine"}
    )


# PDF dosyasını işleme
def process_pdf(uploaded_file):
    pdf_bytes = uploaded_file.getvalue()

    # Dosyanın içeriğinden benzersiz belge kimliği oluştur
    document_id = hashlib.sha256(pdf_bytes).hexdigest()[:16]

    collection = get_collection()

    # Aynı PDF daha önce işlenmiş mi?
    existing = collection.get(
        where={"document_id": document_id},
        limit=1
    )

    if existing["ids"]:
        return document_id, 0, True

    # PDF dosyasını geçici klasöre kaydet
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "uploaded.pdf"
        pdf_path.write_bytes(pdf_bytes)

        chunks = split_pdf_into_chunks(pdf_path)

    if not chunks:
        raise ValueError(
            "PDF dosyasında okunabilir metin bulunamadı."
        )

    # Metin parçalarını hazırla
    texts = [chunk["text"] for chunk in chunks]

    # Embedding vektörlerini oluştur
    vectors = create_embeddings(texts)

    # Verileri ChromaDB'ye kaydet
    batch_size = 100

    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))

        collection.upsert(
            ids=[
                f"{document_id}_{i}"
                for i in range(start, end)
            ],
            documents=texts[start:end],
            embeddings=vectors[start:end].tolist(),
            metadatas=[
                {
                    "source": uploaded_file.name,
                    "page": chunks[i]["page"],
                    "document_id": document_id
                }
                for i in range(start, end)
            ]
        )

    return document_id, len(chunks), False


# Yan menü
with st.sidebar:
    st.header("⚙️ Sistem Bilgileri")

    st.success("LLM: Qwen2.5 3B")
    st.info("Vektör Veritabanı: ChromaDB")
    st.info("Embedding: Multilingual MiniLM")

    st.divider()
    st.caption("Python • RAG • Ollama • Streamlit")


# PDF yükleme bölümü
st.subheader("📄 PDF Yükleme")

uploaded_file = st.file_uploader(
    "PDF belgenizi seçin",
    type=["pdf"]
)

if uploaded_file is not None:

    if st.button("📥 PDF'yi İşle", type="primary"):

        with st.spinner("PDF işleniyor..."):

            try:
                document_id, count, already_exists = process_pdf(
                    uploaded_file
                )

                st.session_state["document_id"] = document_id
                st.session_state["document_name"] = uploaded_file.name

                if already_exists:
                    st.info("Bu PDF daha önce işlenmiş.")
                else:
                    st.success(
                        f"PDF başarıyla işlendi! "
                        f"{count} metin parçası kaydedildi."
                    )

            except Exception as error:
                st.error(
                    f"PDF işleme hatası: {error}"
                )


# Belgeye özel soru-cevap bölümü
if "document_id" in st.session_state:

    st.success(
        "Aktif belge: "
        + st.session_state["document_name"]
    )

    st.subheader("💬 Belgeye Soru Sor")

    question = st.text_input(
        "Sorunuzu yazın:",
        placeholder="Bu belgede anlatılan temel konu nedir?"
    )

    if st.button("🔍 Yapay Zekâya Sor"):

        if not question.strip():
            st.warning("Lütfen bir soru yazın.")

        else:
            with st.spinner("Yapay zekâ cevap hazırlıyor..."):

                try:
                    answer = ask_rag(
                        question,
                        document_id=st.session_state["document_id"]
                    )

                    st.subheader("🤖 Yapay Zekâ Cevabı")
                    st.write(answer)

                except Exception as error:
                    st.error(
                        f"Soru-cevap hatası: {error}"
                    )


st.divider()

st.caption(
    "Enterprise RAG Assistant | "
    "Python • ChromaDB • Ollama • Streamlit"
)
