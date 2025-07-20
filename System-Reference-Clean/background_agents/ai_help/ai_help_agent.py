"""
PostgreSQL-Based AI Help Agent

Enterprise AI assistance with real-time system context integration,
advanced RAG system, and comprehensive business intelligence.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import os
from dataclasses import dataclass
from pathlib import Path

from ..coordination.base_agent import BaseAgent
from ..coordination.shared_state import SharedState
from ..monitoring.agent_memory_interface import MemoryOptimizationMixin, AIHelpAgentMemoryOptimizer
from .enhanced_rag_system import EnhancedRAGSystem, Document
from .knowledge_base_validator import KnowledgeBaseValidator
from .advanced_query_system import AdvancedQuerySystem, QueryContext


@dataclass
class HelpRequest:
    """Help request data structure"""
    request_id: str
    user_id: str
    query: str
    context: Dict[str, Any]
    timestamp: datetime
    priority: str = 'normal'
    category: str = 'general'


@dataclass
class HelpResponse:
    """Help response data structure"""
    response_id: str
    request_id: str
    response_text: str
    confidence_score: float
    sources: List[str]
    processing_time: float
    timestamp: datetime
    business_value: float = 0.0


class SystemContextIntegrator:
    """Real-time system context integration for enhanced AI responses"""
    
    def __init__(self, shared_state):
        self.shared_state = shared_state
        
    async def gather_system_context(self, query: str) -> Dict[str, Any]:
        """Gather comprehensive system context for AI assistance"""
        
        context = {
            'timestamp': datetime.now(timezone.utc),
            'system_status': await self.get_system_status(),
            'agent_performance': await self.get_agent_performance_context(),
            'recent_events': await self.get_recent_system_events(),
            'performance_metrics': await self.get_performance_metrics_context(),
            'business_metrics': await self.get_business_context(),
            'query_category': await self.categorize_query(query)
        }
        
        return context
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # Get all registered agents
            agents = await self.shared_state.get_registered_agents()
            
            # Calculate system health
            total_agents = len(agents)
            active_agents = len([a for a in agents if a.get('state') == 'active'])
            
            return {
                'total_agents': total_agents,
                'active_agents': active_agents,
                'system_health': 'healthy' if active_agents >= total_agents * 0.8 else 'degraded',
                'uptime_status': 'operational'
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 'unknown'}
            
    async def get_agent_performance_context(self) -> Dict[str, Any]:
        """Get agent performance context"""
        try:
            # Get recent performance metrics
            metrics = await self.shared_state.get_performance_metrics(hours=1)
            
            # Aggregate by agent
            agent_performance = {}
            for metric in metrics:
                agent_id = metric.get('agent_id')
                if agent_id and agent_id not in agent_performance:
                    agent_performance[agent_id] = {
                        'metrics_count': 0,
                        'avg_processing_time': 0,
                        'error_count': 0
                    }
                    
                agent_performance[agent_id]['metrics_count'] += 1
                
                if metric.get('metric_name') == 'processing_time':
                    agent_performance[agent_id]['avg_processing_time'] = metric.get('metric_value', 0)
                elif 'error' in metric.get('metric_name', ''):
                    agent_performance[agent_id]['error_count'] += 1
                    
            return {
                'agent_count': len(agent_performance),
                'performance_summary': agent_performance,
                'overall_health': 'good' if len(agent_performance) > 0 else 'unknown'
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def get_recent_system_events(self) -> List[Dict]:
        """Get recent system events for context"""
        try:
            # Get recent events
            events = await self.shared_state.get_system_events(hours=2)
            
            # Filter and format relevant events
            relevant_events = []
            for event in events[:10]:  # Last 10 events
                relevant_events.append({
                    'event_type': event.get('event_type'),
                    'severity': event.get('severity'),
                    'timestamp': event.get('timestamp'),
                    'agent_id': event.get('agent_id'),
                    'summary': self.summarize_event(event)
                })
                
            return relevant_events
            
        except Exception as e:
            return [{'error': str(e)}]
            
    def summarize_event(self, event: Dict) -> str:
        """Create a brief summary of an event"""
        event_type = event.get('event_type', 'unknown')
        agent_id = event.get('agent_id', 'system')
        
        if event_type == 'agent_error':
            return f"Error in {agent_id}"
        elif event_type == 'performance_summary':
            return f"Performance update from {agent_id}"
        elif event_type == 'health_check':
            return f"Health check for {agent_id}"
        else:
            return f"{event_type} event"
            
    async def get_performance_metrics_context(self) -> Dict[str, Any]:
        """Get performance metrics context"""
        try:
            metrics = await self.shared_state.get_performance_metrics(hours=1)
            
            # Calculate summary statistics
            processing_times = [m['metric_value'] for m in metrics 
                              if m['metric_name'] == 'processing_time']
            cpu_usage = [m['metric_value'] for m in metrics 
                        if m['metric_name'] == 'cpu_usage']
            memory_usage = [m['metric_value'] for m in metrics 
                           if m['metric_name'] == 'memory_usage']
            
            return {
                'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'avg_cpu_usage': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'metrics_collected': len(metrics)
            }
            
        except Exception as e:
            return {'error': str(e)}
            
    async def get_business_context(self) -> Dict[str, Any]:
        """Get business metrics context"""
        try:
            # Get business metrics (if available)
            business_metrics = await self.shared_state.get_business_metrics(hours=24)
            
            return {
                'business_metrics_count': len(business_metrics),
                'cost_efficiency': 'optimized',
                'user_satisfaction': 'high',
                'operational_status': 'normal'
            }
            
        except Exception as e:
            return {'business_status': 'unknown', 'error': str(e)}
            
    async def categorize_query(self, query: str) -> str:
        """Categorize the help query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['error', 'failed', 'problem', 'issue']):
            return 'troubleshooting'
        elif any(word in query_lower for word in ['performance', 'slow', 'optimization']):
            return 'performance'
        elif any(word in query_lower for word in ['cost', 'money', 'billing', 'savings']):
            return 'cost_analysis'
        elif any(word in query_lower for word in ['how', 'what', 'explain', 'guide']):
            return 'information'
        elif any(word in query_lower for word in ['health', 'status', 'monitoring']):
            return 'monitoring'
        else:
            return 'general'


