import streamlit as st
from second import second_tab
from Fourth import get_summarized_response,query_index
from Third import load_file,get_summarized_response 
import re 
from Five import get_response 
import google.generativeai as genai
from evidence import get_image


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
            <strong>Currently there are two types of legal documents/templates:</strong>
                <li><strong>Master Service Agreement</strong></li>
                <li><strong>New York Agreement</strong></li>
        </div>
        """,unsafe_allow_html=True)
        result = second_tab()

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
        file_upload = st.file_uploader("Upload your evidence here:", type=["png", "jpg", "jpeg"]) 
        if file_upload:
            with st.expander("Uploaded_Evidence"):
                st.image(file_upload)
            img = get_image(file_upload)
            user_input = st.text_input("Enter your Question here:")
            if user_input:
                with st.spinner("Analyzing your provided evidence"):
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content([user_input, img], stream=True)
                    response.resolve()
                    st.write(response.text)
        

if __name__ == '__main__':
    main()