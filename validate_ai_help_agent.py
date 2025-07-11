#!/usr/bin/env python3
"""
AI Help Agent - Pre-Test Validation
===================================

This script validates that the AI Help Agent is ready for the final user test
by testing all core functionality programmatically.

Tests:
1. System initialization
2. Context integration
3. RAG system functionality  
4. Quality assessment
5. End-to-end workflow

Usage: python validate_ai_help_agent.py
"""

import asyncio
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any

class AIHelpAgentValidator:
    def __init__(self):
        self.shared_state = None
        self.ai_help_agent = None
        self.test_results = []

    async def initialize(self):
        """Initialize AI Help Agent for validation"""
        try:
            from background_agents.coordination.shared_state import SharedState
            from background_agents.ai_help.ai_help_agent import AIHelpAgent
            
            # Initialize shared state
            self.shared_state = SharedState()
            await self.shared_state.initialize()
            
            # Initialize AI Help Agent
            self.ai_help_agent = AIHelpAgent(shared_state=self.shared_state)
            await self.ai_help_agent.initialize()
            
            print("✅ AI Help Agent initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize AI Help Agent: {e}")
            return False

    async def test_system_context_integration(self):
        """Test SystemContextIntegrator functionality"""
        print("\n🔍 Testing System Context Integration...")
        
        try:
            test_query = "What is the current system status?"
            
            start_time = time.time()
            context = await self.ai_help_agent.context_integrator.gather_system_context(test_query)
            processing_time = time.time() - start_time
            
            # Validate context structure
            required_keys = ['system_status', 'query_category']
            missing_keys = [key for key in required_keys if key not in context]
            
            result = {
                'test': 'system_context_integration',
                'processing_time': processing_time,
                'context_keys': list(context.keys()),
                'missing_keys': missing_keys,
                'success': len(missing_keys) == 0 and processing_time < 5.0,
                'details': {
                    'system_status': context.get('system_status', {}),
                    'query_category': context.get('query_category', 'unknown')
                }
            }
            
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ System context integration: {processing_time:.3f}s")
                print(f"   Context keys: {len(context)} ({', '.join(context.keys())})")
                return True
            else:
                print(f"❌ System context integration failed")
                print(f"   Missing keys: {missing_keys}")
                return False
                
        except Exception as e:
            print(f"❌ System context integration error: {e}")
            self.test_results.append({
                'test': 'system_context_integration',
                'error': str(e),
                'success': False
            })
            return False

    async def test_rag_system(self):
        """Test AdvancedRAGSystem functionality"""
        print("\n🔍 Testing RAG System...")
        
        try:
            test_query = "Explain the AI Help Agent architecture"
            test_context = {'query_category': 'code_analysis'}
            
            start_time = time.time()
            response = await self.ai_help_agent.rag_system.generate_response(test_query, test_context)
            processing_time = time.time() - start_time
            
            result = {
                'test': 'rag_system',
                'processing_time': processing_time,
                'response_length': len(response.response_text),
                'confidence_score': response.confidence_score,
                'business_value': response.business_value,
                'sources_count': len(response.sources),
                'success': (
                    processing_time < 10.0 and 
                    response.confidence_score > 0 and 
                    len(response.response_text) > 50
                ),
                'details': {
                    'response_preview': response.response_text[:100] + "...",
                    'sources': response.sources
                }
            }
            
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ RAG system: {processing_time:.3f}s")
                print(f"   Response: {len(response.response_text)} chars, {response.confidence_score:.1f}% confidence")
                print(f"   Business value: ${response.business_value:.2f}")
                return True
            else:
                print(f"❌ RAG system failed")
                return False
                
        except Exception as e:
            print(f"❌ RAG system error: {e}")
            self.test_results.append({
                'test': 'rag_system',
                'error': str(e),
                'success': False
            })
            return False

    async def test_quality_assessment(self):
        """Test QualityAssessmentSystem functionality"""
        print("\n🔍 Testing Quality Assessment...")
        
        try:
            from background_agents.ai_help.ai_help_agent import HelpRequest
            
            # Create test request and response
            test_request = HelpRequest(
                request_id="validation_test",
                user_id="validator", 
                query="Test query for quality assessment",
                context={'test': True},
                timestamp=datetime.now(timezone.utc),
                priority='normal',
                category='system_status'
            )
            
            test_response = {
                'response_text': 'This is a test response for quality assessment validation.',
                'confidence_score': 85.0,
                'business_value': 50.0,
                'sources': ['test_source']
            }
            
            start_time = time.time()
            assessment = await self.ai_help_agent.quality_assessor.assess_response_quality(
                test_request, 
                type('Response', (), test_response)()
            )
            processing_time = time.time() - start_time
            
            result = {
                'test': 'quality_assessment',
                'processing_time': processing_time,
                'assessment_keys': list(assessment.keys()) if isinstance(assessment, dict) else [],
                'quality_score': assessment.get('overall_quality_score', 0) if isinstance(assessment, dict) else 0,
                'quality_grade': assessment.get('quality_grade', 'F') if isinstance(assessment, dict) else 'F',
                'success': processing_time < 5.0 and isinstance(assessment, dict),
                'details': assessment if isinstance(assessment, dict) else str(assessment)
            }
            
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ Quality assessment: {processing_time:.3f}s")
                print(f"   Quality score: {result['quality_score']}/100, Grade: {result['quality_grade']}")
                return True
            else:
                print(f"❌ Quality assessment failed")
                return False
                
        except Exception as e:
            print(f"❌ Quality assessment error: {e}")
            self.test_results.append({
                'test': 'quality_assessment',
                'error': str(e),
                'success': False
            })
            return False

    async def test_integration_guidance(self):
        """Test new agent integration guidance functionality"""
        print("\n🔍 Testing Integration Guidance...")
        
        try:
            integration_queries = [
                "How do I integrate a new monitoring agent into the background agents system?",
                "What steps should I follow to add a new data processing agent safely?",
                "Guide me through creating a new agent that follows existing patterns"
            ]
            
            total_guidance_quality = 0
            successful_guidance = 0
            
            for query in integration_queries:
                try:
                    context = await self.ai_help_agent.context_integrator.gather_system_context(query)
                    response = await self.ai_help_agent.rag_system.generate_response(query, context)
                    
                    # Check for integration-specific keywords
                    response_lower = response.response_text.lower()
                    integration_keywords = [
                        'step', 'integrate', 'agent', 'class', 'inherit', 'pattern',
                        'database', 'register', 'test', 'validate', 'config'
                    ]
                    
                    keywords_found = sum(1 for keyword in integration_keywords 
                                       if keyword in response_lower)
                    
                    if keywords_found >= 3 and response.confidence_score > 40:
                        total_guidance_quality += response.confidence_score
                        successful_guidance += 1
                        
                except Exception as e:
                    print(f"     Warning: Integration query failed: {e}")
            
            avg_guidance_quality = total_guidance_quality / max(successful_guidance, 1)
            
            result = {
                'test': 'integration_guidance',
                'queries_tested': len(integration_queries),
                'successful_guidance': successful_guidance,
                'avg_guidance_quality': avg_guidance_quality,
                'success': successful_guidance >= 2 and avg_guidance_quality > 50
            }
            
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ Integration guidance: {avg_guidance_quality:.1f}% average quality")
                print(f"   {successful_guidance}/{len(integration_queries)} guidance responses successful")
                return True
            else:
                print(f"❌ Integration guidance failed")
                return False
                
        except Exception as e:
            print(f"❌ Integration guidance error: {e}")
            self.test_results.append({
                'test': 'integration_guidance',
                'error': str(e),
                'success': False
            })
            return False

    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔍 Testing End-to-End Workflow...")
        
        test_scenarios = [
            {
                'query': 'What is the current system status?',
                'category': 'system_status',
                'expected_keywords': ['agent', 'system', 'status']
            },
            {
                'query': 'Explain the background agents architecture',
                'category': 'code_analysis', 
                'expected_keywords': ['architecture', 'agent', 'class']
            },
            {
                'query': 'What performance issues should I investigate?',
                'category': 'performance',
                'expected_keywords': ['performance', 'issue', 'monitor']
            },
            {
                'query': 'How do I integrate a new monitoring agent into the system?',
                'category': 'integration',
                'expected_keywords': ['agent', 'integrate', 'system', 'steps']
            }
        ]
        
        successful_scenarios = 0
        total_processing_time = 0
        
        for i, scenario in enumerate(test_scenarios):
            try:
                print(f"   Scenario {i+1}: {scenario['query'][:50]}...")
                
                start_time = time.time()
                
                # 1. Context integration
                context = await self.ai_help_agent.context_integrator.gather_system_context(scenario['query'])
                
                # 2. RAG response generation
                response = await self.ai_help_agent.rag_system.generate_response(scenario['query'], context)
                
                # 3. Quality assessment (simplified)
                processing_time = time.time() - start_time
                total_processing_time += processing_time
                
                # Check for expected keywords
                response_lower = response.response_text.lower()
                keywords_found = sum(1 for keyword in scenario['expected_keywords'] 
                                   if keyword.lower() in response_lower)
                
                scenario_success = (
                    processing_time < 10.0 and
                    response.confidence_score > 30 and
                    len(response.response_text) > 30 and
                    keywords_found >= 1
                )
                
                if scenario_success:
                    successful_scenarios += 1
                    print(f"     ✅ {processing_time:.2f}s, {response.confidence_score:.1f}% confidence")
                else:
                    print(f"     ❌ Failed: {processing_time:.2f}s, {response.confidence_score:.1f}% confidence")
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
        
        success_rate = (successful_scenarios / len(test_scenarios)) * 100
        avg_processing_time = total_processing_time / len(test_scenarios)
        
        result = {
            'test': 'end_to_end_workflow',
            'scenarios_tested': len(test_scenarios),
            'successful_scenarios': successful_scenarios,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'total_processing_time': total_processing_time,
            'success': success_rate >= 66.7 and avg_processing_time < 8.0  # 2/3 scenarios pass
        }
        
        self.test_results.append(result)
        
        if result['success']:
            print(f"✅ End-to-end workflow: {successful_scenarios}/{len(test_scenarios)} scenarios passed")
            print(f"   Success rate: {success_rate:.1f}%, Avg time: {avg_processing_time:.2f}s")
            return True
        else:
            print(f"❌ End-to-end workflow failed: {success_rate:.1f}% success rate")
            return False

    async def test_business_value_calculation(self):
        """Test business value calculation functionality"""
        print("\n🔍 Testing Business Value Calculation...")
        
        try:
            test_queries = [
                "What is the current system health score?",
                "How can I optimize database performance?", 
                "What errors occurred in the last hour?"
            ]
            
            total_business_value = 0
            successful_calculations = 0
            
            for query in test_queries:
                try:
                    context = await self.ai_help_agent.context_integrator.gather_system_context(query)
                    response = await self.ai_help_agent.rag_system.generate_response(query, context)
                    
                    if response.business_value > 0:
                        total_business_value += response.business_value
                        successful_calculations += 1
                        
                except Exception as e:
                    print(f"     Warning: Query failed: {e}")
            
            avg_business_value = total_business_value / max(successful_calculations, 1)
            
            result = {
                'test': 'business_value_calculation',
                'queries_tested': len(test_queries),
                'successful_calculations': successful_calculations,
                'total_business_value': total_business_value,
                'avg_business_value': avg_business_value,
                'success': successful_calculations >= 2 and avg_business_value > 0
            }
            
            self.test_results.append(result)
            
            if result['success']:
                print(f"✅ Business value calculation: ${avg_business_value:.2f} average")
                print(f"   {successful_calculations}/{len(test_queries)} calculations successful")
                return True
            else:
                print(f"❌ Business value calculation failed")
                return False
                
        except Exception as e:
            print(f"❌ Business value calculation error: {e}")
            self.test_results.append({
                'test': 'business_value_calculation',
                'error': str(e),
                'success': False
            })
            return False

    async def cleanup(self):
        """Clean up resources"""
        if self.shared_state:
            await self.shared_state.close()

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "="*70)
        print("📊 AI HELP AGENT VALIDATION SUMMARY")
        print("="*70)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get('success', False))
        success_rate = (successful_tests / max(total_tests, 1)) * 100
        
        print(f"🎯 Overall Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        
        for result in self.test_results:
            status = "✅" if result.get('success', False) else "❌"
            test_name = result['test'].replace('_', ' ').title()
            
            if 'processing_time' in result:
                print(f"{status} {test_name}: {result['processing_time']:.3f}s")
            elif 'error' in result:
                print(f"{status} {test_name}: Error - {result['error'][:50]}...")
            else:
                print(f"{status} {test_name}")
        
        print("\n🎯 Production Readiness Assessment:")
        if success_rate >= 80:
            print("🎉 READY FOR FINAL USER TEST!")
            print("   All critical components are functional")
            print("   Proceed with confidence to user validation")
        elif success_rate >= 60:
            print("⚠️ MOSTLY READY - Some issues detected")
            print("   Consider addressing failures before user test")
        else:
            print("❌ NOT READY - Significant issues detected")
            print("   Fix critical failures before proceeding")
        
        print("\n📋 Next Steps:")
        if success_rate >= 60:
            print("   1. Run: python run_final_test.py")
            print("   2. Complete user validation test")
            print("   3. Aim for 80+ Production Readiness Score")
        else:
            print("   1. Review and fix failed components")
            print("   2. Re-run validation")
            print("   3. Ensure all tests pass before user test")

async def main():
    """Main validation function"""
    print("🎯 AI HELP AGENT - PRE-TEST VALIDATION")
    print("="*50)
    print("🔍 Validating core functionality before final user test")
    print("⏱️ Estimated duration: 2-3 minutes")
    print("="*50)
    
    validator = AIHelpAgentValidator()
    
    try:
        # Initialize
        if not await validator.initialize():
            print("\n❌ Initialization failed - cannot proceed")
            return
        
        # Run validation tests
        tests = [
            validator.test_system_context_integration(),
            validator.test_rag_system(),
            validator.test_quality_assessment(),
            validator.test_business_value_calculation(),
            validator.test_integration_guidance(),
            validator.test_end_to_end_workflow()
        ]
        
        print(f"\n🧪 Running {len(tests)} validation tests...")
        print("   1. System Context Integration")
        print("   2. RAG System Response Generation") 
        print("   3. Quality Assessment")
        print("   4. Business Value Calculation")
        print("   5. Integration Guidance (NEW)")
        print("   6. End-to-End Workflow")
        
        for test in tests:
            await test
        
        # Print summary
        validator.print_summary()
        
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
    finally:
        await validator.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 