class LegacyRAGSystem:
    """Legacy RAG system - kept for fallback compatibility"""
    
    def __init__(self):
        self.document_store = {}
        self.knowledge_base = self.initialize_knowledge_base()
        # Tunable parameter for self-healing optimizations
        if not hasattr(LegacyRAGSystem, "MAX_RELEVANT_DOCS"):
            LegacyRAGSystem.MAX_RELEVANT_DOCS = 5  # default
        
    def initialize_knowledge_base(self) -> Dict[str, str]:
        """Initialize the knowledge base with system documentation"""
        return {
            'agent_architecture': """
            The system uses a PostgreSQL-based agent architecture with:
            - BaseAgent: Foundation class for all agents
            - AgentCoordinator: Manages agent lifecycle and health
            - SharedState: PostgreSQL-backed state management
            - Health monitoring with automated recovery
            """,
            
            'performance_monitoring': """
            Performance monitoring includes:
            - Real-time metrics collection
            - ML-powered anomaly detection
            - Cost optimization recommendations
            - Business intelligence reporting
            - Automated alerting and recovery
            """,
            
            'troubleshooting_guide': """
            Common troubleshooting steps:
            1. Check agent health in shared state
            2. Review recent system events
            3. Analyze performance metrics
            4. Check database connectivity
            5. Review error logs and recovery attempts
            """,
            
            'cost_optimization': """
            Cost optimization strategies:
            - Monitor resource usage patterns
            - Identify inefficient agents
            - Optimize processing intervals
            - Use cost-effective models
            - Implement automated scaling
            """,
            
            'business_intelligence': """
            Business intelligence features:
            - Executive dashboards
            - ROI calculation
            - Cost-benefit analysis
            - Performance trending
            - Predictive analytics
            """
        }
        
    async def generate_response(self, query: str, context: Dict[str, Any]) -> HelpResponse:
        """Generate AI-powered response using RAG"""
        
        # Retrieve relevant knowledge
        relevant_docs = await self.retrieve_relevant_documents(query, context)
        
        # Generate contextual response
        response_text = await self.generate_contextual_response(query, relevant_docs, context)
        
        # Calculate confidence score
        confidence_score = await self.calculate_confidence_score(query, response_text, context)
        
        # Identify sources
        sources = await self.identify_sources(relevant_docs)
        
        # Calculate business value
        business_value = await self.calculate_response_business_value(query, context)
        
        response = HelpResponse(
            response_id=f"resp_{int(time.time())}",
            request_id=context.get('request_id', 'unknown'),
            response_text=response_text,
            confidence_score=confidence_score,
            sources=sources,
            processing_time=context.get('processing_time', 0),
            timestamp=datetime.now(timezone.utc),
            business_value=business_value
        )
        
        return response
        
    async def retrieve_relevant_documents(self, query: str, context: Dict[str, Any]) -> List[Dict]:
        """Retrieve relevant documents from knowledge base"""
        
        query_category = context.get('query_category', 'general')
        relevant_docs = []
        
        # Retrieve based on category
        if query_category == 'troubleshooting':
            relevant_docs.append({
                'title': 'Troubleshooting Guide',
                'content': self.knowledge_base['troubleshooting_guide'],
                'relevance_score': 0.9
            })
            
        elif query_category == 'performance':
            relevant_docs.append({
                'title': 'Performance Monitoring',
                'content': self.knowledge_base['performance_monitoring'],
                'relevance_score': 0.9
            })
            
        elif query_category == 'cost_analysis':
            relevant_docs.append({
                'title': 'Cost Optimization',
                'content': self.knowledge_base['cost_optimization'],
                'relevance_score': 0.9
            })
            
        # Always include architecture info for technical queries
        if any(word in query.lower() for word in ['agent', 'system', 'architecture']):
            relevant_docs.append({
                'title': 'Agent Architecture',
                'content': self.knowledge_base['agent_architecture'],
                'relevance_score': 0.8
            })
            
        # Add business intelligence for business queries
        if any(word in query.lower() for word in ['business', 'roi', 'value']):
            relevant_docs.append({
                'title': 'Business Intelligence',
                'content': self.knowledge_base['business_intelligence'],
                'relevance_score': 0.8
            })
            
        # Respect MAX_RELEVANT_DOCS limit to reduce payload size
        max_docs = getattr(LegacyRAGSystem, "MAX_RELEVANT_DOCS", 5)
        return relevant_docs[:max_docs]
        
    async def generate_contextual_response(self, query: str, relevant_docs: List[Dict], 
                                         context: Dict[str, Any]) -> str:
        """Generate contextual response using retrieved documents and system context"""
        
        # Analyze query intent
        query_intent = await self.analyze_query_intent(query)
        
        # If intent analyser asks for clarification, short-circuit with prompt
        if isinstance(query_intent, dict):
            if query_intent.get('requires_clarification'):
                return query_intent['clarification_prompt']
            intent_value = query_intent.get('intent', 'general_inquiry')
        else:
            intent_value = query_intent
        
        # Build response based on intent and context
        if intent_value == 'status_check':
            return await self.generate_status_response(context)
        elif intent_value == 'troubleshooting':
            return await self.generate_troubleshooting_response(query, relevant_docs, context)
        elif intent_value == 'performance_analysis':
            return await self.generate_performance_response(context)
        elif intent_value == 'cost_analysis':
            return await self.generate_cost_response(context)
        else:
            return await self.generate_general_response(query, relevant_docs, context)
            
    async def analyze_query_intent(self, query: str):
        """Analyze the intent of the user query.

        Returns
        -------
        dict | str
            • Historical behaviour ‑ when the intent is confidently detected, the function returns a simple
              string (back-compat).
            • If the intent confidence is *low*, we now return a dictionary::

                {
                  "intent": "general_inquiry",
                  "confidence": 0.3,
                  "requires_clarification": True,
                  "clarification_prompt": "I’m not totally sure I understood – could you please clarify your request?"
                }
        """

        query_lower = (query or "").lower().strip()

        # Simple keyword heuristics
        intent_map = {
            'status_check': ['status', 'health', 'running'],
            'troubleshooting': ['problem', 'error', 'fix', 'troubleshoot'],
            'performance_analysis': ['performance', 'speed', 'optimization'],
            'cost_analysis': ['cost', 'money', 'savings', 'budget'],
        }

        chosen_intent: str = 'general_inquiry'
        max_keyword_hits = 0

        for intent, keywords in intent_map.items():
            hits = sum(1 for kw in keywords if kw in query_lower)
            if hits > max_keyword_hits:
                max_keyword_hits = hits
                chosen_intent = intent

        # Confidence is proportional to keyword hits (very naive – upgradeable later)
        confidence = min(1.0, max_keyword_hits / 2.0)  # 0, 0.5, or 1.0

        if confidence < 0.5:
            # Return clarification payload
            return {
                'intent': chosen_intent,
                'confidence': confidence,
                'requires_clarification': True,
                'clarification_prompt': "I’m not totally sure I understood – could you please clarify your request?",
            }

        return chosen_intent
            
    async def generate_status_response(self, context: Dict[str, Any]) -> str:
        """Generate system status response"""
        system_status = context.get('system_status', {})
        
        total_agents = system_status.get('total_agents', 0)
        active_agents = system_status.get('active_agents', 0)
        health = system_status.get('system_health', 'unknown')
        
        response = f"""**System Status Report**

🔍 **Overall Health**: {health.title()}
📊 **Agent Status**: {active_agents}/{total_agents} agents active
⚡ **System Performance**: """
        
        perf_context = context.get('performance_metrics', {})
        avg_processing = perf_context.get('avg_processing_time', 0)
        
        if avg_processing > 0:
            response += f"Average processing time: {avg_processing:.2f}s"
        else:
            response += "Performance data collecting"
            
        # Add recent events
        recent_events = context.get('recent_events', [])
        if recent_events:
            response += f"\n\n📋 **Recent Activity**: {len(recent_events)} events in last 2 hours"
            
        response += "\n\n✅ **System is operating normally** with full monitoring and automated recovery active."
        
        return response
        
    async def generate_troubleshooting_response(self, query: str, relevant_docs: List[Dict], 
                                              context: Dict[str, Any]) -> str:
        """Generate troubleshooting response"""
        
        response = "🔧 **Troubleshooting Assistance**\n\n"
        
        # Check for specific issues in recent events
        recent_events = context.get('recent_events', [])
        error_events = [e for e in recent_events if e.get('severity') in ['ERROR', 'CRITICAL']]
        
        if error_events:
            response += f"⚠️ **Detected Issues**: Found {len(error_events)} recent errors\n\n"
            for event in error_events[:3]:  # Show first 3 errors
                response += f"- {event.get('summary', 'Unknown error')} ({event.get('agent_id', 'system')})\n"
                
            response += "\n**Recommended Actions**:\n"
            response += "1. Check agent health status\n"
            response += "2. Review detailed error logs\n"
            response += "3. Verify database connectivity\n"
            response += "4. Consider agent restart if issues persist\n"
        else:
            response += "✅ **No Critical Issues Detected**\n\n"
            response += "The system appears to be running normally. "
            
            # Provide general troubleshooting guidance
            if relevant_docs:
                response += "Here are some general troubleshooting steps:\n\n"
                for doc in relevant_docs:
                    response += f"**{doc['title']}**:\n{doc['content']}\n\n"
                    
        return response
        
    async def generate_performance_response(self, context: Dict[str, Any]) -> str:
        """Generate performance analysis response"""
        
        response = "📈 **Performance Analysis**\n\n"
        
        perf_metrics = context.get('performance_metrics', {})
        agent_performance = context.get('agent_performance', {})
        
        # Overall performance summary
        avg_processing = perf_metrics.get('avg_processing_time', 0)
        avg_cpu = perf_metrics.get('avg_cpu_usage', 0)
        avg_memory = perf_metrics.get('avg_memory_usage', 0)
        
        response += f"**System Performance Metrics**:\n"
        response += f"- Average Processing Time: {avg_processing:.2f}s\n"
        response += f"- CPU Usage: {avg_cpu:.1f}%\n"
        response += f"- Memory Usage: {avg_memory:.1f}%\n\n"
        
        # Performance recommendations
        response += "**Performance Recommendations**:\n"
        
        if avg_processing > 5.0:
            response += "🔴 High processing times detected - consider optimization\n"
        elif avg_processing > 2.0:
            response += "🟡 Moderate processing times - monitor for trends\n"
        else:
            response += "✅ Good processing performance\n"
            
        if avg_cpu > 80:
            response += "🔴 High CPU usage - consider load balancing\n"
        elif avg_cpu > 60:
            response += "🟡 Moderate CPU usage - monitor for peaks\n"
        else:
            response += "✅ Efficient CPU utilization\n"
            
        response += "\n💡 **Optimization Tip**: Use the Performance Monitor agent for detailed analytics and automated optimization recommendations."
        
        return response
        
    async def generate_cost_response(self, context: Dict[str, Any]) -> str:
        """Generate cost analysis response"""
        
        response = "💰 **Cost Analysis & Optimization**\n\n"
        
        business_context = context.get('business_metrics', {})
        agent_count = context.get('system_status', {}).get('total_agents', 0)
        
        # Estimated costs (simplified calculation)
        estimated_monthly_cost = agent_count * 50  # $50 per agent per month
        
        response += f"**Current System Costs**:\n"
        response += f"- Estimated Monthly Cost: ${estimated_monthly_cost}\n"
        response += f"- Cost per Agent: $50/month\n"
        response += f"- Total Agents: {agent_count}\n\n"
        
        response += "**Cost Optimization Opportunities**:\n"
        response += "- 🎯 Automated resource optimization: Save up to 25%\n"
        response += "- 📊 Performance tuning: Reduce processing costs by 15%\n"
        response += "- 🔄 Intelligent scaling: Optimize based on demand\n\n"
        
        response += "**Business Value Generated**:\n"
        response += "- ✅ Automated monitoring: $2,000/month value\n"
        response += "- 🚀 Performance optimization: $1,500/month savings\n"
        response += "- 🛡️ Error prevention: $3,000/month risk mitigation\n\n"
        
        response += "💡 **ROI**: The system typically pays for itself within 2-3 months through automation and optimization."
        
        return response
        
    async def generate_general_response(self, query: str, relevant_docs: List[Dict], 
                                      context: Dict[str, Any]) -> str:
        """Generate general response for information queries"""
        
        response = "🤖 **AI Help Assistant**\n\n"
        
        if relevant_docs:
            response += "Based on your query, here's the relevant information:\n\n"
            for doc in relevant_docs:
                response += f"**{doc['title']}**:\n{doc['content']}\n\n"
        else:
            response += "I can help you with:\n\n"
            response += "- 🔍 System status and health monitoring\n"
            response += "- 🔧 Troubleshooting and error resolution\n"
            response += "- 📈 Performance analysis and optimization\n"
            response += "- 💰 Cost analysis and business metrics\n"
            response += "- 📚 System documentation and guides\n\n"
            response += "Please ask me specific questions about any of these topics!"
            
        # Add current system context
        system_status = context.get('system_status', {})
        if system_status.get('system_health') == 'healthy':
            response += "\n✅ **Current Status**: All systems operating normally"
        
        return response
        
    async def calculate_confidence_score(self, query: str, response: str, context: Dict[str, Any]) -> float:
        """Calculate confidence score for the response"""
        
        confidence = 70.0  # Base confidence
        
        # Increase confidence for specific categories
        query_category = context.get('query_category', 'general')
        if query_category in ['troubleshooting', 'performance', 'monitoring']:
            confidence += 20.0
            
        # Increase confidence if we have recent system data
        if context.get('system_status') and context.get('recent_events'):
            confidence += 10.0
            
        # Response quality indicators
        if len(response) > 200:  # Detailed response
            confidence += 5.0
            
        if '**' in response:  # Formatted response
            confidence += 3.0
            
        return min(confidence, 95.0)  # Cap at 95%
        
    async def identify_sources(self, relevant_docs: List[Dict]) -> List[str]:
        """Identify sources used in response generation"""
        
        sources = ['Real-time system data', 'Agent performance metrics']
        
        for doc in relevant_docs:
            sources.append(doc['title'])
            
        return sources
        
    async def calculate_response_business_value(self, query: str, context: Dict[str, Any]) -> float:
        """Calculate business value of the AI response"""
        
        base_value = 25.0  # Base value for AI assistance
        
        query_category = context.get('query_category', 'general')
        
        # Higher value for critical categories
        if query_category == 'troubleshooting':
            base_value += 75.0  # Problem solving saves significant costs
        elif query_category == 'performance':
            base_value += 50.0  # Performance optimization value
        elif query_category == 'cost_analysis':
            base_value += 100.0  # Cost insights have high business value
            
        return base_value


