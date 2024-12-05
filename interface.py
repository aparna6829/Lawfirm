import streamlit as st
import requests
import html
from urllib.parse import urlencode
 
# Define the API URL and headers
SEARCH_API_URL = 'https://api.indiankanoon.org/search/'
DOC_API_URL = 'https://api.indiankanoon.org/doc/'
API_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': 'Token 68f11641a79c33c99fbb97fd5edfc6740708ea2b'  # Replace with your actual token
}
 
def fetch_documents(query):
    """Fetch documents from the Indian Kanoon API based on the user query."""
    try:
        data = urlencode({'formInput': query})
        response = requests.post(SEARCH_API_URL, headers=API_HEADERS, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None
 
def fetch_document_by_tid(tid):
    """Fetch a specific document from the Indian Kanoon API based on the tid."""
    try:
        url = f"{DOC_API_URL}{tid}/"
        data = urlencode({'include_doc': 'true'})
        response = requests.post(url, headers=API_HEADERS, data=data)
        response.raise_for_status()
        result = response.json()
        if 'doc' in result:
            return result['doc']
        else:
            return 'Document content not available.'
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while fetching the document: {e}")
        return None
 
def display_documents(docs):
    """Display documents using custom HTML and CSS to match the image."""
    for doc in docs:
        title = html.escape(doc.get('title', 'No Title'))
        snippet = doc.get('headline', 'No snippet available')
        docsource = html.escape(doc.get('docsource', 'Unknown Source'))
        cites = doc.get('numcites', 0)
        cited_by = doc.get('numcitedby', 0)
        tid = doc.get('tid', '')
       
        html_content = f"""
        <div style="margin-bottom: 20px; font-family: Arial, sans-serif;">
            <a href="?tid={tid}" target="_blank"
               style="color: #1a0dab; text-decoration: none; font-size: 18px; font-weight: normal;">
                {title}
            </a>
            <div style="color: #545454; font-size: 14px; line-height: 1.4; margin-top: 5px;">
                {snippet}
            </div>
            <div style="color: #006621; font-size: 13px; margin-top: 2px;">
                {docsource} Cites {cites} - Cited by {cited_by} -
                <a href="?tid={tid}" target="_blank" style="color: #006621;">Full Document</a>
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
 
def main():
    st.set_page_config(page_title="Indian Kanoon Legal Search", layout="wide")
 
    # Custom CSS for the page
    st.markdown("""
        <style>
        .stTextInput > div > div > input {
            font-size: 16px;
        }
        .stButton > button {
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
        .stSelectbox {
            font-size: 14px;
        }
        [data-testid="stButton"]{
            margin-top:23px;
           
        }
        [id="legal-search-engine"]{
            color: rgb(26, 115, 232);
            font-size: 30px;
            font-weight: 600;
            margin-top : -70px;
            margin-left: 600px;
          
        }

        </style>
        """, unsafe_allow_html=True)
 
    # Check if we're in document view mode
    if 'tid' in st.query_params:
        tid = st.query_params['tid']
        doc_content = fetch_document_by_tid(tid)
        if doc_content:
            st.markdown(doc_content, unsafe_allow_html=True)
        else:
            st.error("Failed to fetch the document content.")
        return  # Exit the function early as we're in document view mode
 
    # Title and search bar
    st.markdown("<h1 style='color: #1a73e8; font-size: 24px; font-weight: normal;'>Legal Search Engine</h1>", unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input("", placeholder="Enter your search query")
    with col2:
        search_button = st.button("Search")
    with col3:
        sort_option = st.selectbox("", options=["Relevance", "Date"], index=0)
 
    # Main app logic
    if search_button and query.strip():
        with st.spinner("Fetching results..."):
            response_json = fetch_documents(query)
        if response_json:
            total_results = response_json.get('total', 0)
            search_time = response_json.get('time', 0)
            docs = response_json.get('docs', [])
           
            st.markdown(f"<div style='color: #808080; font-size: 14px;'>1 - 10 of {total_results} ({search_time:.2f} seconds)</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #e0e0e0;'>", unsafe_allow_html=True)
            display_documents(docs[:10])  # Display only the first 10 results
    elif search_button:
        st.warning("Please enter a valid search query.")
 
    # Footnote
    st.markdown("<div style='margin-top: 450px; text-align: center; color: #808080; font-size: 12px;'>Powered by Promptora</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()