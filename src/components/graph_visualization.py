#!/usr/bin/env python3
"""
Advanced UI Graph Visualization for Cross-References

Interactive graph visualization component for displaying code relationships,
function call graphs, class inheritance trees, and dependency maps.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime
import asyncio
import logging

# Add the project root to the path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import clean versions instead of problematic background agents
try:
    from clean_pynarrative_agent import PyNarrativeAgent, NarrativeVisualizationRequest, NarrativeVisualizationResult
    PY_NARRATIVE_AVAILABLE = True
except ImportError:
    PY_NARRATIVE_AVAILABLE = False
    print("⚠️  Clean PyNarrative agent not available")

# Create simplified versions of the systems to avoid import issues
class EnhancedRAGSystem:
    """Simplified RAG system for graph visualization"""
    async def initialize(self):
        return True

class AdvancedQuerySystem:
    """Simplified query system for graph visualization"""
    def __init__(self, rag_system):
        self.rag_system = rag_system


class CodeGraphVisualizer:
    """Advanced code graph visualization system"""
    
    def __init__(self):
        self.rag_system = None
        self.query_system = None
        self.graph_data = {}
        self.visualization_config = {
            'node_size': 20,
            'edge_width': 2,
            'node_color': '#1f77b4',
            'edge_color': '#666666',
            'highlight_color': '#ff7f0e',
            'background_color': '#ffffff',
            'text_color': '#000000',
            'font_size': 12,
            'arrow_size': 10
        }
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the visualization system"""
        try:
            self.rag_system = EnhancedRAGSystem()
            await self.rag_system.initialize()
            
            self.query_system = AdvancedQuerySystem(self.rag_system)
            self.logger.info("Code Graph Visualizer initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Code Graph Visualizer: {e}")
            return False
    
    def create_function_call_graph(self, function_name: str, max_depth: int = 3) -> Dict[str, Any]:
        """Create a function call graph visualization"""
        
        # Build the graph using NetworkX
        G = nx.DiGraph()
        
        # Add the root function
        G.add_node(function_name, type='function', level=0, file='unknown')
        
        # Simulate function call relationships (in real implementation, this would query the RAG system)
        call_relationships = self._get_function_calls(function_name, max_depth)
        
        for caller, callees in call_relationships.items():
            for callee, file_info in callees.items():
                G.add_node(callee, type='function', level=G.nodes[caller]['level'] + 1, file=file_info['file'])
                G.add_edge(caller, callee, type='calls', file=file_info['file'])
        
        return self._convert_networkx_to_plotly(G, f"Function Call Graph: {function_name}")
    
    def create_class_inheritance_tree(self, base_class: str, max_depth: int = 3) -> Dict[str, Any]:
        """Create a class inheritance tree visualization"""
        
        G = nx.DiGraph()
        
        # Add the base class
        G.add_node(base_class, type='class', level=0, file='unknown')
        
        # Simulate inheritance relationships
        inheritance_relationships = self._get_class_inheritance(base_class, max_depth)
        
        for parent, children in inheritance_relationships.items():
            for child, file_info in children.items():
                G.add_node(child, type='class', level=G.nodes[parent]['level'] + 1, file=file_info['file'])
                G.add_edge(parent, child, type='inherits', file=file_info['file'])
        
        return self._convert_networkx_to_plotly(G, f"Class Inheritance Tree: {base_class}")
    
    def create_dependency_graph(self, file_path: str, max_depth: int = 2) -> Dict[str, Any]:
        """Create a dependency graph visualization"""
        
        G = nx.DiGraph()
        
        # Add the root file
        G.add_node(file_path, type='file', level=0)
        
        # Simulate dependency relationships
        dependencies = self._get_file_dependencies(file_path, max_depth)
        
        for file, deps in dependencies.items():
            for dep, dep_type in deps.items():
                G.add_node(dep, type='dependency', level=G.nodes[file]['level'] + 1, dep_type=dep_type)
                G.add_edge(file, dep, type='depends_on', dep_type=dep_type)
        
        return self._convert_networkx_to_plotly(G, f"Dependency Graph: {file_path}")
    
    def create_codebase_overview_graph(self, max_nodes: int = 50) -> Dict[str, Any]:
        """Create an overview graph of the entire codebase"""
        
        G = nx.Graph()
        
        # Simulate codebase structure
        codebase_structure = self._get_codebase_structure(max_nodes)
        
        for file_info in codebase_structure:
            file_path = file_info['file']
            file_type = file_info['type']
            functions = file_info.get('functions', [])
            classes = file_info.get('classes', [])
            
            G.add_node(file_path, 
                      type=file_type, 
                      functions=len(functions), 
                      classes=len(classes),
                      size=len(functions) + len(classes) + 1)
            
            # Add edges based on imports and relationships
            for import_file in file_info.get('imports', []):
                if import_file in G.nodes:
                    G.add_edge(file_path, import_file, type='imports')
        
        return self._convert_networkx_to_plotly(G, "Codebase Overview", layout='force')
    
    def _convert_networkx_to_plotly(self, G: nx.Graph, title: str, layout: str = 'hierarchical') -> Dict[str, Any]:
        """Convert NetworkX graph to Plotly visualization data"""
        
        if layout == 'hierarchical':
            pos = nx.spring_layout(G, k=3, iterations=50)
        else:
            pos = nx.spring_layout(G, k=1, iterations=30)
        
        # Extract node positions
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Node text
            node_data = G.nodes[node]
            if node_data.get('type') == 'function':
                node_text.append(f"Function: {node}<br>File: {node_data.get('file', 'unknown')}")
                node_colors.append('#1f77b4')
            elif node_data.get('type') == 'class':
                node_text.append(f"Class: {node}<br>File: {node_data.get('file', 'unknown')}")
                node_colors.append('#ff7f0e')
            elif node_data.get('type') == 'file':
                node_text.append(f"File: {node}<br>Functions: {node_data.get('functions', 0)}<br>Classes: {node_data.get('classes', 0)}")
                node_colors.append('#2ca02c')
            else:
                node_text.append(f"{node}<br>Type: {node_data.get('type', 'unknown')}")
                node_colors.append('#d62728')
            
            # Node size based on importance
            if 'size' in node_data:
                node_sizes.append(node_data['size'] * 5 + 10)
            else:
                node_sizes.append(15)
        
        # Extract edge positions
        edge_x = []
        edge_y = []
        edge_text = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            edge_data = G.edges[edge]
            edge_text.append(f"{edge[0]} → {edge[1]}<br>Type: {edge_data.get('type', 'unknown')}")
        
        # Create the figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            showlegend=False
        ))
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=600
        )
        
        return {
            'figure': fig,
            'graph': G,
            'node_count': len(G.nodes),
            'edge_count': len(G.edges),
            'title': title
        }
    
    def _get_function_calls(self, function_name: str, max_depth: int) -> Dict[str, Dict[str, Dict]]:
        """Get function call relationships (simulated for now)"""
        # In a real implementation, this would query the RAG system
        # For now, return simulated data
        return {
            function_name: {
                'helper_function': {'file': 'utils.py'},
                'process_data': {'file': 'data_processor.py'},
                'validate_input': {'file': 'validator.py'}
            },
            'helper_function': {
                'format_output': {'file': 'formatter.py'},
                'log_activity': {'file': 'logger.py'}
            },
            'process_data': {
                'transform_data': {'file': 'transformer.py'},
                'save_results': {'file': 'storage.py'}
            }
        }
    
    def _get_class_inheritance(self, base_class: str, max_depth: int) -> Dict[str, Dict[str, Dict]]:
        """Get class inheritance relationships (simulated for now)"""
        return {
            base_class: {
                'ConcreteClass1': {'file': 'concrete1.py'},
                'ConcreteClass2': {'file': 'concrete2.py'},
                'AbstractClass': {'file': 'abstract.py'}
            },
            'AbstractClass': {
                'SpecializedClass': {'file': 'specialized.py'},
                'UtilityClass': {'file': 'utility.py'}
            }
        }
    
    def _get_file_dependencies(self, file_path: str, max_depth: int) -> Dict[str, Dict[str, str]]:
        """Get file dependency relationships (simulated for now)"""
        return {
            file_path: {
                'numpy': 'external',
                'pandas': 'external',
                'utils.py': 'internal',
                'config.py': 'internal'
            },
            'utils.py': {
                'os': 'standard',
                'sys': 'standard',
                'helpers.py': 'internal'
            }
        }
    
    def _get_codebase_structure(self, max_nodes: int) -> List[Dict[str, Any]]:
        """Get codebase structure (simulated for now)"""
        return [
            {
                'file': 'main.py',
                'type': 'python',
                'functions': ['main', 'setup', 'teardown'],
                'classes': ['MainController'],
                'imports': ['utils', 'config']
            },
            {
                'file': 'utils.py',
                'type': 'python',
                'functions': ['helper_function', 'format_data'],
                'classes': ['UtilityClass'],
                'imports': ['os', 'sys']
            },
            {
                'file': 'config.py',
                'type': 'python',
                'functions': ['load_config', 'validate_config'],
                'classes': ['ConfigManager'],
                'imports': ['json', 'pathlib']
            },
            {
                'file': 'models.py',
                'type': 'python',
                'functions': ['create_model', 'train_model'],
                'classes': ['BaseModel', 'NeuralNetwork'],
                'imports': ['torch', 'numpy']
            }
        ]
    
    def create_interactive_graph_ui(self):
        """Create the interactive graph visualization UI"""
        
        st.header("🔗 Advanced Code Graph Visualization")
        st.markdown("Visualize code relationships, function calls, class inheritance, and dependencies.")
        
        # Graph type selection
        graph_type = st.selectbox(
            "Select Graph Type",
            ["Function Call Graph", "Class Inheritance Tree", "Dependency Graph", "Codebase Overview"],
            help="Choose the type of code relationship to visualize"
        )
        
        # Graph parameters
        col1, col2 = st.columns(2)
        
        with col1:
            max_depth = st.slider("Max Depth", 1, 5, 3, help="Maximum depth for relationship traversal")
        
        with col2:
            max_nodes = st.slider("Max Nodes", 10, 100, 50, help="Maximum number of nodes to display")
        
        # Input parameters based on graph type
        if graph_type == "Function Call Graph":
            function_name = st.text_input("Function Name", "main", help="Enter the function name to analyze")
            if st.button("Generate Function Call Graph"):
                with st.spinner("Generating function call graph..."):
                    graph_data = self.create_function_call_graph(function_name, max_depth)
                    self._display_graph(graph_data)
        
        elif graph_type == "Class Inheritance Tree":
            base_class = st.text_input("Base Class Name", "BaseClass", help="Enter the base class name")
            if st.button("Generate Inheritance Tree"):
                with st.spinner("Generating class inheritance tree..."):
                    graph_data = self.create_class_inheritance_tree(base_class, max_depth)
                    self._display_graph(graph_data)
        
        elif graph_type == "Dependency Graph":
            file_path = st.text_input("File Path", "main.py", help="Enter the file path to analyze")
            if st.button("Generate Dependency Graph"):
                with st.spinner("Generating dependency graph..."):
                    graph_data = self.create_dependency_graph(file_path, max_depth)
                    self._display_graph(graph_data)
        
        elif graph_type == "Codebase Overview":
            if st.button("Generate Codebase Overview"):
                with st.spinner("Generating codebase overview..."):
                    graph_data = self.create_codebase_overview_graph(max_nodes)
                    self._display_graph(graph_data)
    
    def _display_graph(self, graph_data: Dict[str, Any]):
        """Display the graph visualization"""
        
        # Display graph statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nodes", graph_data['node_count'])
        
        with col2:
            st.metric("Edges", graph_data['edge_count'])
        
        with col3:
            st.metric("Graph Type", graph_data['title'])
        
        # Display the interactive graph
        st.plotly_chart(graph_data['figure'], use_container_width=True)
        
        # Graph controls
        with st.expander("Graph Controls"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔍 Zoom In"):
                    st.info("Use mouse wheel or pinch gestures to zoom in")
            
            with col2:
                if st.button("🔍 Zoom Out"):
                    st.info("Use mouse wheel or pinch gestures to zoom out")
            
            with col3:
                if st.button("🔄 Reset View"):
                    st.info("Double-click to reset the view")
        
        # Graph information
        with st.expander("Graph Information"):
            st.markdown(f"**Title:** {graph_data['title']}")
            st.markdown(f"**Nodes:** {graph_data['node_count']}")
            st.markdown(f"**Edges:** {graph_data['edge_count']}")
            st.markdown("**Legend:**")
            st.markdown("- 🔵 Blue: Functions")
            st.markdown("- 🟠 Orange: Classes")
            st.markdown("- 🟢 Green: Files")
            st.markdown("- 🔴 Red: Dependencies")
    
    def create_cross_reference_query_ui(self):
        """Create UI for cross-reference queries"""
        
        st.header("🔍 Cross-Reference Query Interface")
        st.markdown("Query code relationships and visualize the results.")
        
        # Query input
        query = st.text_input(
            "Enter your query",
            placeholder="e.g., 'Where is main() used?' or 'Show me all subclasses of BaseClass'",
            help="Ask about function usage, class inheritance, or dependencies"
        )
        
        if st.button("🔍 Search Cross-References"):
            if query:
                with st.spinner("Searching cross-references..."):
                    # In a real implementation, this would use the query system
                    results = self._simulate_cross_reference_query(query)
                    self._display_cross_reference_results(query, results)
            else:
                st.warning("Please enter a query")
    
    def _simulate_cross_reference_query(self, query: str) -> Dict[str, Any]:
        """Simulate cross-reference query results"""
        query_lower = query.lower()
        
        if "where is" in query_lower and "used" in query_lower:
            # Function usage query
            return {
                'type': 'function_usage',
                'target': 'main',
                'results': [
                    {'file': 'app.py', 'line': 15, 'context': 'main()'},
                    {'file': 'test_app.py', 'line': 25, 'context': 'main()'},
                    {'file': 'cli.py', 'line': 10, 'context': 'main()'}
                ]
            }
        elif "subclass" in query_lower:
            # Class inheritance query
            return {
                'type': 'class_inheritance',
                'target': 'BaseClass',
                'results': [
                    {'file': 'concrete1.py', 'class': 'ConcreteClass1', 'inherits': 'BaseClass'},
                    {'file': 'concrete2.py', 'class': 'ConcreteClass2', 'inherits': 'BaseClass'},
                    {'file': 'abstract.py', 'class': 'AbstractClass', 'inherits': 'BaseClass'}
                ]
            }
        else:
            return {
                'type': 'general',
                'results': []
            }
    
    def _display_cross_reference_results(self, query: str, results: Dict[str, Any]):
        """Display cross-reference query results"""
        
        st.subheader(f"Results for: '{query}'")
        
        if results['type'] == 'function_usage':
            st.markdown(f"**Function Usage:** {results['target']}")
            
            for result in results['results']:
                with st.expander(f"📄 {result['file']} (line {result['line']})"):
                    st.code(result['context'], language='python')
                    st.markdown(f"**File:** {result['file']}")
                    st.markdown(f"**Line:** {result['line']}")
        
        elif results['type'] == 'class_inheritance':
            st.markdown(f"**Class Inheritance:** {results['target']}")
            
            for result in results['results']:
                with st.expander(f"🏗️ {result['class']} in {result['file']}"):
                    st.markdown(f"**Class:** {result['class']}")
                    st.markdown(f"**Inherits from:** {result['inherits']}")
                    st.markdown(f"**File:** {result['file']}")
        
        else:
            st.info("No specific cross-reference results found. Try a more specific query.")
        
        # Option to visualize results
        if results['results']:
            if st.button("📊 Visualize Results"):
                if results['type'] == 'function_usage':
                    graph_data = self.create_function_call_graph(results['target'])
                elif results['type'] == 'class_inheritance':
                    graph_data = self.create_class_inheritance_tree(results['target'])
                else:
                    graph_data = self.create_codebase_overview_graph()
                
                self._display_graph(graph_data)


def main():
    """Main function for the graph visualization component"""
    
    st.set_page_config(
        page_title="Code Graph Visualization",
        page_icon="🔗",
        layout="wide"
    )
    
    st.title("🔗 Advanced Code Graph Visualization")
    st.markdown("Interactive visualization of code relationships, dependencies, and cross-references.")
    
    # Initialize the visualizer
    visualizer = CodeGraphVisualizer()
    
    # Create tabs for different visualization types
    tab1, tab2, tab3 = st.tabs(["📊 Graph Visualization", "🔍 Cross-Reference Queries", "📈 Analytics"])
    
    with tab1:
        visualizer.create_interactive_graph_ui()
    
    with tab2:
        visualizer.create_cross_reference_query_ui()
    
    with tab3:
        st.header("📈 Graph Analytics")
        st.markdown("Advanced analytics and insights from code relationships.")
        
        # Placeholder for analytics
        st.info("Graph analytics features coming soon!")
        
        # Sample analytics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Functions", "1,234")
        
        with col2:
            st.metric("Total Classes", "567")
        
        with col3:
            st.metric("Dependencies", "89")


if __name__ == "__main__":
    main() 