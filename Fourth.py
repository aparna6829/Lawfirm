import streamlit as st
import os
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.chains import LLMChain

# Initialize the LLM
Gemini = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=Gemini)

# Set the FAISS index path
EMBEDDING_PATH = "INDEX_3"

def get_summarized_response():
    cache_key = "embeddings_chain"
    if cache_key not in st.session_state:
        embeddings = HuggingFaceEmbeddings()
        vector = FAISS.load_local(EMBEDDING_PATH, embeddings, allow_dangerous_deserialization=True)
        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=vector.as_retriever(search_kwargs={"k": 10}),  # Increase k to get more results
            llm=llm
        )

        template = """
    You are an expert legal assistant specializing in case retrieval. 
    Your task is to help lawyers find the most relevant cases based on their query.
    The query may contain multiple topics. Ensure you retreive and present all the relevant cases for each topic mentioned in the query .

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
    Source PDF: [Insert the link which you have in the document ]
    Relevance: [Briefly explain how this case is relevant to the query]
    [CASE_END]
 


    (Repeat the above format for each relevant case)
    Ensure you include ALL cases that are relevant to ANY part of the query. Do not limit the number of cases returned.
 

    If any information is missing, clearly state what cannot be provided. Ensure your response is clear, concise, and directly relevant to the lawyer's query.
    """
        prompt = ChatPromptTemplate.from_template(template=template)
        doc_chain = create_stuff_documents_chain(llm, prompt)

        def retrieve_and_generate(query):
            docs = retriever_from_llm.get_relevant_documents(query)
            return doc_chain.invoke({"input": query, "context": docs})
        st.session_state[cache_key] = retrieve_and_generate
    else:
        retrieve_and_generate = st.session_state[cache_key]
    return retrieve_and_generate



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
    response = chain({"input": user_query})

    if isinstance(response, str):
        parsed_cases = parse_cases(response)
    elif isinstance(response, dict):
        # If it's a dictionary, it might contain the 'answer' directly
        parsed_cases = parse_cases(str(response))
    else:
        st.error("Unexpected response format. Please try again.")
        return []
 
    for case in parsed_cases:
        source_pdf_path = case.get('Source PDF')
        case_name = case.get('Case Name', 'Open PDF')  # Default to "Open PDF" if 'Case Name' is not found
        if source_pdf_path:
            case['Source PDF'] = f"[{case_name}]({source_pdf_path})"  # Convert to a clickable link with case name
    return parsed_cases


