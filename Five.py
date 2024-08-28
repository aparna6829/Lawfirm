import streamlit as st
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

Gemini = st.secrets["GOOGLE_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=Gemini)


def get_response(question):
    template = f"""
                As a legal expert, your primary task is to assist lawyers and paralegals by providing accurate, relevant, and well-structured information about their cases. This will aid them in making informed legal decisions and arguments. Please use the following context to craft a precise and informative response:
                
                **Lawyer's Question:** {question}

                **Instructions:**
                Your response should be structured in the following format to ensure clarity and thoroughness:

                1. **Legal Principle:**
                
                - Provide a brief and clear description of the main legal rule, doctrine, or statute that is relevant to the lawyer's question. This should include the foundational legal principles that underpin the issue at hand.

                2. **Case Reference:**
                
                - Cite a relevant case that supports or illustrates the legal principle discussed. Include the full name of the case and the official citation. If possible, select a case that is widely recognized or directly applicable to the jurisdiction of the query.
                - Provide the valid and Hyperlink of the case for user reference.

                3. **Implications:**
                
                - Discuss the significance of the legal principle in the broader context of the law. Explain how this principle affects the legal landscape, including any potential consequences or precedents that it sets. Consider the practical implications for both current and future cases.

                4. **Court Decision:**
                
                - Summarize the court’s ruling in the cited case, emphasizing how the court applied the legal principle to the facts of the case. Highlight any key reasoning or legal interpretations made by the court that are pertinent to the lawyer's query.

                5. **Summary:**
                
                - Provide a concise overall summary that integrates the legal principle, case reference, implications, and court decision. This section should distill the information into a clear and actionable insight that directly addresses the lawyer’s question.

                **Guidance:**
                - Ensure your response is clear, concise, and directly relevant to the lawyer's query.
                - Use legal terminology appropriately, but also explain complex concepts in a way that is accessible to those who may not have specialized knowledge.
                - Strive to deliver an answer that is both informative and practically useful for the lawyer’s case preparation and strategy.

                - When addressing questions related to U.S. state laws, be specific to the state in question and provide information on permitting requirements, notice, wildlife management, and hunting laws as needed.

                    This template is designed to support lawyers and paralegals in conducting thorough legal research and developing well-founded legal arguments, particularly in cases involving U.S. state laws.
                
                """

                                
                    
    prompt = PromptTemplate(template=template, input_variables=["question"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    return llm_chain