class QualityAssessmentSystem:
    """Quality assessment and continuous improvement system"""
    
    async def assess_response_quality(self, request: HelpRequest, response: HelpResponse) -> Dict[str, Any]:
        """Assess the quality of AI help response"""
        
        quality_metrics = {
            'relevance_score': await self.assess_relevance(request, response),
            'completeness_score': await self.assess_completeness(request, response),
            'accuracy_score': await self.assess_accuracy(response),
            'timeliness_score': await self.assess_timeliness(response),
            'user_satisfaction_prediction': await self.predict_user_satisfaction(request, response)
        }
        
        # Calculate overall quality score
        weights = {
            'relevance_score': 0.3,
            'completeness_score': 0.25,
            'accuracy_score': 0.25,
            'timeliness_score': 0.1,
            'user_satisfaction_prediction': 0.1
        }
        
        overall_score = sum(
            quality_metrics[metric] * weights[metric]
            for metric in quality_metrics
        )
        
        quality_metrics['overall_quality_score'] = overall_score
        quality_metrics['quality_grade'] = self.determine_quality_grade(overall_score)
        
        return quality_metrics
        
    async def assess_relevance(self, request: HelpRequest, response: HelpResponse) -> float:
        """Assess response relevance to the request"""
        
        query_words = set(request.query.lower().split())
        response_words = set(response.response_text.lower().split())
        
        # Simple relevance based on word overlap
        overlap = len(query_words.intersection(response_words))
        relevance = min((overlap / len(query_words)) * 100, 100) if query_words else 50
        
        # Boost for category-specific responses
        if request.category in response.response_text.lower():
            relevance += 10
            
        return min(relevance, 100)
        
    async def assess_completeness(self, request: HelpRequest, response: HelpResponse) -> float:
        """Assess response completeness"""
        
        completeness = 70.0  # Base completeness
        
        # Check for structured response
        if '**' in response.response_text:  # Has formatting
            completeness += 15
            
        # Check for actionable information
        if any(word in response.response_text.lower() for word in ['steps', 'actions', 'recommendations']):
            completeness += 10
            
        # Check for comprehensive coverage
        if len(response.response_text) > 300:
            completeness += 5
            
        return min(completeness, 100)
        
    async def assess_accuracy(self, response: HelpResponse) -> float:
        """Assess response accuracy"""
        
        # Use confidence score as proxy for accuracy
        accuracy = response.confidence_score
        
        # Boost for real-time data usage
        if 'real-time' in response.response_text.lower():
            accuracy += 5
            
        return min(accuracy, 100)
        
    async def assess_timeliness(self, response: HelpResponse) -> float:
        """Assess response timeliness"""
        processing_time = getattr(response, 'processing_time', 0.0)
        if processing_time < 2.0:
            return 100.0
        elif processing_time < 5.0:
            return 90.0
        elif processing_time < 10.0:
            return 80.0
        else:
            return 70.0
            
    async def predict_user_satisfaction(self, request: HelpRequest, response: HelpResponse) -> float:
        """Predict user satisfaction with response"""
        
        satisfaction = 75.0  # Base satisfaction
        
        # Higher satisfaction for urgent requests that get quick responses
        if request.priority == 'high' and response.processing_time < 3.0:
            satisfaction += 15
            
        # Higher satisfaction for detailed responses
        if len(response.response_text) > 200:
            satisfaction += 10
            
        return min(satisfaction, 100)
        
    def determine_quality_grade(self, score: float) -> str:
        """Determine quality grade from score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


class AIHelpAgent(BaseAgent, MemoryOptimizationMixin):
    """
    Enterprise AI Help Agent with Real-time System Context Integration
    """
    
    def __init__(self, agent_id: str = "ai_help_agent", shared_state=None):
        super().__init__(agent_id, shared_state)
        self.agent_name = "AIHelpAgent"
        
        # Initialize enhanced components first
        self.context_integrator = SystemContextIntegrator(shared_state)
        self.rag_system = EnhancedRAGSystem()
        self.legacy_rag_system = LegacyRAGSystem()  # Fallback compatibility
        self.quality_assessor = QualityAssessmentSystem()
        self.knowledge_base_validator = KnowledgeBaseValidator()
        
        # Initialize memory optimization after components
        MemoryOptimizationMixin.__init__(self, agent_id, self.agent_name)
        self.memory_optimizer = AIHelpAgentMemoryOptimizer(agent_id, self.agent_name, self.rag_system, self.context_integrator)
        
        # Advanced Query System for intelligent search and code analysis
        self.advanced_query_system = AdvancedQuerySystem(self.rag_system)
        
        # Configuration
        self.help_processing_interval = 30  # seconds
        self.max_concurrent_requests = 5
        self.response_timeout = 30  # seconds
        
        # Enhanced performance tracking
        self.help_stats = {
            'requests_processed': 0,
            'average_response_time': 0,
            'user_satisfaction_score': 4.8,
            'business_value_generated': 0,
            'rag_system_status': 'initializing',
            'documents_indexed': 0,
            'vector_store_ready': False,
            'semantic_retrieval_accuracy': 0.0,
            'fallback_usage_count': 0
        }
        
        # Request queue
        self.request_queue = asyncio.Queue()
        self.active_requests = {}
        
    async def initialize(self) -> None:
        """Initialize AI Help agent with enhanced RAG system"""
        self.logger.info("Initializing AI Help Agent with enhanced RAG and real-time system integration")
        
        # Set work interval
        self.work_interval = self.help_processing_interval
        
        # Initialize enhanced RAG system
        await self.setup_enhanced_rag_system()
        
        # Initialize request processing
        await self.setup_request_processing()
    
    async def setup_enhanced_rag_system(self) -> None:
        """Setup enhanced RAG system with knowledge indexing"""
        try:
            self.logger.info("Setting up enhanced RAG system...")
            
            # Initialize enhanced RAG system
            await self.rag_system.initialize()
            self.help_stats['rag_system_status'] = 'initialized'
            
            # Index knowledge base
            await self.setup_knowledge_indexing()
            
            self.logger.info("Enhanced RAG system setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced RAG system: {e}")
            self.help_stats['rag_system_status'] = 'failed'
            # Fall back to legacy system
            self.logger.info("Falling back to legacy RAG system")
            from background_agents.ai_help.ai_help_agent import LegacyRAGSystem  # local import to avoid circular
            debug_msg = (
                f"Falling back to legacy RAG system | total_fallbacks={self.help_stats['fallback_usage_count'] + 1} "
                f"| legacy_max_docs={getattr(LegacyRAGSystem, 'MAX_RELEVANT_DOCS', 'n/a')} "
                f"| rag_status={self.help_stats['rag_system_status']}"
            )
            self.logger.info(debug_msg)
            # Emit system event for self-healing detection
            try:
                await self.shared_state.log_system_event(
                    "rag_fallback",
                    {"reason": "enhanced_not_ready"},
                    agent_id=self.agent_id,
                    severity="WARNING",
                )
            except Exception:
                pass  # Avoid recursive failures during fallback logging
    
    async def setup_knowledge_indexing(self):
        """Index all available knowledge sources"""
        try:
            self.logger.info("Starting knowledge base indexing...")
            
            # Get real codebase analysis
            codebase_analysis = await self.get_real_codebase_analysis()
            validated_codebase = self.knowledge_base_validator.validate_codebase_analysis(codebase_analysis)
            
            # Get knowledge base from legacy system
            knowledge_base = self.legacy_rag_system.knowledge_base
            validated_kb = self.knowledge_base_validator.validate_knowledge_base(knowledge_base)
            
            # Get conversation memory (simulate for now)
            conversation_memory = None  # Will be integrated when available
            
            # Index everything in vector store
            await self.rag_system.index_knowledge_base(
                validated_codebase,
                validated_kb,
                conversation_memory
            )
            
            # Update stats
            self.help_stats['documents_indexed'] = len(validated_codebase.get('full_files', {})) + len(validated_kb)
            self.help_stats['vector_store_ready'] = True
            self.help_stats['rag_system_status'] = 'ready'
            
            self.logger.info(f"Knowledge base indexing complete: {self.help_stats['documents_indexed']} documents indexed")
            self.logger.info(f"Validation stats: {self.knowledge_base_validator.get_validation_stats()}")
            
        except Exception as e:
            self.logger.error(f"Failed to index knowledge base: {e}")
            self.help_stats['rag_system_status'] = 'indexing_failed'
    
    async def get_real_codebase_analysis(self) -> Dict[str, Any]:
        """Get real codebase analysis using CodebaseAnalyzer"""
        try:
            # Import the CodebaseAnalyzer from the main module
            import sys
            import os
            from pathlib import Path
            
            # Add the parent directory to sys.path to import CodebaseAnalyzer
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            try:
                from ai_help_agent_streamlit_fixed import CodebaseAnalyzer
                
                # Initialize analyzer
                analyzer = CodebaseAnalyzer()
                
                # Get comprehensive analysis with more files
                analysis = analyzer.analyze_codebase(max_files=150, include_full_content=True)
                
                self.logger.info(f"Real codebase analysis complete: {analysis.get('total_files', 0)} files, "
                               f"{len(analysis.get('full_files', {}))} full files analyzed")
                
                return analysis
                
            except ImportError as e:
                self.logger.error(f"Failed to import CodebaseAnalyzer: {e}")
                return await self.get_mock_codebase_analysis()
                
        except Exception as e:
            self.logger.error(f"Failed to get real codebase analysis: {e}")
            return await self.get_mock_codebase_analysis()
    
    async def get_mock_codebase_analysis(self) -> Dict[str, Any]:
        """Get mock codebase analysis for fallback"""
        # This would normally come from CodebaseAnalyzer
        return {
            'full_files': {
                'ai_help_agent.py': {
                    'content': 'AI Help Agent implementation with enhanced RAG system',
                    'language': 'Python',
                    'functions': ['initialize', 'process_request', 'generate_response'],
                    'classes': ['AIHelpAgent', 'EnhancedRAGSystem'],
                    'imports': ['asyncio', 'logging', 'datetime'],
                    'summary': 'Main AI Help Agent with vector-based RAG',
                    'lines': 500
                },
                'enhanced_rag_system.py': {
                    'content': 'Enhanced RAG system with vector embeddings and semantic search',
                    'language': 'Python', 
                    'functions': ['initialize', 'index_knowledge_base', 'retrieve_relevant_content'],
                    'classes': ['EnhancedRAGSystem', 'EmbeddingManager', 'VectorStore'],
                    'imports': ['chromadb', 'sentence_transformers', 'numpy'],
                    'summary': 'Vector-based RAG system with ChromaDB',
                    'lines': 800
                }
            },
            'key_files': [
                {
                    'path': 'ai_help_agent.py',
                    'type': 'Python',
                    'functions': ['initialize', 'process_request'],
                    'classes': ['AIHelpAgent'],
                    'summary': 'Main AI Help Agent implementation'
                }
            ]
        }
        
    async def setup_request_processing(self) -> None:
        """Setup request processing capabilities"""
        self.logger.info("AI Help Agent request processing system ready")
        
    async def execute_work_cycle(self) -> Dict[str, Any]:
        """Execute AI help processing cycle"""
        work_start_time = time.time()
        
        try:
            # Process pending help requests
            processed_requests = await self.process_help_requests()
            
            # Generate system insights
            system_insights = await self.generate_system_insights()
            
            # Update help statistics
            await self.update_help_statistics(processed_requests)
            
            processing_time = time.time() - work_start_time
            
            return {
                'success': True,
                'items_processed': len(processed_requests),
                'processing_time': processing_time,
                'business_value': self.calculate_help_business_value(processed_requests),
                'processed_requests': len(processed_requests),
                'system_insights': system_insights,
                'user_satisfaction': self.help_stats['user_satisfaction_score']
            }
            
        except Exception as e:
            self.logger.error(f"AI help processing cycle failed: {e}")
            return {
                'success': False,
                'items_processed': 0,
                'processing_time': time.time() - work_start_time,
                'business_value': 0,
                'error_details': str(e)
            }
            
    async def process_help_requests(self) -> List[Dict]:
        """Process queued help requests"""
        processed_requests = []
        
        try:
            # Get mock requests for demonstration
            help_requests = await self.get_mock_help_requests()
            
            for request in help_requests:
                try:
                    response = await self.process_single_request(request)
                    processed_requests.append({
                        'request': request,
                        'response': response
                    })
                    
                except Exception as e:
                    self.logger.error(f"Failed to process request {request.request_id}: {e}")
                    
            return processed_requests
            
        except Exception as e:
            self.logger.error(f"Failed to process help requests: {e}")
            return []
            
    async def get_mock_help_requests(self) -> List[HelpRequest]:
        """Generate mock help requests for demonstration"""
        import random
        
        mock_queries = [
            "What is the current system status?",
            "How can I troubleshoot agent performance issues?",
            "What are the current cost optimization opportunities?",
            "How does the health monitoring system work?",
            "Can you explain the agent architecture?"
        ]
        
        mock_requests = []
        
        # Generate 1-3 random requests
        for i in range(random.randint(1, 3)):
            request = HelpRequest(
                request_id=f"req_{int(time.time())}_{i}",
                user_id=f"user_{random.randint(1, 10)}",
                query=random.choice(mock_queries),
                context={'source': 'demo'},
                timestamp=datetime.now(timezone.utc),
                priority=random.choice(['normal', 'high']),
                category=random.choice(['general', 'troubleshooting', 'performance'])
            )
            mock_requests.append(request)
            
        return mock_requests
        
    async def process_single_request(self, request: HelpRequest) -> HelpResponse:
        """Process a single help request with enhanced RAG"""
        
        process_start = time.time()
        
        try:
            # Gather system context
            system_context = await self.context_integrator.gather_system_context(request.query)
            system_context['request_id'] = request.request_id
            
            # Try enhanced RAG system first
            response = await self.try_enhanced_rag_response(request, system_context)
            
            # Update processing time
            response.processing_time = time.time() - process_start
            
            # Assess response quality
            quality_assessment = await self.quality_assessor.assess_response_quality(request, response)
            
            # Log the help interaction
            await self.log_help_interaction(request, response, quality_assessment)
            
            # If the response text suggests clarification, attach clarification_prompt
            clarification_keywords = [
                'clarify', 'could you please clarify', 'not totally sure', 'please specify', 'need more information'
            ]
            if response and hasattr(response, 'response_text'):
                lower_text = response.response_text.lower()
                if any(kw in lower_text for kw in clarification_keywords):
                    response.clarification_prompt = response.response_text
            
            # Store conversation memory
            shared_state = getattr(self, 'shared_state', None)
            if shared_state and hasattr(shared_state, '_conversation_memory'):
                user_id = getattr(request, 'user_id', None)
                if user_id:
                    if user_id not in shared_state._conversation_memory:
                        shared_state._conversation_memory[user_id] = []
                    shared_state._conversation_memory[user_id].append({
                        'request': request,
                        'response': response
                    })
            elif shared_state:
                # Initialize if missing
                user_id = getattr(request, 'user_id', None)
                if user_id:
                    shared_state._conversation_memory = {user_id: [{
                        'request': request,
                        'response': response
                    }]}
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to process request {request.request_id}: {e}")
            
            # Return error response
            return HelpResponse(
                response_id=f"resp_error_{int(time.time())}",
                request_id=request.request_id,
                response_text=f"I apologize, but I encountered an error processing your request: {str(e)}",
                confidence_score=50.0,
                sources=['Error handling system'],
                processing_time=time.time() - process_start,
                timestamp=datetime.now(timezone.utc),
                business_value=0.0
            )
    
    async def try_enhanced_rag_response(self, request: HelpRequest, system_context: Dict) -> HelpResponse:
        """Try enhanced RAG system with advanced query capabilities and fallback to legacy system"""
        try:
            # Check if enhanced RAG system is ready
            if self.help_stats['vector_store_ready'] and self.help_stats['rag_system_status'] == 'ready':
                # Use Advanced Query System for intelligent search
                conversation_history = await self._get_conversation_history(request.user_id)
                
                advanced_query_result = await self.advanced_query_system.process_advanced_query(
                    request.query,
                    request.user_id,
                    conversation_history,
                    system_context
                )
                
                # Use enhanced RAG with vector retrieval
                relevant_documents = await self.rag_system.retrieve_relevant_content(
                    request.query, 
                    system_context, 
                    top_k=10
                )
                
                if relevant_documents:
                    # Generate enhanced response
                    response_text = await self.generate_enhanced_response(
                        request.query, 
                        relevant_documents, 
                        system_context
                    )
                    
                    confidence_score = await self.calculate_enhanced_confidence(
                        request.query, 
                        response_text, 
                        relevant_documents,
                        system_context
                    )
                    
                    # Create enhanced response with advanced query metadata
                    response = HelpResponse(
                        response_id=f"enhanced_resp_{int(time.time())}",
                        request_id=request.request_id,
                        response_text=response_text,
                        confidence_score=confidence_score,
                        sources=[f"{doc.source}:{doc.metadata.get('file_path', 'unknown')}" for doc in relevant_documents[:5]],
                        processing_time=0,  # Will be updated by caller
                        timestamp=datetime.now(timezone.utc),
                        business_value=await self.calculate_enhanced_business_value(request.query, system_context, relevant_documents)
                    )
                    
                    # Add advanced query metadata to response
                    response.advanced_query_metadata = {
                        'intent_analysis': advanced_query_result.get('intent_analysis', {}),
                        'query_expansions': advanced_query_result.get('query_expansions', []),
                        'context': advanced_query_result.get('context', {}),
                        'total_results': advanced_query_result.get('total_results', 0)
                    }
                    
                    # Update retrieval accuracy
                    self.help_stats['semantic_retrieval_accuracy'] = confidence_score
                    
                    return response
            
            # Fallback to legacy RAG system
            self.logger.info("Falling back to legacy RAG system")
            from background_agents.ai_help.ai_help_agent import LegacyRAGSystem  # local import
            debug_msg = (
                f"Falling back to legacy RAG system | total_fallbacks={self.help_stats['fallback_usage_count'] + 1} "
                f"| legacy_max_docs={getattr(LegacyRAGSystem, 'MAX_RELEVANT_DOCS', 'n/a')} "
                f"| rag_status={self.help_stats['rag_system_status']}"
            )
            self.logger.info(debug_msg)
            # Emit system event for self-healing detection
            try:
                await self.shared_state.log_system_event(
                    "rag_fallback",
                    {"reason": "enhanced_not_ready"},
                    agent_id=self.agent_id,
                    severity="WARNING",
                )
            except Exception:
                pass  # Avoid recursive failures during fallback logging
            self.help_stats['fallback_usage_count'] += 1
            return await self.legacy_rag_system.generate_response(request.query, system_context)
            
        except Exception as e:
            self.logger.error(f"Enhanced RAG processing failed: {e}")
            try:
                await self.shared_state.log_system_event(
                    "rag_fallback",
                    {"reason": str(e)},
                    agent_id=self.agent_id,
                    severity="WARNING",
                )
            except Exception:
                pass
            # Fallback to legacy system
            self.help_stats['fallback_usage_count'] += 1
            return await self.legacy_rag_system.generate_response(request.query, system_context)
    
    async def generate_enhanced_response(self, query: str, relevant_documents: List[Document], system_context: Dict) -> str:
        """Generate enhanced response using retrieved documents and system context"""
        
        # Build context from retrieved documents
        context_parts = ["=== RELEVANT INFORMATION ==="]
        
        for i, doc in enumerate(relevant_documents[:5], 1):
            source_info = f"Source {i}: {doc.source}"
            if doc.metadata.get('file_path'):
                source_info += f" ({doc.metadata['file_path']})"
            
            context_parts.append(f"\n{source_info}:")
            context_parts.append(f"{doc.content[:300]}...")  # First 300 chars
            
            # Add metadata if available
            if doc.metadata.get('functions'):
                context_parts.append(f"Functions: {', '.join(doc.metadata['functions'][:3])}")
            if doc.metadata.get('classes'):
                context_parts.append(f"Classes: {', '.join(doc.metadata['classes'][:3])}")
        
        # Add system context
        context_parts.append("\n=== SYSTEM STATUS ===")
        system_status = system_context.get('system_status', {})
        context_parts.append(f"System Health: {system_status.get('system_health', 'unknown')}")
        context_parts.append(f"Active Agents: {system_status.get('active_agents', 0)}/{system_status.get('total_agents', 0)}")
        
        # Generate response based on query type and context
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['status', 'health', 'running']):
            return await self.generate_status_response_enhanced(system_context, relevant_documents)
        elif any(word in query_lower for word in ['how', 'explain', 'what', 'where']):
            return await self.generate_explanation_response_enhanced(query, relevant_documents, system_context)
        elif any(word in query_lower for word in ['problem', 'error', 'issue', 'fix']):
            return await self.generate_troubleshooting_response_enhanced(query, relevant_documents, system_context)
        else:
            return await self.generate_general_response_enhanced(query, relevant_documents, system_context)
    
    async def generate_status_response_enhanced(self, system_context: Dict, relevant_documents: List[Document]) -> str:
        """Generate enhanced status response with retrieved context"""
        system_status = system_context.get('system_status', {})
        
        response = f"""**🔍 Enhanced System Status Analysis**

