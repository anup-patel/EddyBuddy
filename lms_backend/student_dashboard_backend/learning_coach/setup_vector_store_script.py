import os
import json
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.vectorstores import FAISS
from langchain_text_splitters import TokenTextSplitter
from langchain.schema import Document


embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)

list_of_documents = []

y = 0
notes_folder = '../../../db/notes'
print(notes_folder)
for filename in os.listdir(notes_folder):
    if filename.endswith('.txt'):
        with open(os.path.join(notes_folder, filename), 'r') as f:
            content = f.read()
            doc_id = y
            chunks = text_splitter.split_text(content)

            x = 0
            for chunk in chunks:
       
                doc_idd = f"{doc_id}_{x+1}"
                metadata = {"doc_id": doc_idd}
                document = Document(page_content=chunk, metadata=metadata)
                list_of_documents.append(document)
                x = x+1

            y = y+1

db = FAISS.from_documents(list_of_documents, embeddings)
db.save_local('../../../db/notes_vector_store')
