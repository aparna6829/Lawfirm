import os
from pathlib import Path
import logging
import json
import nest_asyncio
from typing import List, Optional
import asyncio
from llama_index.core.workflow import Event, StartEvent, StopEvent, Context, Workflow, step
from llama_index.core.llms import LLM
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.schema import Document
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_parse import LlamaParse
from pydantic import BaseModel, Field
import streamlit as st
from langchain_community.llms.openai import OpenAI

asyncio.set_event_loop(asyncio.new_event_loop())
nest_asyncio.apply()




llm = OpenAI(model="gpt-4o-mini", api_key=st.secrets["OPENAI_API_KEY"])

# Configure logging
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

# Define paths
STORAGE_CACHE_DIR = Path('./Contractcache')
DATA_PATH = Path(r'data')

# Ensure directories exist
STORAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Initialize the embedding model
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def create_index(data_path: Path, cache_dir: Path) -> VectorStoreIndex:
    """Create a new index or load existing one from cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("Creating new index...")
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    documents = SimpleDirectoryReader(input_dir=str(data_path)).load_data()
    storage_context = StorageContext.from_defaults()
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=embed_model, show_progress=True)
    index.storage_context.persist(persist_dir=str(cache_dir))
    print(f"Index created and saved to: {cache_dir}")
    return index

index = create_index(DATA_PATH, STORAGE_CACHE_DIR)
retriever = index.as_retriever(similarity_top_k=2)

# Model definitions
class ContractClause(BaseModel):
    clause_text: str = Field(..., description="The exact text of the clause.")
    mentions_data_processing: bool = Field(False, description="True if the clause involves personal data collection or usage.")
    mentions_data_transfer: bool = Field(False, description="True if the clause involves transferring personal data.")
    requires_consent: bool = Field(False, description="True if the clause explicitly states that user consent is needed.")
    specifies_purpose: bool = Field(False, description="True if the clause specifies a clear purpose.")
    mentions_safeguards: bool = Field(False, description="True if the clause mentions security measures.")

class ContractExtraction(BaseModel):
    vendor_name: Optional[str] = Field(None, description="The vendor's name if identifiable.")
    effective_date: Optional[str] = Field(None, description="The effective date of the agreement.")
    governing_law: Optional[str] = Field(None, description="The governing law of the contract.")
    clauses: List[ContractClause] = Field(..., description="List of extracted clauses.")

class GuidelineMatch(BaseModel):
    guideline_text: str = Field(..., description="The relevant guideline excerpt.")
    similarity_score: float = Field(..., description="Similarity score between 0 and 1.")
    relevance_explanation: Optional[str] = Field(None, description="Relevance explanation.")

class ClauseComplianceCheck(BaseModel):
    clause_text: str = Field(..., description="The exact text of the clause.")
    matched_guideline: Optional[GuidelineMatch] = Field(None, description="The most relevant guideline.")
    compliant: bool = Field(..., description="Compliance status.")
    notes: Optional[str] = Field(None, description="Additional notes.")

class ComplianceReport(BaseModel):
    vendor_name: Optional[str] = Field(None, description="The vendor's name.")
    overall_compliant: bool = Field(..., description="Overall compliance status.")
    summary_notes: Optional[str] = Field(None, description="Summary notes.")


# Prompts
CONTRACT_EXTRACT_PROMPT = """
You are given contract data below. 
Please extract out relevant information from the contract into the defined schema - the schema is defined as a function call.

{contract_data}
"""

CONTRACT_MATCH_PROMPT = """
Given the following contract clause and the corresponding relevant guideline text, evaluate the compliance 
and provide a JSON object that matches the ClauseComplianceCheck schema.

**Contract Clause:**
{clause_text}

**Matched Guideline Text(s):**
{guideline_text}
"""

COMPLIANCE_REPORT_SYSTEM_PROMPT = """
You are a compliance reporting assistant. Your task is to generate a final compliance report 
based on the results of clause compliance checks against a given set of guidelines. 

Analyze the provided compliance results and produce a structured report according to the specified schema. 
Ensure that if there are no noncompliant clauses, the report clearly indicates full compliance.
"""

COMPLIANCE_REPORT_USER_PROMPT = """
A set of clauses within a contract were checked against GDPR compliance guidelines for the following vendor: {vendor_name}. 
The set of noncompliant clauses are given below.

Each section includes:
- **Clause:** The exact text of the contract clause.
- **Guideline:** The relevant GDPR guideline text.
- **Compliance Status:** Should be `False` for noncompliant clauses.
- **Notes:** Additional information or explanations.

{compliance_results}