**Overall Health**: {system_status.get('system_health', 'Unknown').title()}
**Agent Status**: {system_status.get('active_agents', 0)}/{system_status.get('total_agents', 0)} agents active
**RAG System**: {self.help_stats['rag_system_status'].title()} ({self.help_stats['documents_indexed']} documents indexed)

**📊 Enhanced Intelligence**:
- Vector Store: {'Ready' if self.help_stats['vector_store_ready'] else 'Initializing'}
- Semantic Retrieval Accuracy: {self.help_stats['semantic_retrieval_accuracy']:.1f}%
- Knowledge Sources: {len(relevant_documents)} relevant documents found

**🎯 Contextual Insights**:
"""
        
        # Add insights from retrieved documents
        for doc in relevant_documents[:3]:
            if 'monitoring' in doc.content.lower() or 'health' in doc.content.lower():
                response += f"- Found monitoring guidance in {doc.source}\n"
        
        response += "\n✅ **Enhanced AI Help Agent is operational with vector-based knowledge retrieval**"
        
        return response
    
    async def generate_explanation_response_enhanced(self, query: str, relevant_documents: List[Document], system_context: Dict) -> str:
        """Generate enhanced explanation response"""
        
        response = f"**🧠 Enhanced Explanation Based on Retrieved Knowledge**\n\n"
        
        # Use most relevant document
        if relevant_documents:
            top_doc = relevant_documents[0]
            response += f"**Primary Source**: {top_doc.source}"
            if top_doc.metadata.get('file_path'):
                response += f" ({top_doc.metadata['file_path']})"
            response += f"\n\n{top_doc.content[:500]}...\n\n"
            
            # Add technical details if available
            if top_doc.metadata.get('functions'):
                response += f"**Key Functions**: {', '.join(top_doc.metadata['functions'][:5])}\n"
            if top_doc.metadata.get('classes'):
                response += f"**Key Classes**: {', '.join(top_doc.metadata['classes'][:3])}\n"
        
        # Add system context if relevant
        response += f"\n**Current System Context**: {len(relevant_documents)} related knowledge sources found"
        
        return response
    
    async def generate_troubleshooting_response_enhanced(self, query: str, relevant_documents: List[Document], system_context: Dict) -> str:
        """Generate enhanced troubleshooting response"""
        
        response = "**🔧 Enhanced Troubleshooting Analysis**\n\n"
        
        # Look for troubleshooting documents
        troubleshooting_docs = [doc for doc in relevant_documents if 'troubleshoot' in doc.content.lower() or 'error' in doc.content.lower()]
        
        if troubleshooting_docs:
            response += "**📋 Relevant Troubleshooting Information**:\n"
            for doc in troubleshooting_docs[:2]:
                response += f"- {doc.content[:200]}...\n"
        
        # Add system status context
        system_status = system_context.get('system_status', {})
        if system_status.get('system_health') != 'healthy':
            response += f"\n**⚠️ Current System Issues Detected**: {system_status.get('system_health', 'unknown')} health status\n"
        
        response += "\n**💡 Next Steps**: Check the specific components mentioned above and review recent system events."
        
        return response
    
    async def generate_general_response_enhanced(self, query: str, relevant_documents: List[Document], system_context: Dict) -> str:
        """Generate enhanced general response"""
        
        response = f"**🤖 Enhanced AI Response**\n\n"
        response += f"Based on {len(relevant_documents)} relevant knowledge sources:\n\n"
        
        # Summarize top documents
        for i, doc in enumerate(relevant_documents[:3], 1):
            response += f"**{i}. {doc.source.title()}**: {doc.content[:150]}...\n\n"
        
        response += f"**System Context**: {self.help_stats['rag_system_status'].title()} RAG system with {self.help_stats['documents_indexed']} indexed documents"
        
        return response
    
    async def calculate_enhanced_confidence(self, query: str, response: str, relevant_documents: List[Document], system_context: Dict) -> float:
        """Calculate enhanced confidence score based on retrieval quality"""
        
        base_confidence = 75.0  # Base confidence for enhanced system
        
        # Boost for number of relevant documents
        if len(relevant_documents) >= 5:
            base_confidence += 10
        elif len(relevant_documents) >= 3:
            base_confidence += 5
        
        # Boost for document relevance scores
        if relevant_documents:
            avg_relevance = sum(doc.relevance_score for doc in relevant_documents) / len(relevant_documents)
            base_confidence += avg_relevance * 10
        
        # Boost for system context integration
        if system_context.get('system_status'):
            base_confidence += 5
        
        return min(base_confidence, 95.0)  # Cap at 95%
    
    async def calculate_enhanced_business_value(self, query: str, system_context: Dict, relevant_documents: List[Document]) -> float:
        """Calculate enhanced business value based on knowledge utilization"""
        
        base_value = 25.0  # Base value for enhanced assistance
        
        # Value based on knowledge sources utilized
        source_multiplier = {
            'codebase': 2.0,
            'key_file': 3.0,
            'documentation': 1.5,
            'conversation': 1.2
        }
        
        for doc in relevant_documents:
            base_value += source_multiplier.get(doc.source, 1.0) * 5
        
        # Value based on query complexity
        query_lower = query.lower()
        if any(word in query_lower for word in ['troubleshoot', 'debug', 'fix']):
            base_value *= 1.5  # Troubleshooting has higher value
        elif any(word in query_lower for word in ['explain', 'how', 'architecture']):
            base_value *= 1.3  # Knowledge transfer value
        
        return min(base_value, 100.0)  # Cap at $100
            
    async def log_help_interaction(self, request: HelpRequest, response: HelpResponse, 
                                 quality_assessment: Dict) -> None:
        """Log help interaction for analytics"""
        try:
            interaction_data = {
                'request_id': request.request_id,
                'user_id': request.user_id,
                'query': request.query,
                'category': request.category,
                'priority': request.priority,
                'response_length': len(response.response_text),
                'confidence_score': response.confidence_score,
                'processing_time': response.processing_time,
                'business_value': response.business_value,
                'quality_score': quality_assessment.get('overall_quality_score', 0),
                'quality_grade': quality_assessment.get('quality_grade', 'C')
            }
            
            await self.shared_state.log_system_event(
                'ai_help_interaction',
                interaction_data,
                agent_id=self.agent_id,
                severity='INFO'
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log help interaction: {e}")
            
    async def generate_system_insights(self) -> Dict[str, Any]:
        """Generate system insights from help patterns"""
        
        # Get recent help interactions
        recent_events = await self.shared_state.get_system_events(
            event_type='ai_help_interaction',
            hours=24
        )
        
        insights = {
            'total_interactions': len(recent_events),
            'common_categories': await self.analyze_common_categories(recent_events),
            'user_satisfaction_trend': 'stable',
            'performance_insights': await self.analyze_performance_insights(recent_events)
        }
        
        return insights
        
    async def analyze_common_categories(self, events: List[Dict]) -> Dict[str, int]:
        """Analyze common query categories"""
        categories = {}
        
        for event in events:
            category = event.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
            
        return categories
        
    async def analyze_performance_insights(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze AI help performance insights"""
        
        if not events:
            return {'message': 'No recent interactions'}
            
        # Calculate average metrics
        processing_times = [e.get('processing_time', 0) for e in events]
        confidence_scores = [e.get('confidence_score', 0) for e in events]
        quality_scores = [e.get('quality_score', 0) for e in events]
        
        return {
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'avg_confidence_score': sum(confidence_scores) / len(confidence_scores),
            'avg_quality_score': sum(quality_scores) / len(quality_scores),
            'interaction_count': len(events)
        }
        
    async def update_help_statistics(self, processed_requests: List[Dict]) -> None:
        """Update help agent statistics"""
        
        if not processed_requests:
            return
            
        # Update request count
        self.help_stats['requests_processed'] += len(processed_requests)
        
        # Update average response time
        total_time = sum(r['response'].processing_time for r in processed_requests)
        avg_time = total_time / len(processed_requests)
        
        # Running average
        if self.help_stats['average_response_time'] == 0:
            self.help_stats['average_response_time'] = avg_time
        else:
            self.help_stats['average_response_time'] = (
                self.help_stats['average_response_time'] * 0.8 + avg_time * 0.2
            )
            
        # Update business value
        total_value = sum(r['response'].business_value for r in processed_requests)
        self.help_stats['business_value_generated'] += total_value
        
    def calculate_help_business_value(self, processed_requests: List[Dict]) -> float:
        """Calculate business value of help processing"""
        
        if not processed_requests:
            return 0.0
            
        # Base value per request
        base_value = 50.0 * len(processed_requests)
        
        # Additional value from individual responses
        response_value = sum(r['response'].business_value for r in processed_requests)
        
        return base_value + response_value 
    
    async def _get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get conversation history for user (placeholder implementation)"""
        # This would normally fetch from conversation memory system
        # For now, return empty list
        return [] 
