#!/usr/bin/env python3
"""
Test Knowledge Update Mechanisms
Verifies that the AI Help Agent can find new code like enhanced_rag_system.py
"""

import sys
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_streamlit_agent_knowledge():
    """Test that StreamlitAIHelpAgent can find Enhanced RAG code"""
    
    print("🧪 Testing StreamlitAIHelpAgent knowledge update...")
    
    try:
        from ai_help_agent_streamlit_fixed import StreamlitAIHelpAgent
        
        # Initialize the agent
        agent = StreamlitAIHelpAgent()
        print("✅ StreamlitAIHelpAgent initialized")
        
        # Force refresh to pick up new files
        agent.force_refresh_codebase_analysis()
        print("✅ Forced codebase analysis refresh")
        
        # Get codebase analysis
        analysis = agent._get_codebase_analysis()
        print(f"✅ Codebase analysis: {analysis.get('total_files', 0)} files")
        
        # Check for Enhanced RAG system (handle path separators)
        enhanced_rag_found = False
        enhanced_rag_files = []
        
        for file_path in analysis.get('full_files', {}).keys():
            normalized_path = file_path.replace('\\', '/')
            if 'enhanced_rag_system.py' in normalized_path:
                enhanced_rag_found = True
                enhanced_rag_files.append(file_path)
        
        if enhanced_rag_found:
            print(f"✅ Enhanced RAG file found: {enhanced_rag_files}")
        else:
            print("❌ Enhanced RAG file NOT found in analysis")
            print("Available files with 'enhanced' in name:")
            for file_path in analysis.get('full_files', {}).keys():
                if 'enhanced' in file_path.lower():
                    print(f"   - {file_path}")
        
        # Test enhanced query context
        print("\n🔍 Testing query context for Enhanced RAG...")
        query_context = agent._get_enhanced_code_context("Enhanced RAG System")
        
        relevant_files = query_context.get('relevant_files', [])
        print(f"✅ Query context: {len(relevant_files)} relevant files found")
        
        # Check if Enhanced RAG is in relevant files
        enhanced_in_relevant = any(
            'enhanced_rag_system' in rf.get('path', '').lower() 
            for rf in relevant_files
        )
        
        if enhanced_in_relevant:
            print("✅ Enhanced RAG found in relevant files for query")
        else:
            print("❌ Enhanced RAG NOT found in relevant files")
            print("Relevant files found:")
            for rf in relevant_files[:5]:
                print(f"   - {rf.get('path', 'unknown')} (score: {rf.get('relevance_score', 0)})")
        
        return enhanced_rag_found and enhanced_in_relevant
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_background_agent_knowledge():
    """Test that background AI Help Agent can access real codebase"""
    
    print("\n🧪 Testing Background AI Help Agent knowledge...")
    
    try:
        from background_agents.ai_help.ai_help_agent import AIHelpAgent
        
        # Initialize the agent
        agent = AIHelpAgent(shared_state=None)
        print("✅ Background AI Help Agent initialized")
        
        # Test real codebase analysis
        import asyncio
        analysis = asyncio.run(agent.get_real_codebase_analysis())
        
        print(f"✅ Real codebase analysis: {analysis.get('total_files', 0)} files")
        
        # Check for Enhanced RAG system
        enhanced_found = False
        for file_path in analysis.get('full_files', {}).keys():
            if 'enhanced_rag_system' in file_path.lower():
                enhanced_found = True
                print(f"✅ Enhanced RAG found in background agent: {file_path}")
                break
        
        if not enhanced_found:
            print("❌ Enhanced RAG NOT found in background agent analysis")
        
        return enhanced_found
        
    except Exception as e:
        print(f"❌ Background agent test failed: {e}")
        return False

def simulate_user_query():
    """Simulate the user queries that were failing"""
    
    print("\n🎯 Simulating user queries...")
    
    try:
        from ai_help_agent_streamlit_fixed import StreamlitAIHelpAgent
        
        agent = StreamlitAIHelpAgent()
        agent.force_refresh_codebase_analysis()
        
        # Test queries that were failing
        test_queries = [
            "can you find get_enhanced_rag_status method?",
            "can you find Enhanced RAG System code and explain it to me?",
            "where is the vector search implementation?",
            "show me the ChromaDB integration code"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: '{query}'")
            
            # Check if it's code-related
            is_code_related = agent._is_code_related_query(query)
            print(f"   Code-related: {is_code_related}")
            
            if is_code_related:
                # Get code context
                code_context = agent._get_enhanced_code_context(query)
                relevant_files = code_context.get('relevant_files', [])
                
                print(f"   Relevant files found: {len(relevant_files)}")
                
                # Check for Enhanced RAG in results
                enhanced_found = any(
                    'enhanced_rag' in rf.get('path', '').lower() 
                    for rf in relevant_files
                )
                
                if enhanced_found:
                    print("   ✅ Enhanced RAG found in query results!")
                else:
                    print("   ❌ Enhanced RAG NOT found in query results")
                    if relevant_files:
                        print("   Top relevant files:")
                        for rf in relevant_files[:3]:
                            print(f"     - {rf.get('path', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query simulation failed: {e}")
        return False

def main():
    print("🤖 Knowledge Update Test Suite")
    print("=" * 50)
    
    # Test individual components
    streamlit_success = test_streamlit_agent_knowledge()
    background_success = test_background_agent_knowledge()
    query_success = simulate_user_query()
    
    print(f"\n🎯 Test Results:")
    print(f"✅ Streamlit Agent Knowledge: {'PASS' if streamlit_success else 'FAIL'}")
    print(f"✅ Background Agent Knowledge: {'PASS' if background_success else 'FAIL'}")
    print(f"✅ Query Simulation: {'PASS' if query_success else 'FAIL'}")
    
    if streamlit_success and background_success and query_success:
        print("\n🎉 All tests passed! Knowledge update is working.")
        print("The AI should now be able to find Enhanced RAG code.")
    else:
        print("\n⚠️ Some tests failed. Knowledge update needs more work.")
    
    return streamlit_success and background_success and query_success

if __name__ == "__main__":
    main() 