Based on the above compliance results, generate a final compliance report following the `ComplianceReport` schema below. 
If there are no noncompliant clauses, the report should indicate that the contract is fully compliant.
"""


class ContractExtractionEvent(Event):
    contract_extraction: ContractExtraction
    contract_path: str
    vendor_name: Optional[str] = None

class MatchGuidelineEvent(Event):
    clause: ContractClause
    vendor_name: Optional[str] = None
    contract_path: str  # Add this to pass through the contract path

class MatchGuidelineResultEvent(Event):
    result: ClauseComplianceCheck
    contract_path: str  # Add this to pass through the contract path

class GenerateReportEvent(Event):
    match_results: List[ClauseComplianceCheck]

class LogEvent(Event):
    msg: str
    delta: bool = False

class ContractReviewWorkflow(Workflow):
    """Contract review workflow."""

    def __init__(
        self,
        parser: LlamaParse,
        guideline_retriever: BaseRetriever,
        llm: LLM | None = None,
        similarity_top_k: int = 20,
        output_dir: str = "data_out",
        **kwargs,
    ) -> None:
        """Init params."""
        super().__init__(**kwargs)

        self.parser = parser
        self.guideline_retriever = guideline_retriever
        self.llm = llm or OpenAI(model="gpt-4o-mini")
        self.similarity_top_k = similarity_top_k

        # if not exists, create
        out_path = Path(output_dir) / "workflow_output"
        if not out_path.exists():
            out_path.mkdir(parents=True, exist_ok=True)
            os.chmod(str(out_path), 0o0777)
        self.output_dir = out_path

    def _get_contract_specific_paths(self, contract_path: str | Path) -> tuple[Path, Path]:
        """Generate contract-specific cache file paths based on contract filename."""
        contract_name = Path(contract_path).stem
        contract_extraction_path = self.output_dir / f"{contract_name}_contract_extraction.json"
        match_results_path = self.output_dir / f"{contract_name}_match_results.jsonl"
        return contract_extraction_path, match_results_path

    @step
    async def parse_contract(
        self, ctx: Context, ev: StartEvent
    ) -> ContractExtractionEvent:
        # Get contract-specific cache paths
        contract_extraction_path, _ = self._get_contract_specific_paths(ev.contract_path)
        
        if self._verbose:
            ctx.write_event_to_stream(
                LogEvent(msg=f">> Using cache path: {contract_extraction_path}")
            )
        
        if contract_extraction_path.exists():
            if self._verbose:
                ctx.write_event_to_stream(LogEvent(msg=">> Loading contract from cache"))
            contract_extraction_dict = json.load(open(str(contract_extraction_path), "r"))
            contract_extraction = ContractExtraction.model_validate(contract_extraction_dict)
        else:
            if self._verbose:
                ctx.write_event_to_stream(LogEvent(msg=">> Reading contract"))

            docs = SimpleDirectoryReader(input_files=[ev.contract_path]).load_data()

            # extract from contract
            prompt = ChatPromptTemplate.from_messages([
                ("user", CONTRACT_EXTRACT_PROMPT)
            ])
            contract_extraction = await llm.astructured_predict(
                ContractExtraction,
                prompt,
                contract_data="\n".join([d.get_content(metadata_mode="all") for d in docs])
            )
            if not isinstance(contract_extraction, ContractExtraction):
                raise ValueError(f"Invalid extraction from contract: {contract_extraction}")
            # save output template to file
            with open(contract_extraction_path, "w") as fp:
                fp.write(contract_extraction.model_dump_json())
        
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=f">> Contract data: {contract_extraction.dict()}"))

        return ContractExtractionEvent(
            contract_extraction=contract_extraction,
            contract_path=str(ev.contract_path)  # Pass the contract path
        )


    
    @step
    async def dispatch_guideline_match(
        self, ctx: Context, ev: ContractExtractionEvent
    ) -> MatchGuidelineEvent:
        """For each clause in the contract, find relevant guidelines."""
        await ctx.set("num_clauses", len(ev.contract_extraction.clauses))
        await ctx.set("vendor_name", ev.contract_extraction.vendor_name)
        await ctx.set("contract_path", ev.contract_path)
        
        for clause in ev.contract_extraction.clauses:
            ctx.send_event(
                MatchGuidelineEvent(
                    clause=clause,
                    vendor_name=ev.contract_extraction.vendor_name,
                    contract_path=ev.contract_path  # Pass through the contract path
                )
            )

    @step
    async def handle_guideline_match(
        self, ctx: Context, ev: MatchGuidelineEvent
    ) -> MatchGuidelineResultEvent:
        """Handle matching clause against guideline."""
        query = f"""\
Please find the relevant guideline from {ev.vendor_name} that aligns with the following contract clause:

