import streamlit as st
# from second import second_tab
from Fourth import get_summarized_response,query_index
from Third import load_file,get_summarized_response 
import re 
from Five import get_response 
import google.generativeai as genai
from Evidence_2 import encode_image
import requests
import json
import io
from second import process_input, add_content_to_document, doc1_path,doc2_path, doc3_path, doc4_path, doc5_path,doc6_path, doc7_path, placeholders1,placeholders2,placeholders3,placeholders4,placeholders5,placeholders6,placeholders7


# Set page configuration
st.set_page_config(page_icon="⚖️", page_title="Legal Bot", layout="wide")

# Hide Streamlit default elements
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# OpenAI API Key
api_key = st.secrets["OPENAI_API_KEY"]

# Header container
header = st.container()
header.title("⚖️Legal Bot")
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

case_pattern = re.compile(r'\*\*Case (\d+):\*\* (.+?)(?=\n\*\*Case \d+:|$)', re.DOTALL)
# Style modifications for fixed header and other elements
st.markdown(
    """
    <style>
        .st-emotion-cache-vj1c9o {
            background-color: rgb(242, 242, 242, 0.68);
        }
        div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
            position: sticky;
            top: 2; /* Stick to top edge */
            background-color: rgb(242, 242, 242, 0.68);
            z-index: 999;
            text-align: center;
        }
        .fixed-header {
            border-bottom: 0;
        }
        .st-emotion-cache-1whx7iy p {
            color: black;
            word-break: break-word;
            margin-bottom: 0px;
            font-size: 14px;
            font-weight: 1000;
        }
        .st-emotion-cache-1jicfl2 {
            width: 100%;
            padding: 6rem 1rem 10rem;
            min-width: auto;
            max-width: initial;
            margin-top: -100px;
        }
        [data-testid="stChatInput"]{
            position: fixed;
            bottom: 2%;
        }
        
        .st-emotion-cache-16idsys p {
            word-break: break-word;
            margin-bottom: 0px;
            font-size: 15px;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Main function
def main():
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📜 What is Legal Assist", "📄 Template Drafting", "📁 Document Insight", "🧠 Legal Inference Engine", "🧑🏼‍⚖️Legal Assistant", " 🔍 Legal Evidence"])

    with tab1:
        st.write("""<h2 style='color: #2c3e50; text-align: center;'>Your Trusted Legal Assistant</h2>""", unsafe_allow_html=True)
        st.write(
            """
            <div style='text-align: justify; font-size: 16px; color: #34495e;'>
                Welcome to <strong>Legal Bot </strong>, your trusted partner in navigating the complexities of legal documentation. 
                Whether you're drafting contracts, agreements, or any other legal documents, we are here to simplify the process and ensure precision in every detail.
                As legal professionals, we understand that the smallest mistake in a document can have significant implications. 
                Our advanced AI-powered tools are designed to assist you with drafting, reviewing, and finalizing your legal documents, 
                ensuring that you never miss a critical detail.<br><br>
                With <strong>Legal Bot</strong>, 
                <ul>
                    <li>Generate accurate and comprehensive legal documents with ease.</li>
                    <li>Fill in placeholders with confidence, knowing that every detail is meticulously handled.</li>
                    <li>Review and finalize your drafts quickly, saving valuable time and resources.</li>
                </ul><br>
                Our platform combines the power of cutting-edge AI technology with the knowledge of seasoned legal professionals, 
                offering you a reliable assistant that adapts to your specific needs. Whether you're an individual, a law firm, or a corporation, 
                <strong>Legal Bot</strong> is here to enhance your productivity and ensure the highest standards of legal accuracy.
                Step into the future of legal document management with <strong>Legal Bot</strong>. Let us handle the details, 
                so you can focus on what truly matters – providing exceptional legal services to your clients.
            </div>                  
            """,
            unsafe_allow_html=True
        )

    with tab2:
        st.markdown("""
        <div style='text-align: justify; font-size: 16px; color: #34495e;'>
            <strong>Currently these are the document templates available to streamline your legal documentation/templates:</strong>
                <li><strong>1.Master Service Agreement</strong></li><li><strong> 2.New York Agreement</strong></li><li><strong> 3.Data License Agreement</strong></li><li><strong> 4.Professional Service Agreement</strong></li>
                <li><strong>5.Asset Purchase Agreement 6.Safe Simple Agreement for Future Equity 7.Founder's Stock Purchase Agreement</strong></li>
                
        </div>
        """,unsafe_allow_html=True)
        # Initialize session state
        if 'state' not in st.session_state:
            st.session_state.state = {
                'user_input': "",
                'collected_details': {},
                'definitions': {},
                'placeholders': {},
                'processed': False,
                'document_generated': False,
                'final_doc': None,
                'document_type': ""
            }
        
        
        user_input = st.text_area("Enter your query to fill the details:", value=st.session_state.state['user_input'])
        if user_input and st.button("Process Input"):
            st.session_state.state['user_input'] = user_input
            with st.spinner("Processing your input..."):
                processed_response = process_input(user_input, placeholders1, placeholders2,placeholders3,placeholders4,placeholders5,placeholders6,placeholders7)
                processed_response = processed_response.content
                fresponse = processed_response.replace('[','{').replace(']','}')
                try:
                    fresponse = fresponse.split("```json")[1].split("```")[0]
                    fresponse = json.loads(fresponse)
                except:
                    fresponse = json.loads(fresponse)
                st.session_state.state['document_type'] = fresponse.get("document", "")
                st.session_state.state['placeholders'] = fresponse.get("placeholders", {})
                st.session_state.state['processed'] = True
            st.success(f"Input processed successfully for {st.session_state.state['document_type']}!")
        
        # Display placeholders and definitions side by side
        if st.session_state.state['processed']:
            st.markdown('<div class="step-header">Step 2: Review and Update Details</div>', unsafe_allow_html=True)
            st.markdown('<p class="subheader">Missing Details</p>', unsafe_allow_html=True)
            for key, value in st.session_state.state['placeholders'].items():
                if value == "MISSING":
                    user_detail = st.text_input(f"{key.replace('_', ' ')}:", key=key,
                                                value=st.session_state.state['collected_details'].get(key, ""))
                    st.session_state.state['collected_details'][key] = user_detail
                else:
                    st.text_input(f"{key.replace('_', ' ')}:", value=value, disabled=True)
        
            if st.button("Update Missing Details"):
                for key, value in st.session_state.state['collected_details'].items():
                    if value:
                        st.session_state.state['placeholders'][key] = value
                st.success("Missing Details updated successfully!")
        
            # st.markdown('<div class="step-header">Step 3: Generate and Download Document</div>', unsafe_allow_html=True)
            if st.button("Generate Final Document"):
                with st.spinner("Generating document..."):
                    doc_paths = {
                    "master service agreement": doc2_path,
                    "new york agreement": doc1_path,
                    "data license agreement": doc3_path,
                    "professional service agreement": doc4_path,
                    "asset purchase agreement": doc5_path,
                    "safe simple agreement for future equity" : doc6_path,
                    "founders stock purchase agreement" : doc7_path
                }
                
                    document_type = st.session_state.state['document_type'].lower()
                
                    doc_path = doc_paths.get(document_type.lower())
                    if doc_path:
                        st.session_state.state['final_doc'] = add_content_to_document(
                            doc_path,
                            st.session_state.state['placeholders']
                        )
                        st.session_state.state['document_generated'] = True
                    
                    else:
                        st.error(f"Unknown document type: {st.session_state.state['document_type']}")
                st.success(f"Final document generated for {st.session_state.state['document_type']} with all missing details.")
            if st.session_state.state['document_generated']:
                bio = io.BytesIO()
                st.session_state.state['final_doc'].save(bio)
                st.download_button(
                    label="Download Final Document",
                    data=bio.getvalue(),
                    file_name=f"{st.session_state.state['document_type'].replace(' ', '_').lower()}_final.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        
            # Display the final content of placeholders and definitions
            if st.checkbox("Show final content"):
                st.json(st.session_state.state['placeholders'])
        
        else:
            st.info("Please enter your query and click 'Process Input' to start.")
        # st.markdown('</div>', unsafe_allow_html=True)
    with tab3:
        uploaded_file = st.file_uploader("Upload your file", type=["pdf", "csv", "docx", "xlsx", "xls"], label_visibility="collapsed")
        if uploaded_file is not None:
            st.success("File uploaded successfully.")
            file_name = uploaded_file.name.split('.')[0]

            with st.spinner("Processing"):
                load_file(uploaded_file, file_name)
                chain = get_summarized_response(f"{file_name}_INDEX", uploaded_file.name)

            user_input = st.chat_input("Enter your question here:")
            if user_input:
                with st.spinner("Getting Response"):
                    response = chain.invoke({"input": user_input})
                    with st.expander("Response"):
                        st.write(response['answer'])
   

    with tab4:
        st.markdown("""
        <div style='text-align: justify; font-size: 16px; color: #34495e;'>
            <strong>Database Source:</strong>
                <li><strong>Local Case's File</strong></li>
                
        </div>
        """,unsafe_allow_html=True)       
        user_query = st.text_input("Ask a question about your legal cases:")
        if user_query:
            
            with st.spinner("Analyzing your query..."):
                cases = query_index(user_query)
                
                for i, case in enumerate(cases, 1):
                    case_title = f"Case {i}: {case.get('Case Name', 'Unnamed Case')}"
                    with st.expander(case_title):
                        for key, value in case.items():
                            if key != 'Case Name':
                                st.markdown(f"**{key}:** {value}")
                                
    with tab5:
        def set_query(query):
            st.session_state.query_input = query
            st.rerun()

        # Initialize session state for the query if it doesn't exist
        if "query_input" not in st.session_state:
            st.session_state.query_input = ""

        # The text input field, populated with the query stored in session state
        query = st.text_input("Enter your query:", value=st.session_state.query_input)
        
        st.write("Queries to try:")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("What are the state's laws on wildlife management and hunting?"):
                set_query("What are the state's laws on wildlife management and hunting?")
        with col2:
                
            if st.button("Please explain the current eminent domain policies in NewYork."):
                set_query("Please explain the current eminent domain policies in NewYork.")
        
        with col3:
                    
            if st.button("What are the elements of permitting requirements and notice?"):
                set_query("What are the elements of permitting requirements and notice?")
        
        with col4:

            if st.button("What is adverse possession? What are the elements of adverse possession in Alaska? "):
                set_query("What is adverse possession? What are the elements of adverse possession in Alaska?")
                
            
        if query:
            with st.spinner("Analyzing your Query"):
                llm_chain = get_response(question=query)
                # Generate text based on the user's input
                generated_text = llm_chain.invoke({"question": query})
                # Print the generated text
                generated_answer=generated_text['text']
                st.write(generated_answer)
                
    with tab6:
        # Path to your image
        image_path = st.file_uploader("Upload your evidence here:", type=["png", "jpg", "jpeg"])
        if image_path:
            with st.expander("Uploaded Evidence"):
                st.image(image_path)
            query = st.text_input("Enter your query here:")
            if query.lower():
                with st.spinner("Analyzing the Evidence"):
                    prompt_template = "You are an legal assistance bot who is an expert in Analyzing the evidences and provide the complete insight about the evidence provided even without missing any minute detail"
            
                    # Getting the base64 string
                    base64_image = encode_image(image_path)
                    
                    headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                    }
                    
                    payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                        "role": "user",
                        "content": [
                            {
                            "type": "text",
                            "text": prompt_template
                            },
                            {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                            }
                        ]
                        }
                    ],
                    "max_tokens": 4096
                    }
                    
                    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            
                    st.write(response.json()['choices'][0]['message']['content'])
            

if __name__ == '__main__':
    main()