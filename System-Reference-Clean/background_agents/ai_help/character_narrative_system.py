"""
Character-Driven Narrative System for PyNarrative
Transforms codebase exploration into engaging character-driven stories
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import random

try:
    import pynarrative as pn
    PY_NARRATIVE_AVAILABLE = True
except ImportError:
    PY_NARRATIVE_AVAILABLE = False
    pn = None

from .pynarrative_agent import PyNarrativeAgent, NarrativeVisualizationRequest, NarrativeVisualizationResult

class CharacterRole(Enum):
    """Character roles for narrative generation"""
    DEVELOPER = "developer"
    CLIENT_SUPPORT = "client_support"
    ACCOUNT_MANAGER = "account_manager"
    LAWYER = "lawyer"
    GOVERNMENT_LEGISLATOR = "government_legislator"
    DATA_SCIENTIST = "data_scientist"
    SECURITY_ANALYST = "security_analyst"
    PROJECT_MANAGER = "project_manager"
    UX_DESIGNER = "ux_designer"
    SYSTEM_ADMIN = "system_admin"

class StoryArchetype(Enum):
    """Story archetypes for different narrative styles"""
    QUEST = "quest"
    MYSTERY = "mystery"
    TRANSFORMATION = "transformation"
    DEFENSE = "defense"
    LEGISLATION = "legislation"
    INVESTIGATION = "investigation"
    OPTIMIZATION = "optimization"
    INNOVATION = "innovation"
    COMPLIANCE = "compliance"
    STRATEGY = "strategy"

@dataclass
class CharacterProfile:
    """Character profile with personality, goals, and narrative style"""
    role: CharacterRole
    name: str
    background: str
    personality_traits: List[str]
    goals: List[str]
    challenges: List[str]
    success_metrics: List[str]
    narrative_style: str
    color_scheme: Dict[str, str]
    story_templates: List[str]
    expertise_areas: List[str]
    motivation: str
    conflict_type: str
    resolution_style: str

@dataclass
class StoryContext:
    """Context for story generation"""
    character: CharacterProfile
    target_element: str
    codebase_context: Dict[str, Any]
    user_goals: List[str]
    complexity_level: str
    time_constraint: str
    risk_factors: List[str]
    success_criteria: List[str]

@dataclass
class CharacterNarrativeResult:
    """Result of character-driven narrative creation"""
    success: bool
    story_title: str
    character_name: str
    story_html: str
    narrative_text: str
    character_arc: str
    goals_achieved: List[str]
    challenges_overcome: List[str]
    metrics_tracked: Dict[str, Any]
    story_metadata: Dict[str, Any]
    error_message: Optional[str] = None

class CharacterNarrativeSystem:
    """System for creating character-driven narratives using PyNarrative"""
    
    def __init__(self, pynarrative_agent: PyNarrativeAgent):
        self.agent = pynarrative_agent
        self.logger = logging.getLogger(__name__)
        self.characters = self._initialize_characters()
        self.story_archetypes = self._initialize_story_archetypes()
        self.narrative_templates = self._initialize_narrative_templates()
        
    def _initialize_characters(self) -> Dict[CharacterRole, CharacterProfile]:
        """Initialize character profiles"""
        return {
            CharacterRole.DEVELOPER: CharacterProfile(
                role=CharacterRole.DEVELOPER,
                name="Alex Chen",
                background="Senior Software Engineer with 8 years of experience in enterprise systems",
                personality_traits=["analytical", "curious", "detail-oriented", "problem-solver"],
                goals=["uncover hidden dependencies", "optimize performance", "understand legacy code"],
                challenges=["complex inheritance hierarchies", "undocumented APIs", "performance bottlenecks"],
                success_metrics=["code coverage", "performance improvement", "bug reduction"],
                narrative_style="technical detective story with code archaeology elements",
                color_scheme={"primary": "#2E86AB", "secondary": "#A23B72", "accent": "#F18F01", "highlight": "#C73E1D"},
                story_templates=["quest", "mystery", "transformation"],
                expertise_areas=["backend systems", "performance optimization", "code refactoring"],
                motivation="Master the codebase to build better, more maintainable systems",
                conflict_type="technical complexity vs. business requirements",
                resolution_style="iterative problem-solving with documentation"
            ),
            
            CharacterRole.CLIENT_SUPPORT: CharacterProfile(
                role=CharacterRole.CLIENT_SUPPORT,
                name="Sarah Martinez",
                background="Client Success Specialist with expertise in business intelligence tools",
                personality_traits=["empathetic", "patient", "solution-focused", "client-advocate"],
                goals=["increase client satisfaction", "reduce support tickets", "improve user experience"],
                challenges=["complex user workflows", "integration issues", "training gaps"],
                success_metrics=["client satisfaction score", "ticket resolution time", "feature adoption rate"],
                narrative_style="client journey story with business impact focus",
                color_scheme={"primary": "#4CAF50", "secondary": "#2196F3", "accent": "#FF9800", "highlight": "#9C27B0"},
                story_templates=["transformation", "optimization", "innovation"],
                expertise_areas=["user experience", "business processes", "client communication"],
                motivation="Empower clients to achieve their business goals through better software",
                conflict_type="user needs vs. system limitations",
                resolution_style="collaborative problem-solving with training"
            ),
            
            CharacterRole.ACCOUNT_MANAGER: CharacterProfile(
                role=CharacterRole.ACCOUNT_MANAGER,
                name="Michael Rodriguez",
                background="Senior Account Manager specializing in sales automation and CRM systems",
                personality_traits=["persuasive", "goal-oriented", "relationship-builder", "data-driven"],
                goals=["increase sales efficiency", "improve lead conversion", "streamline sales processes"],
                challenges=["manual processes", "data silos", "integration complexity"],
                success_metrics=["sales velocity", "conversion rates", "deal size"],
                narrative_style="sales journey story with automation transformation",
                color_scheme={"primary": "#FF6B35", "secondary": "#004E89", "accent": "#1A936F", "highlight": "#C06E52"},
                story_templates=["transformation", "optimization", "strategy"],
                expertise_areas=["sales processes", "CRM systems", "business development"],
                motivation="Transform sales teams into high-performing, data-driven organizations",
                conflict_type="manual processes vs. automation opportunities",
                resolution_style="process optimization with technology integration"
            ),
            
            CharacterRole.LAWYER: CharacterProfile(
                role=CharacterRole.LAWYER,
                name="Jennifer Thompson",
                background="Corporate Attorney specializing in financial regulations and compliance",
                personality_traits=["analytical", "thorough", "risk-aware", "detail-oriented"],
                goals=["protect client interests", "ensure compliance", "mitigate legal risks"],
                challenges=["regulatory complexity", "data privacy requirements", "contract interpretation"],
                success_metrics=["compliance rate", "risk mitigation", "client protection"],
                narrative_style="legal defense story with regulatory compliance focus",
                color_scheme={"primary": "#2C3E50", "secondary": "#E74C3C", "accent": "#F39C12", "highlight": "#8E44AD"},
                story_templates=["defense", "compliance", "investigation"],
                expertise_areas=["financial regulations", "data privacy", "contract law"],
                motivation="Safeguard client financial interests through comprehensive legal analysis",
                conflict_type="business needs vs. regulatory requirements",
                resolution_style="risk assessment with compliance framework"
            ),
            
            CharacterRole.GOVERNMENT_LEGISLATOR: CharacterProfile(
                role=CharacterRole.GOVERNMENT_LEGISLATOR,
                name="Congresswoman Elizabeth Park",
                background="Legislator with focus on technology policy and digital transformation",
                personality_traits=["strategic", "collaborative", "public-service-oriented", "evidence-based"],
                goals=["pass effective legislation", "improve public services", "ensure transparency"],
                challenges=["stakeholder alignment", "technical complexity", "public scrutiny"],
                success_metrics=["bill passage rate", "public support", "implementation success"],
                narrative_style="legislative journey story with public impact focus",
                color_scheme={"primary": "#34495E", "secondary": "#3498DB", "accent": "#E67E22", "highlight": "#27AE60"},
                story_templates=["legislation", "strategy", "transformation"],
                expertise_areas=["public policy", "technology governance", "stakeholder management"],
                motivation="Create effective legislation that serves the public interest",
                conflict_type="diverse stakeholder needs vs. legislative constraints",
                resolution_style="consensus-building with evidence-based decision making"
            ),
            
            CharacterRole.DATA_SCIENTIST: CharacterProfile(
                role=CharacterRole.DATA_SCIENTIST,
                name="Dr. David Kim",
                background="Lead Data Scientist with expertise in machine learning and analytics",
                personality_traits=["analytical", "innovative", "data-driven", "experimental"],
                goals=["extract insights", "build predictive models", "optimize algorithms"],
                challenges=["data quality", "model complexity", "interpretability"],
                success_metrics=["model accuracy", "insight generation", "business impact"],
                narrative_style="scientific discovery story with data exploration",
                color_scheme={"primary": "#8E44AD", "secondary": "#2980B9", "accent": "#E67E22", "highlight": "#27AE60"},
                story_templates=["investigation", "innovation", "optimization"],
                expertise_areas=["machine learning", "statistical analysis", "data engineering"],
                motivation="Transform data into actionable insights that drive business decisions",
                conflict_type="model complexity vs. interpretability",
                resolution_style="iterative experimentation with validation"
            ),
            
            CharacterRole.SECURITY_ANALYST: CharacterProfile(
                role=CharacterRole.SECURITY_ANALYST,
                name="Marcus Johnson",
                background="Cybersecurity Specialist with expertise in threat detection and incident response",
                personality_traits=["vigilant", "methodical", "risk-aware", "detail-oriented"],
                goals=["identify vulnerabilities", "prevent breaches", "ensure compliance"],
                challenges=["evolving threats", "false positives", "resource constraints"],
                success_metrics=["threat detection rate", "incident response time", "vulnerability reduction"],
                narrative_style="security investigation story with threat hunting",
                color_scheme={"primary": "#E74C3C", "secondary": "#2C3E50", "accent": "#F39C12", "highlight": "#27AE60"},
                story_templates=["investigation", "defense", "compliance"],
                expertise_areas=["threat analysis", "incident response", "security architecture"],
                motivation="Protect systems and data from evolving cyber threats",
                conflict_type="security requirements vs. usability",
                resolution_style="risk-based approach with continuous monitoring"
            ),
            
            CharacterRole.PROJECT_MANAGER: CharacterProfile(
                role=CharacterRole.PROJECT_MANAGER,
                name="Lisa Chen",
                background="Senior Project Manager with expertise in agile methodologies and team leadership",
                personality_traits=["organized", "communicative", "results-driven", "team-oriented"],
                goals=["deliver on time", "manage resources", "ensure quality"],
                challenges=["scope creep", "resource constraints", "stakeholder alignment"],
                success_metrics=["on-time delivery", "budget adherence", "team satisfaction"],
                narrative_style="project journey story with team collaboration",
                color_scheme={"primary": "#3498DB", "secondary": "#2ECC71", "accent": "#F39C12", "highlight": "#E74C3C"},
                story_templates=["strategy", "transformation", "optimization"],
                expertise_areas=["project planning", "team leadership", "stakeholder management"],
                motivation="Lead teams to successful project delivery while fostering collaboration",
                conflict_type="project constraints vs. stakeholder expectations",
                resolution_style="collaborative planning with clear communication"
            ),
            
            CharacterRole.UX_DESIGNER: CharacterProfile(
                role=CharacterRole.UX_DESIGNER,
                name="Emma Wilson",
                background="Senior UX Designer with expertise in user research and interface design",
                personality_traits=["creative", "user-focused", "empathic", "iterative"],
                goals=["improve user experience", "increase usability", "drive engagement"],
                challenges=["user needs complexity", "technical constraints", "design consistency"],
                success_metrics=["user satisfaction", "task completion rate", "engagement metrics"],
                narrative_style="user journey story with design thinking",
                color_scheme={"primary": "#9B59B6", "secondary": "#3498DB", "accent": "#E67E22", "highlight": "#2ECC71"},
                story_templates=["innovation", "transformation", "optimization"],
                expertise_areas=["user research", "interface design", "usability testing"],
                motivation="Create intuitive and engaging user experiences that solve real problems",
                conflict_type="user needs vs. technical constraints",
                resolution_style="user-centered design with iterative testing"
            ),
            
            CharacterRole.SYSTEM_ADMIN: CharacterProfile(
                role=CharacterRole.SYSTEM_ADMIN,
                name="Robert Davis",
                background="System Administrator with expertise in infrastructure management and automation",
                personality_traits=["reliable", "efficient", "problem-solver", "automation-focused"],
                goals=["ensure system reliability", "optimize performance", "reduce manual work"],
                challenges=["system complexity", "scaling issues", "maintenance overhead"],
                success_metrics=["system uptime", "performance metrics", "automation coverage"],
                narrative_style="infrastructure optimization story with automation focus",
                color_scheme={"primary": "#34495E", "secondary": "#7F8C8D", "accent": "#F39C12", "highlight": "#27AE60"},
                story_templates=["optimization", "transformation", "strategy"],
                expertise_areas=["infrastructure management", "automation", "performance tuning"],
                motivation="Build reliable, scalable, and efficient systems through automation",
                conflict_type="system complexity vs. operational efficiency",
                resolution_style="automation-first approach with monitoring"
            )
        }
    
    def _initialize_story_archetypes(self) -> Dict[StoryArchetype, Dict[str, Any]]:
        """Initialize story archetypes"""
        return {
            StoryArchetype.QUEST: {
                "description": "Hero's journey to achieve a specific goal",
                "structure": ["call_to_adventure", "challenges", "transformation", "return"],
                "tone": "adventurous",
                "pacing": "progressive"
            },
            StoryArchetype.MYSTERY: {
                "description": "Investigation to uncover hidden truths",
                "structure": ["clue_discovery", "analysis", "revelation", "resolution"],
                "tone": "suspenseful",
                "pacing": "building_tension"
            },
            StoryArchetype.TRANSFORMATION: {
                "description": "Character growth and change through challenges",
                "structure": ["current_state", "catalyst", "struggle", "transformation"],
                "tone": "inspirational",
                "pacing": "gradual_build"
            },
            StoryArchetype.DEFENSE: {
                "description": "Protecting interests against threats",
                "structure": ["threat_identification", "preparation", "defense", "victory"],
                "tone": "protective",
                "pacing": "urgent"
            },
            StoryArchetype.LEGISLATION: {
                "description": "Creating and passing important policies",
                "structure": ["issue_identification", "stakeholder_engagement", "drafting", "passage"],
                "tone": "collaborative",
                "pacing": "methodical"
            },
            StoryArchetype.INVESTIGATION: {
                "description": "Systematic analysis to find solutions",
                "structure": ["hypothesis", "data_collection", "analysis", "conclusion"],
                "tone": "analytical",
                "pacing": "systematic"
            },
            StoryArchetype.OPTIMIZATION: {
                "description": "Improving systems and processes",
                "structure": ["baseline", "analysis", "improvement", "validation"],
                "tone": "efficient",
                "pacing": "iterative"
            },
            StoryArchetype.INNOVATION: {
                "description": "Creating new solutions and approaches",
                "structure": ["inspiration", "experimentation", "creation", "implementation"],
                "tone": "creative",
                "pacing": "exploratory"
            },
            StoryArchetype.COMPLIANCE: {
                "description": "Ensuring adherence to standards and regulations",
                "structure": ["requirement_analysis", "gap_assessment", "implementation", "validation"],
                "tone": "thorough",
                "pacing": "methodical"
            },
            StoryArchetype.STRATEGY: {
                "description": "Planning and executing long-term objectives",
                "structure": ["situation_analysis", "strategy_development", "execution", "evaluation"],
                "tone": "strategic",
                "pacing": "deliberate"
            }
        }
    
    def _initialize_narrative_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize narrative templates for different character types"""
        return {
            "developer_quest": {
                "title_template": "The Code Archaeologist: {character_name}'s Quest for {target}",
                "subtitle_template": "Uncovering the secrets of ancient artifacts in the codebase",
                "context_template": "As {character_name} delves deeper into the {target} system, they discover hidden patterns and forgotten wisdom that could revolutionize the entire codebase.",
                "steps": [
                    "Initial exploration reveals mysterious patterns",
                    "Deep analysis uncovers hidden dependencies",
                    "Discovery of optimization opportunities",
                    "Implementation of improvements"
                ],
                "color_scheme": {"primary": "#2E86AB", "secondary": "#A23B72", "accent": "#F18F01", "highlight": "#C73E1D"}
            },
            "client_support_transformation": {
                "title_template": "The Client Advocate: {character_name}'s Journey to Excellence",
                "subtitle_template": "Transforming client support through business intelligence",
                "context_template": "{character_name} embarks on a mission to revolutionize client support by leveraging advanced business intelligence tools and data-driven insights.",
                "steps": [
                    "Analysis of current support challenges",
                    "Implementation of BI tools",
                    "Training and adoption process",
                    "Measurable improvement in satisfaction"
                ],
                "color_scheme": {"primary": "#4CAF50", "secondary": "#2196F3", "accent": "#FF9800", "highlight": "#9C27B0"}
            },
            "account_manager_optimization": {
                "title_template": "The Sales Automation Pioneer: {character_name}'s Digital Revolution",
                "subtitle_template": "Learning sales automation to increase efficiency",
                "context_template": "{character_name} leads the charge in modernizing sales processes through automation, transforming manual workflows into streamlined, data-driven operations.",
                "steps": [
                    "Assessment of current sales processes",
                    "Identification of automation opportunities",
                    "Implementation of sales automation tools",
                    "Training and optimization of workflows"
                ],
                "color_scheme": {"primary": "#FF6B35", "secondary": "#004E89", "accent": "#1A936F", "highlight": "#C06E52"}
            },
            "lawyer_defense": {
                "title_template": "The Legal Guardian: {character_name}'s Defense Strategy",
                "subtitle_template": "Preparing to defend clients' financial interests",
                "context_template": "{character_name} meticulously analyzes the {target} system to ensure compliance with financial regulations and protect client interests from potential risks.",
                "steps": [
                    "Comprehensive risk assessment",
                    "Regulatory compliance analysis",
                    "Defense strategy development",
                    "Implementation of protective measures"
                ],
                "color_scheme": {"primary": "#2C3E50", "secondary": "#E74C3C", "accent": "#F39C12", "highlight": "#8E44AD"}
            },
            "legislator_strategy": {
                "title_template": "The Policy Architect: {character_name}'s Legislative Mission",
                "subtitle_template": "Preparing a case for important technology vote",
                "context_template": "{character_name} researches and analyzes the {target} system to build a compelling case for legislation that will benefit the public and ensure proper governance.",
                "steps": [
                    "Stakeholder research and engagement",
                    "Technical analysis and impact assessment",
                    "Policy development and drafting",
                    "Building support and consensus"
                ],
                "color_scheme": {"primary": "#34495E", "secondary": "#3498DB", "accent": "#E67E22", "highlight": "#27AE60"}
            }
        }
    
    async def create_character_narrative(self, 
                                       character_role: CharacterRole,
                                       target_element: str,
                                       story_archetype: StoryArchetype = None,
                                       user_goals: List[str] = None,
                                       complexity_level: str = "intermediate") -> CharacterNarrativeResult:
        """Create a character-driven narrative for the specified role and target"""
        
        try:
            # Get character profile
            character = self.characters.get(character_role)
            if not character:
                return CharacterNarrativeResult(
                    success=False,
                    story_title="",
                    character_name="",
                    story_html="",
                    narrative_text="",
                    character_arc="",
                    goals_achieved=[],
                    challenges_overcome=[],
                    metrics_tracked={},
                    story_metadata={},
                    error_message=f"Character role {character_role} not found"
                )
            
            # Determine story archetype if not specified
            if not story_archetype:
                story_archetype = self._select_archetype_for_character(character, target_element)
            
            # Create story context
            context = StoryContext(
                character=character,
                target_element=target_element,
                codebase_context=self._analyze_codebase_context(target_element),
                user_goals=user_goals or character.goals,
                complexity_level=complexity_level,
                time_constraint="moderate",
                risk_factors=character.challenges,
                success_criteria=character.success_metrics
            )
            
            # Generate narrative using PyNarrative
            story_result = await self._generate_character_story(context, story_archetype)
            
            if not story_result.success:
                return CharacterNarrativeResult(
                    success=False,
                    story_title="",
                    character_name=character.name,
                    story_html="",
                    narrative_text="",
                    character_arc="",
                    goals_achieved=[],
                    challenges_overcome=[],
                    metrics_tracked={},
                    story_metadata={},
                    error_message=story_result.error_message
                )
            
            # Generate story title
            story_title = self._generate_story_title(character, target_element, story_archetype)
            
            # Extract character arc and achievements
            character_arc = self._extract_character_arc(context, story_archetype)
            goals_achieved = self._identify_goals_achieved(context, story_result)
            challenges_overcome = self._identify_challenges_overcome(context, story_result)
            metrics_tracked = self._calculate_metrics(context, story_result)
            
            return CharacterNarrativeResult(
                success=True,
                story_title=story_title,
                character_name=character.name,
                story_html=story_result.story_html or "",
                narrative_text=story_result.narrative_text or "",
                character_arc=character_arc,
                goals_achieved=goals_achieved,
                challenges_overcome=challenges_overcome,
                metrics_tracked=metrics_tracked,
                story_metadata={
                    "character_role": character_role.value,
                    "story_archetype": story_archetype.value,
                    "complexity_level": complexity_level,
                    "color_scheme": character.color_scheme,
                    "personality_traits": character.personality_traits,
                    "expertise_areas": character.expertise_areas
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creating character narrative: {e}")
            return CharacterNarrativeResult(
                success=False,
                story_title="",
                character_name="",
                story_html="",
                narrative_text="",
                character_arc="",
                goals_achieved=[],
                challenges_overcome=[],
                metrics_tracked={},
                story_metadata={},
                error_message=f"Failed to create character narrative: {str(e)}"
            )
    
    def _select_archetype_for_character(self, character: CharacterProfile, target_element: str) -> StoryArchetype:
        """Select appropriate story archetype for character and target"""
        # Map character roles to preferred archetypes
        archetype_mapping = {
            CharacterRole.DEVELOPER: [StoryArchetype.QUEST, StoryArchetype.MYSTERY, StoryArchetype.INVESTIGATION],
            CharacterRole.CLIENT_SUPPORT: [StoryArchetype.TRANSFORMATION, StoryArchetype.OPTIMIZATION, StoryArchetype.INNOVATION],
            CharacterRole.ACCOUNT_MANAGER: [StoryArchetype.TRANSFORMATION, StoryArchetype.OPTIMIZATION, StoryArchetype.STRATEGY],
            CharacterRole.LAWYER: [StoryArchetype.DEFENSE, StoryArchetype.COMPLIANCE, StoryArchetype.INVESTIGATION],
            CharacterRole.GOVERNMENT_LEGISLATOR: [StoryArchetype.LEGISLATION, StoryArchetype.STRATEGY, StoryArchetype.TRANSFORMATION],
            CharacterRole.DATA_SCIENTIST: [StoryArchetype.INVESTIGATION, StoryArchetype.INNOVATION, StoryArchetype.OPTIMIZATION],
            CharacterRole.SECURITY_ANALYST: [StoryArchetype.INVESTIGATION, StoryArchetype.DEFENSE, StoryArchetype.COMPLIANCE],
            CharacterRole.PROJECT_MANAGER: [StoryArchetype.STRATEGY, StoryArchetype.TRANSFORMATION, StoryArchetype.OPTIMIZATION],
            CharacterRole.UX_DESIGNER: [StoryArchetype.INNOVATION, StoryArchetype.TRANSFORMATION, StoryArchetype.OPTIMIZATION],
            CharacterRole.SYSTEM_ADMIN: [StoryArchetype.OPTIMIZATION, StoryArchetype.TRANSFORMATION, StoryArchetype.STRATEGY]
        }
        
        preferred_archetypes = archetype_mapping.get(character.role, [StoryArchetype.QUEST])
        return random.choice(preferred_archetypes)
    
    def _analyze_codebase_context(self, target_element: str) -> Dict[str, Any]:
        """Analyze codebase context for the target element"""
        # This would integrate with the RAG system to get real codebase data
        # For now, return simulated context
        return {
            "element_type": "function" if "()" in target_element else "class" if target_element[0].isupper() else "module",
            "complexity": "high" if len(target_element) > 20 else "medium",
            "dependencies": random.randint(3, 8),
            "lines_of_code": random.randint(50, 200),
            "last_modified": "recent",
            "documentation": "partial"
        }
    
    async def _generate_character_story(self, context: StoryContext, archetype: StoryArchetype) -> NarrativeVisualizationResult:
        """Generate character story using PyNarrative"""
        
        # Map archetype to visualization type
        archetype_to_visualization = {
            StoryArchetype.QUEST: "function_call",
            StoryArchetype.MYSTERY: "dependency",
            StoryArchetype.TRANSFORMATION: "overview",
            StoryArchetype.DEFENSE: "cross_reference",
            StoryArchetype.LEGISLATION: "overview",
            StoryArchetype.INVESTIGATION: "dependency",
            StoryArchetype.OPTIMIZATION: "function_call",
            StoryArchetype.INNOVATION: "overview",
            StoryArchetype.COMPLIANCE: "cross_reference",
            StoryArchetype.STRATEGY: "overview"
        }
        
        visualization_type = archetype_to_visualization.get(archetype, "overview")
        
        # Create visualization request
        request = NarrativeVisualizationRequest(
            visualization_type=visualization_type,
            target_element=context.target_element,
            max_depth=3,
            max_nodes=50,
            narrative_style='guided',
            include_annotations=True,
            include_next_steps=True,
            custom_context=json.dumps({
                "character": {
                    "name": context.character.name,
                    "role": context.character.role.value,
                    "background": context.character.background,
                    "personality_traits": context.character.personality_traits,
                    "goals": context.character.goals,
                    "challenges": context.character.challenges,
                    "success_metrics": context.character.success_metrics,
                    "narrative_style": context.character.narrative_style,
                    "color_scheme": context.character.color_scheme,
                    "expertise_areas": context.character.expertise_areas,
                    "motivation": context.character.motivation,
                    "conflict_type": context.character.conflict_type,
                    "resolution_style": context.character.resolution_style
                },
                "archetype": archetype.value,
                "story_context": {
                    "user_goals": context.user_goals,
                    "complexity_level": context.complexity_level,
                    "time_constraint": context.time_constraint,
                    "risk_factors": context.risk_factors,
                    "success_criteria": context.success_criteria
                }
            }),
            user_id=f"character_{context.character.role.value}"
        )
        
        # Generate story using PyNarrative agent
        return await self.agent.create_narrative_visualization(request)
    
    def _extract_character_arc(self, context: StoryContext, archetype: StoryArchetype) -> str:
        """Extract character arc from the story context"""
        arc_templates = {
            StoryArchetype.QUEST: f"{context.character.name} embarks on a quest to master {context.target_element}, facing challenges that test their {', '.join(context.character.personality_traits[:2])} nature.",
            StoryArchetype.TRANSFORMATION: f"{context.character.name} transforms their approach to {context.target_element}, evolving from current methods to innovative solutions that achieve their goals.",
            StoryArchetype.DEFENSE: f"{context.character.name} builds a comprehensive defense strategy for {context.target_element}, ensuring protection against potential risks and compliance with regulations.",
            StoryArchetype.LEGISLATION: f"{context.character.name} researches and analyzes {context.target_element} to build a compelling case for legislation that serves the public interest.",
            StoryArchetype.INVESTIGATION: f"{context.character.name} conducts a thorough investigation of {context.target_element}, uncovering insights that drive better decision-making."
        }
        
        return arc_templates.get(archetype, f"{context.character.name} explores {context.target_element} to achieve their professional goals.")
    
    def _identify_goals_achieved(self, context: StoryContext, story_result: NarrativeVisualizationResult) -> List[str]:
        """Identify goals achieved through the story"""
        achieved_goals = []
        for goal in context.user_goals:
            if any(keyword in goal.lower() for keyword in ["understand", "analyze", "explore"]):
                achieved_goals.append(goal)
            elif any(keyword in goal.lower() for keyword in ["optimize", "improve", "enhance"]):
                if story_result.success:
                    achieved_goals.append(goal)
        return achieved_goals
    
    def _identify_challenges_overcome(self, context: StoryContext, story_result: NarrativeVisualizationResult) -> List[str]:
        """Identify challenges overcome in the story"""
        return context.risk_factors[:2] if story_result.success else []
    
    def _calculate_metrics(self, context: StoryContext, story_result: NarrativeVisualizationResult) -> Dict[str, Any]:
        """Calculate metrics for the character story"""
        return {
            "story_complexity": context.complexity_level,
            "character_engagement": "high" if story_result.success else "low",
            "goal_achievement_rate": len(self._identify_goals_achieved(context, story_result)) / len(context.user_goals),
            "challenge_overcome_rate": len(self._identify_challenges_overcome(context, story_result)) / len(context.risk_factors),
            "narrative_quality": "excellent" if story_result.success else "poor"
        }
    
    def get_available_characters(self) -> List[Dict[str, Any]]:
        """Get list of available characters with their profiles"""
        return [
            {
                "role": role.value,
                "name": profile.name,
                "background": profile.background,
                "personality_traits": profile.personality_traits,
                "goals": profile.goals,
                "expertise_areas": profile.expertise_areas,
                "motivation": profile.motivation,
                "color_scheme": profile.color_scheme
            }
            for role, profile in self.characters.items()
        ]
    
    def get_character_profile(self, role: CharacterRole) -> Optional[CharacterProfile]:
        """Get detailed character profile for a specific role"""
        return self.characters.get(role)
    
    def get_story_archetypes(self) -> List[Dict[str, Any]]:
        """Get list of available story archetypes"""
        return [
            {
                "archetype": archetype.value,
                "description": details["description"],
                "structure": details["structure"],
                "tone": details["tone"]
            }
            for archetype, details in self.story_archetypes.items()
        ] 

    def _generate_story_title(self, character: CharacterProfile, target_element: str, archetype: StoryArchetype) -> str:
        title_templates = {
            StoryArchetype.QUEST: f"The {character.role.value.title()}'s Quest: {character.name} and the {target_element}",
            StoryArchetype.MYSTERY: f"The {target_element} Mystery: {character.name}'s Investigation",
            StoryArchetype.TRANSFORMATION: f"Transforming {target_element}: {character.name}'s Journey",
            StoryArchetype.DEFENSE: f"Defending {target_element}: {character.name}'s Strategy",
            StoryArchetype.LEGISLATION: f"Legislating {target_element}: {character.name}'s Mission",
            StoryArchetype.INVESTIGATION: f"Investigating {target_element}: {character.name}'s Analysis",
            StoryArchetype.OPTIMIZATION: f"Optimizing {target_element}: {character.name}'s Approach",
            StoryArchetype.INNOVATION: f"Innovating {target_element}: {character.name}'s Vision",
            StoryArchetype.COMPLIANCE: f"Ensuring {target_element} Compliance: {character.name}'s Review",
            StoryArchetype.STRATEGY: f"Strategic {target_element}: {character.name}'s Plan"
        }
        return title_templates.get(archetype, f"{character.name} and the {target_element}") 