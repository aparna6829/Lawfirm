import os
import streamlit as st
import re
from langchain.prompts import PromptTemplate
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import io
 
Gemini = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=Gemini)
 

 
doc1_path = "my_own.docx"
doc2_path = "my_own2.docx"

 
doc1 = Document(doc1_path)
doc2 = Document(doc2_path)

 
placeholders1 = re.findall(r'\{\{(.*?)\}\}', ' '.join([p.text for p in doc1.paragraphs]))
placeholders2 = re.findall(r'\{\{(.*?)\}\}', ' '.join([p.text for p in doc2.paragraphs]))

 
def process_input(user_input, placeholders1, placeholders2):
    template = """
    You are an expert in filling details in word documents using placeholders and providing definitions for legal conditions.
    Use the provided details to fill out the placeholders .
    Determine which document the details are for based on the context provided.
    Indicate which document the details belong to by specifying "Document: Master Service Agreement" or "Document: New York Agreement"  at the beginning of your response.
    If any details are missing, indicate which ones are missing.
   
    Document 1 (New York Agreement) placeholders: {placeholders1}
    Document 2 (Master Service Agreement) placeholders: {placeholders2}

   
   
    For Master Service Agreement, please give only date, don't give the year and other matter.
   
    For each placeholder, provide the information in this format:
    PLACEHOLDER: information
 
    If a placeholder is missing information, use this format:
    PLACEHOLDER: MISSING
 
    Based on the user input, fill in the placeholders and provide definitions for relevant legal terms.
    Structure your response exactly like this, replacing the examples with actual content:
    [[
        "document": "Master Service Agreement" or "New York Agreement",
        "placeholders": [
            [["PLACEHOLDER1": "Value1"]],
            [["PLACEHOLDER2": "Value2"]],
            [["PLACEHOLDER3": "MISSING"]]
        ],
        "definitions": [
            [["Term1": "Definition1"]],
            [["Term2": "Definition2"]]
        ]
    ]]

    User input: {content}
   
    Response:
    """
   
    formatted_template = template.format(placeholders1=placeholders1,
                                         placeholders2=placeholders2,
                                    
                                         content=user_input)
    prompt = PromptTemplate(template=formatted_template)
    chain = prompt | llm
    response = chain.invoke({"content": user_input})
    return response
 
 
# Load documents and extract placeholders
 
# Initialize session state
if 'state' not in st.session_state:
    st.session_state.state = {
        'user_input': "",
        'collected_details': {},
        'placeholders': {},
        'processed': False,
        'document_generated': False,
        'final_doc': None,
        'document_type': ""
    }
   
   
def add_content_to_document(doc_path, placeholders):
    doc = Document(doc_path)
    # Replace placeholders
    for paragraph in doc.paragraphs:
        for key, value in placeholders.items():
            if value != "MISSING":
                paragraph.text = paragraph.text.replace(f"{{{{{key}}}}}", value)    
    return doc
 
