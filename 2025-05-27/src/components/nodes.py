from typing import Tuple, Dict, Any
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import HumanMessage
from .state import ClientState
from src.utils.vector_store import VectorStore
from ..utils.llm_utils import LLMHelper
from ..utils.helpers import save_client_profile, load_client_profile
import extract_msg
import os
from datetime import datetime

# Initialize utilities
vector_store = VectorStore()
llm_helper = LLMHelper()

def create_export_emails_node():
    """Node for exporting and processing email content."""
    async def _export_emails(state: ClientState) -> Dict[str, Any]:
        if not state.raw_content:
            return {}
            
        try:
            # Extract email content if it's an MSG file
            if isinstance(state.raw_content, bytes) and state.raw_content.startswith(b'D0CF11E0'):
                msg = extract_msg.Message(state.raw_content)
                content = msg.body
                metadata = {
                    "subject": msg.subject,
                    "sender": msg.sender,
                    "date": msg.date.isoformat() if msg.date else None,
                    "type": "email"
                }
            else:
                content = state.raw_content
                metadata = {
                    "type": "text",
                    "date": datetime.now().isoformat()
                }
            
            return {
                "raw_content": content,
                "metadata": metadata
            }
        except Exception as e:
            print(f"Error processing email: {str(e)}")
            return {"raw_content": state.raw_content}
    return _export_emails

def create_preprocess_node():
    """Node for preprocessing and chunking content."""
    async def _preprocess(state: ClientState) -> Dict[str, Any]:
        if not state.raw_content:
            return {}
            
        # Extract structured information
        profile_info = llm_helper.extract_profile_info(state.raw_content)
        
        # Add to vector store
        metadata = {
            "client_id": state.client_id,
            "date": datetime.now().isoformat(),
            "type": "communication"
        }
        
        vector_store.add_texts(
            texts=[state.raw_content],
            metadatas=[metadata]
        )
        
        return {
            "company_name": profile_info.get("company_name"),
            "contacts": profile_info.get("contacts", []),
            "needs": profile_info.get("needs", [])
        }
    return _preprocess

def create_memory_search_node():
    """Node for searching relevant history in vector store."""
    async def _search_memory(state: ClientState) -> Dict[str, Any]:
        if not state.client_id:
            return {"relevant_history": []}
            
        # Search for relevant past interactions
        results = vector_store.similarity_search(
            query=state.raw_content,
            k=5,
            filter_criteria={"client_id": state.client_id}
        )
        
        return {"relevant_history": results}
    return _search_memory

def create_summarize_node():
    """Node for generating current status summary."""
    async def _summarize(state: ClientState) -> Dict[str, Any]:
        if not state.raw_content:
            return {}
            
        # Get summary with context
        summary = llm_helper.summarize_content(
            content=state.raw_content,
            context=state.relevant_history
        )
        
        return {
            "current_summary": summary.get("key_points", []),
            "sentiment": summary.get("sentiment"),
            "needs": summary.get("needs", []),
            "next_steps": summary.get("next_steps", [])
        }
    return _summarize

def create_profile_update_node():
    """Node for updating client profile state."""
    async def _update_profile(state: ClientState) -> Dict[str, Any]:
        # Load existing profile if any
        existing_profile = load_client_profile(state.client_id) if state.client_id else {}
        
        # Merge new information
        updated_profile = {
            "client_id": state.client_id,
            "company_name": state.company_name or existing_profile.get("company_name"),
            "contacts": state.contacts + existing_profile.get("contacts", []),
            "needs": list(set(state.needs + existing_profile.get("needs", []))),
            "sentiment": state.sentiment,
            "last_interaction": datetime.now().isoformat(),
            "interaction_history": existing_profile.get("interaction_history", []) + [{
                "date": datetime.now().isoformat(),
                "summary": state.current_summary,
                "sentiment": state.sentiment
            }]
        }
        
        # Save updated profile
        if state.client_id:
            save_client_profile(state.client_id, updated_profile)
        
        return updated_profile
    return _update_profile

def create_sales_status_node():
    """Node for tracking sales pipeline status."""
    async def _track_sales_status(state: ClientState) -> Dict[str, Any]:
        if not state.raw_content or not state.client_id:
            return {"sales_stage": "lead"}
            
        # Classify sales stage
        sales_stage = llm_helper.classify_sales_stage(
            profile=load_client_profile(state.client_id),
            recent_interaction=state.raw_content
        )
        
        return {"sales_stage": sales_stage}
    return _track_sales_status

def create_next_step_node():
    """Node for suggesting next steps."""
    async def _suggest_next_step(state: ClientState) -> Dict[str, Any]:
        if not state.current_summary:
            return {"next_steps": []}
            
        # Use existing next steps from summary
        return {"next_steps": state.next_steps}
    return _suggest_next_step

def create_email_generation_node():
    """Node for generating email content."""
    async def _generate_email(state: ClientState) -> Dict[str, Any]:
        if not state.client_id:
            return {}
            
        # Generate email draft
        email_content = llm_helper.generate_email_draft(
            client_profile=load_client_profile(state.client_id),
            context=state.relevant_history,
            purpose="follow_up"
        )
        
        return {"generated_email": email_content}
    return _generate_email

def create_save_notify_node():
    """Node for saving results and notifying user."""
    async def _save_and_notify(state: ClientState) -> Dict[str, Any]:
        if state.client_id:
            # Final profile update
            profile = load_client_profile(state.client_id)
            profile["last_email_generated"] = datetime.now().isoformat()
            save_client_profile(state.client_id, profile)
        
        return {}
    return _save_and_notify

def build_graph():
    """Build the processing graph."""
    # Initialize components
    chat = ChatOpenAI(temperature=0)
    vector_store = VectorStore()
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that processes email attachments."),
        ("user", "Please analyze this file: {file_content}")
    ])
    
    # Build the chain
    chain = (
        {"file_content": RunnablePassthrough()}
        | prompt
        | chat
        | StrOutputParser()
    )
    
    return chain

def build_graph() -> StateGraph:
    """Builds and returns the complete workflow graph."""
    
    # Initialize graph
    workflow = StateGraph(ClientState)
    
    # Add nodes
    workflow.add_node("export_emails", create_export_emails_node())
    workflow.add_node("preprocess", create_preprocess_node())
    workflow.add_node("search_memory", create_memory_search_node())
    workflow.add_node("summarize", create_summarize_node())
    workflow.add_node("update_profile", create_profile_update_node())
    workflow.add_node("track_sales", create_sales_status_node())
    workflow.add_node("suggest_next_step", create_next_step_node())
    workflow.add_node("generate_email", create_email_generation_node())
    workflow.add_node("save_notify", create_save_notify_node())
    
    # Define edges
    workflow.add_edge("export_emails", "preprocess")
    workflow.add_edge("preprocess", "search_memory")
    workflow.add_edge("search_memory", "summarize")
    workflow.add_edge("summarize", "update_profile")
    workflow.add_edge("update_profile", "track_sales")
    workflow.add_edge("track_sales", "suggest_next_step")
    workflow.add_edge("suggest_next_step", "generate_email")
    workflow.add_edge("generate_email", "save_notify")
    
    # Set entry point
    workflow.set_entry_point("export_emails")
    
    return workflow 