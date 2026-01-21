import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv
import os




load_dotenv()
faqs_path = Path(__file__).parent / "resources/faq_data.csv"
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collections_name_faq = 'faqs'
groq_client = Groq()

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name= "sentence-transformers/all-MiniLM-L6-v2",
)



def ingest_faq_data(path):
    if collections_name_faq not in [c.name for c in chroma_client.list_collections()]:
        print("Ingesting faq data into ChromadDB...")
        collection = chroma_client.get_or_create_collection(
            name = collections_name_faq,
            embedding_function = ef
        )

        df = pd.read_csv(path)
        docs = df["question"].tolist()
        metadata = [{'answer' : ans, 'source': 'Flipkart Policy 2024'} for ans in df["answer"].tolist()]
        ids = [f"id_{i}" for i in range(len(docs))]

        collection.add(
            documents= docs,
            metadatas= metadata,
            ids= ids
        )
        print(f"FAQ Data Successfully Ingested into Chroma Collection: {collections_name_faq}")
    else:
        print(f"collection name {collections_name_faq} already exists!")



def get_relevant_qa(query):
    collection = chroma_client.get_collection(name=collections_name_faq)
    result = collection.query(
        query_texts = [query],
        n_results=3
    )
    return result


def faq_chain(query):
    result = get_relevant_qa(query)

    context_list = []
    for i, meta in enumerate(result['metadatas'][0]):
        context_list.append(f"Source {i + 1} ({meta['source']}): {meta['answer']}")

    context = "\n\n".join(context_list)
    answers = generate_ans(query, context)
    return answers


def generate_ans(query, context):
    prompt = f'''You are a Flipkart Customer Assistant. Use the provided context to answer the user's question.

        Strict Rules:
        1. Only use the information in the Context.
        2. If the answer isn't there, say "I'm sorry, I don't have that specific information. Would you like to speak to a human?"
        3. Be polite and professional.

        Context:
        {context}

        Question: {query}

        Final Answer:'''


    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=os.environ['GROQ_MODEL'],
        temperature=0.2
    )

    return chat_completion.choices[0].message.content


if __name__ == '__main__':
    ingest_faq_data(faqs_path)
    query = "Do you take cash as a payment option?"
    # result = get_relevant_qa(query)

    answer = faq_chain(query)
    print(answer)
