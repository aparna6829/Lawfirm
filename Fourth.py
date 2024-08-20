import streamlit as st
import os
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS

# Initialize the LLM
Gemini = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=Gemini)

# Set the FAISS index path
EMBEDDING_PATH = "13_INDEX"

def get_summarized_response():
    cache_key = "embeddings_chain"
    if cache_key not in st.session_state:
        embeddings = HuggingFaceEmbeddings()
        vector = FAISS.load_local(EMBEDDING_PATH, embeddings, allow_dangerous_deserialization=True)
        db = vector.as_retriever()


        template = """
    You are an expert legal assistant specializing in case retrieval. 
    Your task is to help lawyers find the most relevant cases based on their query.

    Use the following context to locate and present cases:

    <context>
    {context}
    </context>

    Lawyer's Query: {input}

    Please provide the response in the following format:

    [CASE_START]
    Case Number: [Insert Case Number]
    Case Name: [Insert Case Name]
    Court: [Insert Court Name]
    Date: [Insert Date]
    Time: [Insert Time]
    Case Number: [Insert Case Number]
    Summary: [The Summary we have expand that into double content]

    [CASE_END]

    (Repeat the above format for each relevant case)

    If any information is missing, clearly state what cannot be provided. Ensure your response is clear, concise, and directly relevant to the lawyer's query.
    """
        prompt = ChatPromptTemplate.from_template(template=template)
        doc_chain = create_stuff_documents_chain(llm, prompt)
        chain = create_retrieval_chain(db, doc_chain)
        st.session_state[cache_key] = chain
    else:
        chain = st.session_state[cache_key]
    return chain

import re

def parse_cases(response):
    cases = []
    for case_text in response.split('[CASE_START]')[1:]:  # Skip the first empty split
        case_data = {}
        lines = case_text.strip().split('\n')
        for line in lines:
            if line.startswith('[CASE_END]'):
                break
            if ':' in line:
                key, value = line.split(':', 1)
                case_data[key.strip()] = value.strip()
        if case_data:
            cases.append(case_data)
    return cases

def query_index(user_query):
    chain = get_summarized_response()
    response = chain.invoke({"input": user_query})
    return parse_cases(response['answer'])


