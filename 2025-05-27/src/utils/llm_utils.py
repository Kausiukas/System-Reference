from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json

class LLMHelper:
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0):
        """Initialize LLM helper."""
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature
        )

    def summarize_content(self, content: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Summarize content with optional context."""
        system_prompt = """You are an AI assistant helping to analyze client communications.
        Summarize the key points, focusing on:
        1. Client needs and pain points
        2. Sentiment and engagement level
        3. Current stage in sales process
        4. Action items or follow-ups needed
        
        Return a JSON object with these fields."""

        context_str = ""
        if context:
            context_str = "\n\nRelevant context from previous communications:\n"
            for item in context:
                context_str += f"- {item['content']}\n"

        human_prompt = f"""Please analyze this communication:{context_str}

        Content to analyze:
        {content}

        Provide a structured summary in JSON format with the following fields:
        - key_points: list of main points discussed
        - needs: list of identified client needs
        - sentiment: overall sentiment (positive/neutral/negative)
        - sales_stage: current stage in sales process
        - next_steps: suggested follow-up actions"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        return json.loads(response.content)

    def generate_email_draft(
        self,
        client_profile: Dict[str, Any],
        context: Optional[List[Dict]] = None,
        purpose: str = "follow_up"
    ) -> str:
        """Generate an email draft based on client profile and context."""
        system_prompt = """You are an AI assistant helping to draft professional client communications.
        Create personalized, context-aware emails that maintain continuity with previous interactions."""

        context_str = ""
        if context:
            context_str = "\nRecent interactions:\n"
            for item in context:
                context_str += f"- {item['content']}\n"

        profile_str = json.dumps(client_profile, indent=2)

        human_prompt = f"""Draft a professional email for this client.

        Client Profile:
        {profile_str}

        {context_str}

        Purpose: {purpose}

        The email should:
        1. Be professional and personalized
        2. Reference relevant previous interactions
        3. Address identified needs
        4. Include clear next steps
        5. Maintain appropriate tone based on relationship stage"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content

    def extract_profile_info(self, content: str) -> Dict[str, Any]:
        """Extract structured profile information from content."""
        system_prompt = """You are an AI assistant helping to extract structured client information.
        Analyze the content and extract key details about the client."""

        human_prompt = f"""Extract key client information from this content:

        {content}

        Return a JSON object with these fields:
        - company_name: company name if mentioned
        - contacts: list of contact persons with names and roles
        - needs: list of identified needs or interests
        - timeline: any mentioned timeframes or deadlines
        - budget: any budget-related information
        - technical_requirements: any technical specifications or requirements"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        return json.loads(response.content)

    def classify_sales_stage(self, profile: Dict[str, Any], recent_interaction: str) -> str:
        """Classify the current sales stage based on profile and recent interaction."""
        system_prompt = """You are an AI assistant helping to classify sales pipeline stages.
        Analyze the client profile and recent interaction to determine the current stage."""

        profile_str = json.dumps(profile, indent=2)

        human_prompt = f"""Determine the sales stage based on this information:

        Client Profile:
        {profile_str}

        Recent Interaction:
        {recent_interaction}

        Available stages:
        - lead: Initial contact or expression of interest
        - qualified: Needs identified and qualification confirmed
        - offered: Proposal or offer made
        - negotiating: In active negotiations
        - closed_won: Deal successfully closed
        - closed_lost: Opportunity lost or declined

        Return only the stage name as a string."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content.strip().lower()

    def create_prompt(self, template: str, input_variables: list) -> ChatPromptTemplate:
        """Create a chat prompt template."""
        return ChatPromptTemplate.from_template(template)
        
    def process_message(self, prompt: ChatPromptTemplate, variables: Dict[str, Any]) -> str:
        """Process a message using the LLM."""
        chain = prompt | self.llm
        return chain.invoke(variables) 