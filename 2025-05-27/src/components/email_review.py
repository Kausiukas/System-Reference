import streamlit as st
from typing import Dict, Any, Optional, Tuple, List
import json
from datetime import datetime
import os

class EmailReviewSystem:
    def __init__(self, base_path: str = "data/email_drafts"):
        """Initialize email review system."""
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
    def save_draft(
        self,
        email_content: str,
        client_profile: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Save email draft for review."""
        draft_id = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{client_profile['client_id']}"
        
        draft_data = {
            "draft_id": draft_id,
            "content": email_content,
            "client_profile": client_profile,
            "metadata": metadata,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "reviewed_at": None,
            "reviewer_comments": None,
            "final_version": None
        }
        
        file_path = os.path.join(self.base_path, f"{draft_id}.json")
        with open(file_path, 'w') as f:
            json.dump(draft_data, f, indent=2)
            
        return draft_id
    
    def get_pending_drafts(self) -> List[Dict[str, Any]]:
        """Get list of pending email drafts."""
        drafts = []
        for file_name in os.listdir(self.base_path):
            if not file_name.endswith('.json'):
                continue
                
            file_path = os.path.join(self.base_path, file_name)
            with open(file_path, 'r') as f:
                draft = json.load(f)
                if draft['status'] == 'pending':
                    drafts.append(draft)
        
        return sorted(drafts, key=lambda x: x['created_at'], reverse=True)
    
    def review_draft(
        self,
        draft_id: str,
        approved: bool,
        comments: str,
        edited_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Review and update email draft."""
        file_path = os.path.join(self.base_path, f"{draft_id}.json")
        
        with open(file_path, 'r') as f:
            draft = json.load(f)
        
        draft['status'] = 'approved' if approved else 'rejected'
        draft['reviewed_at'] = datetime.now().isoformat()
        draft['reviewer_comments'] = comments
        
        if edited_content:
            draft['final_version'] = edited_content
        else:
            draft['final_version'] = draft['content']
        
        with open(file_path, 'w') as f:
            json.dump(draft, f, indent=2)
        
        return draft

def render_email_review_interface() -> None:
    """Render the email review interface in Streamlit."""
    st.header("✍️ Email Review System")
    
    # Initialize review system
    review_system = EmailReviewSystem()
    
    # Get pending drafts
    pending_drafts = review_system.get_pending_drafts()
    
    if not pending_drafts:
        st.info("No pending email drafts to review.")
        return
    
    st.subheader(f"📬 Pending Drafts ({len(pending_drafts)})")
    
    for draft in pending_drafts:
        with st.expander(f"📧 Draft for {draft['client_profile'].get('company_name', 'Unknown Company')}"):
            # Display client information
            st.markdown("### Client Information")
            st.json(draft['client_profile'])
            
            # Display original content
            st.markdown("### Original Draft")
            original_content = draft['content']
            st.text_area(
                "Original Content",
                value=original_content,
                height=200,
                disabled=True
            )
            
            # Editable version
            st.markdown("### Edit Email (if needed)")
            edited_content = st.text_area(
                "Edit Content",
                value=original_content,
                height=200,
                key=f"edit_{draft['draft_id']}"
            )
            
            # Review inputs
            col1, col2 = st.columns(2)
            
            with col1:
                approved = st.radio(
                    "Decision",
                    options=["Approve", "Reject"],
                    key=f"decision_{draft['draft_id']}"
                )
            
            with col2:
                comments = st.text_area(
                    "Review Comments",
                    height=100,
                    key=f"comments_{draft['draft_id']}"
                )
            
            # Submit review
            if st.button("Submit Review", key=f"submit_{draft['draft_id']}"):
                try:
                    review_system.review_draft(
                        draft['draft_id'],
                        approved == "Approve",
                        comments,
                        edited_content if edited_content != original_content else None
                    )
                    st.success("Review submitted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error submitting review: {str(e)}")

def get_approved_email(draft_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Get approved email content and reviewer comments."""
    review_system = EmailReviewSystem()
    file_path = os.path.join(review_system.base_path, f"{draft_id}.json")
    
    if not os.path.exists(file_path):
        return False, None, "Draft not found"
    
    with open(file_path, 'r') as f:
        draft = json.load(f)
    
    if draft['status'] == 'approved':
        return True, draft['final_version'], draft['reviewer_comments']
    elif draft['status'] == 'rejected':
        return False, None, draft['reviewer_comments']
    else:
        return False, None, "Draft is still pending review" 