{ev.clause.clause_text}
"""
        guideline_docs = self.guideline_retriever.retrieve(query)
        guideline_text = "\n\n".join([g.get_content() for g in guideline_docs])
        
        if self._verbose:
            ctx.write_event_to_stream(
                LogEvent(msg=f">> Found guidelines: {guideline_text[:200]}...")
            )
        
        prompt = ChatPromptTemplate.from_messages([
            ("user", CONTRACT_MATCH_PROMPT)
        ])
        compliance_output = await llm.astructured_predict(
            ClauseComplianceCheck,
            prompt,
            clause_text=ev.clause.model_dump_json(),
            guideline_text=guideline_text
        )
        
        if not isinstance(compliance_output, ClauseComplianceCheck):
            raise ValueError(f"Invalid compliance check: {compliance_output}")

        return MatchGuidelineResultEvent(
            result=compliance_output,
            contract_path=ev.contract_path  # Pass through the contract path
        )

    @step
    async def gather_guideline_match(
        self, ctx: Context, ev: MatchGuidelineResultEvent
    ) -> GenerateReportEvent:
        """Handle matching clause against guideline."""
        num_clauses = await ctx.get("num_clauses")
        contract_path = await ctx.get("contract_path")
        events = ctx.collect_events(ev, [MatchGuidelineResultEvent] * num_clauses)
        
        if events is None:
            return

        match_results = [e.result for e in events]
        
        # Get contract-specific match results path
        _, match_results_path = self._get_contract_specific_paths(contract_path)
        
        if self._verbose:
            ctx.write_event_to_stream(
                LogEvent(msg=f">> Saving match results to: {match_results_path}")
            )
        
        # Ensure directory exists
        match_results_path.parent.mkdir(parents=True, exist_ok=True)
        
        # save match results with proper error handling
        try:
            with open(match_results_path, "w") as fp:
                for mr in match_results:
                    fp.write(mr.model_dump_json() + "\n")
            if self._verbose:
                ctx.write_event_to_stream(
                    LogEvent(msg=f">> Successfully saved match results to {match_results_path}")
                )
        except Exception as e:
            if self._verbose:
                ctx.write_event_to_stream(
                    LogEvent(msg=f">> Error saving match results: {str(e)}")
                )
            raise
            
        return GenerateReportEvent(match_results=[e.result for e in events])
    @step
    async def generate_output(
        self, ctx: Context, ev: GenerateReportEvent
    ) -> StopEvent:
        if self._verbose:
            ctx.write_event_to_stream(LogEvent(msg=">> Generating Compliance Report"))

        # if all clauses are compliant, return a compliant result
        non_compliant_results = [r for r in ev.match_results if not r.compliant]

        # generate compliance results string
        result_tmpl = """
1. **Clause**: {clause}
2. **Guideline:** {guideline}
3. **Compliance Status:** {compliance_status}
4. **Notes:** {notes}
"""
        non_compliant_strings = []
        for nr in non_compliant_results:
            non_compliant_strings.append(
                result_tmpl.format(
                    clause=nr.clause_text,
                    guideline=nr.matched_guideline.guideline_text,
                    compliance_status=nr.compliant,
                    notes=nr.notes
                )
            )
        non_compliant_str = "\n\n".join(non_compliant_strings)

        prompt = ChatPromptTemplate.from_messages([
            ("system", COMPLIANCE_REPORT_SYSTEM_PROMPT),
            ("user", COMPLIANCE_REPORT_USER_PROMPT)
        ])
        compliance_report = await llm.astructured_predict(
            ComplianceReport,
            prompt,
            compliance_results=non_compliant_str,
            vendor_name=await ctx.get("vendor_name")
        )

        return StopEvent(result={"report": compliance_report, "non_compliant_results": non_compliant_results})


parser = LlamaParse(result_type="markdown", api_key=st.secrets["LLAMA_KEY"])  # Replace with your API key






nest_asyncio.apply()
asyncio.set_event_loop(asyncio.new_event_loop())

compliance_workflow = ContractReviewWorkflow(
    parser=parser,
    guideline_retriever=retriever,
    llm=llm,
    # verbose=True,
    timeout=None,  # don't worry about timeout to make sure it completes
)


async def run_workflow_async(compliance_workflow: Workflow, contract_path: Path) -> dict:
    """Asynchronous function to run the workflow"""
    print(f"Starting workflow for contract: {contract_path}")
    handler = compliance_workflow.run(contract_path=str(contract_path))
    
    # Handle event streaming
    async for event in handler.stream_events():
        if isinstance(event, LogEvent):
            if event.delta:
                print(event.msg, end="")
            else:
                print(event.msg)
    
    # Get final results
    return await handler

def run_workflow(compliance_workflow: Workflow, contract_path: Path) -> dict:
    """Synchronous wrapper for running the workflow"""
    # Apply nest_asyncio to allow nested event loops
    nest_asyncio.apply()
    
    # Create new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Run the async workflow in the event loop
        return loop.run_until_complete(run_workflow_async(compliance_workflow, contract_path))
    finally:
        # Clean up
        loop.close()

