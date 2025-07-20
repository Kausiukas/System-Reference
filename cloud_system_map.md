# Cloud Repository Investigation System - Complete File Map

## 📁 **System Overview**

This document provides a complete map of all files in the **System-Reference** cloud repository investigation system, organized by functionality and purpose.

---

## 🏗️ **Core Application Files**

### **Main Application Entry Point**
- **`src/main.py`** - Primary Streamlit application entry point with session state management, configuration loading, UI rendering, and repository processing orchestration

### **UI Components**
- **`src/components/ui_components.py`** - Streamlit UI components including header, sidebar, repository input, processing status, analysis results, and AI chat interface
- **`src/components/repository_processor.py`** - Repository processing engine handling cloning, analysis, metadata extraction, and RAG index building

### **Utility Modules**
- **`src/utils/config.py`** - Configuration management for environment variables and Streamlit secrets
- **`src/utils/session.py`** - Session state management for real-time updates and data persistence
- **`src/utils/cache.py`** - Caching utilities optimized for Streamlit Cloud performance

---

## 📋 **Configuration Files**

### **Application Configuration**
- **`requirements.txt`** - Python dependencies optimized for Streamlit Cloud deployment
- **`.streamlit/config.toml`** - Streamlit configuration with theme, server settings, and performance options
- **`config_template.env`** - Environment variable template for local development
- **`env.example`** - Example environment configuration file

### **GitHub Auto-Update System**
- **`config/github_update_config.yaml`** - Configuration for automated GitHub repository update system
- **`scripts/github_auto_update.py`** - Python script implementing automated repository synchronization and release management

---

## 📚 **Documentation Files**

### **Primary Documentation**
- **`docs/README.md`** - Main system documentation with architecture overview, features, deployment guide, and technology stack
- **`docs/streamlit-cloud/deployment.md`** - Comprehensive Streamlit Cloud deployment guide with environment setup and troubleshooting

### **User Experience & Technical Planning**
- **`cloud_user_experience.md`** - User flow description for streamlined single UI screen experience
- **`technical_implementation_plan.md`** - Technical implementation details for real-time repository processing system

### **System Architecture Documentation**
- **`docs/architecture/system-overview.md`** - Detailed system architecture focusing on Streamlit Cloud deployment and external services integration
- **`docs/components/real-time-orchestrator.md`** - Component documentation for the orchestrator managing processing stages and progress tracking

### **Deployment & Integration**
- **`docs/deployment/cloud-deployment.md`** - Multi-cloud deployment guide refactored for Streamlit Cloud
- **`docs/deployment/automated-github-update.md`** - Documentation for automated GitHub repository update system
- **`docs/integration/external-resources.md`** - Instructions for connecting additional resources, databases, and tools

---

## 🔧 **Infrastructure & Deployment Files**

### **Docker Configuration (Legacy - For Reference)**
- **`docker/Dockerfile.streamlit-ui`** - Docker configuration for Streamlit UI (legacy)
- **`docker/Dockerfile.enhanced-rag`** - Docker configuration for enhanced RAG system (legacy)
- **`docker/Dockerfile.background-agents`** - Docker configuration for background agents (legacy)
- **`docker/Dockerfile.agent-coordinator`** - Docker configuration for agent coordinator (legacy)
- **`docker/Dockerfile.postgresql`** - Docker configuration for PostgreSQL (legacy)
- **`docker/docker-compose.yml`** - Docker Compose configuration (legacy)
- **`docker/build.sh`** - Docker build script (legacy)

### **Kubernetes Configuration (Legacy - For Reference)**
- **`k8s/namespace.yaml`** - Kubernetes namespace configuration (legacy)
- **`k8s/configmap.yaml`** - Kubernetes ConfigMap (legacy)
- **`k8s/secrets.yaml`** - Kubernetes Secrets configuration (legacy)
- **`k8s/persistent-volumes.yaml`** - Kubernetes persistent volumes (legacy)
- **`k8s/deployments.yaml`** - Kubernetes deployments (legacy)
- **`k8s/services.yaml`** - Kubernetes services (legacy)
- **`k8s/ingress.yaml`** - Kubernetes ingress configuration (legacy)
- **`k8s/hpas.yaml`** - Kubernetes Horizontal Pod Autoscalers (legacy)
- **`k8s/deploy.sh`** - Kubernetes deployment script (legacy)

### **Database Configuration**
- **`config/postgresql/schema.sql`** - PostgreSQL database schema
- **`config/postgresql/indexes.sql`** - PostgreSQL database indexes
- **`config/monitoring.yml`** - Monitoring configuration

---

## 🧪 **Testing & Validation Files**

### **Test Scripts**
- **`test_advanced_query_system.py`** - Advanced query system testing
- **`test_advanced_query_system_simple.py`** - Simplified advanced query testing
- **`test_character_narrative_system.py`** - Character narrative system testing
- **`test_connection_health.py`** - Connection health testing
- **`test_cross_reference_query.py`** - Cross-reference query testing
- **`test_database_connection.py`** - Database connection testing
- **`test_enhanced_memory_management.py`** - Enhanced memory management testing
- **`test_enhanced_rag_integration.py`** - Enhanced RAG integration testing
- **`test_enhanced_repository_upload.py`** - Enhanced repository upload testing
- **`test_graph_visualization.py`** - Graph visualization testing
- **`test_knowledge_update.py`** - Knowledge update testing
- **`test_postgresql_connection.py`** - PostgreSQL connection testing
- **`test_pynarrative_agent.py`** - PyNarrative agent testing
- **`test_repository_upload_system.py`** - Repository upload system testing
- **`test_working_features.py`** - Working features testing
- **`validate_ai_help_agent.py`** - AI help agent validation
- **`validate_system_readiness.py`** - System readiness validation

### **Test Suites**
- **`tests/test_edge_cases_and_integration.py`** - Edge cases and integration testing
- **`tests/test_knowledge_base_validation.py`** - Knowledge base validation testing
- **`tests/test_low_confidence_clarification.py`** - Low confidence clarification testing
- **`tests/test_performance_and_stress.py`** - Performance and stress testing
- **`tests/test_rag_system_edge_cases.py`** - RAG system edge cases testing
- **`tests/test_self_healing_effectiveness.py`** - Self-healing effectiveness testing

### **Stress Testing**
- **`memory_stress_test.py`** - Memory stress testing
- **`run_stress_test.py`** - Stress test runner
- **`run_stress_test_simple.py`** - Simplified stress test runner
- **`stress_test_config.yml`** - Stress test configuration

---

## 📊 **Analysis & Monitoring Files**

### **Performance Monitoring**
- **`performance_monitor.py`** - Performance monitoring utilities
- **`cloud_health_monitor.py`** - Cloud health monitoring
- **`background_agents_dashboard.py`** - Background agents dashboard
- **`background_agents_dashboard_ui.md`** - Background agents dashboard UI documentation

### **Memory Management**
- **`memory_management.md`** - Memory management documentation
- **`memory_management_component_map.md`** - Memory management component mapping
- **`memory_management_visualizations.md`** - Memory management visualizations
- **`test_enhanced_memory_management.py`** - Enhanced memory management testing

### **System Analysis**
- **`analyze_agents.py`** - Agent analysis utilities
- **`vectorstore_analysis/`** - Vector store analysis directory
- **`test_data/`** - Test data directory

---

## 🎯 **Specialized Components**

### **AI & RAG Systems**
- **`background_agents/ai_help/ai_help_agent.py`** - AI help agent implementation
- **`background_agents/ai_help/enhanced_rag_system.py`** - Enhanced RAG system
- **`background_agents/ai_help/advanced_query_system.py`** - Advanced query system
- **`background_agents/ai_help/character_narrative_system.py`** - Character narrative system
- **`background_agents/ai_help/pynarrative_agent.py`** - PyNarrative agent
- **`background_agents/ai_help/knowledge_base_validator.py`** - Knowledge base validator
- **`background_agents/ai_help/repository_upload_system.py`** - Repository upload system

### **Coordination & Management**
- **`background_agents/coordination/agent_coordinator.py`** - Agent coordinator
- **`background_agents/coordination/base_agent.py`** - Base agent class
- **`background_agents/coordination/shared_state.py`** - Shared state management
- **`background_agents/coordination/system_initializer.py`** - System initializer
- **`background_agents/coordination/postgresql_adapter.py`** - PostgreSQL adapter
- **`background_agents/coordination/self_healing_autopatch.py`** - Self-healing autopatch
- **`background_agents/coordination/shared_state_postgresql.py`** - PostgreSQL shared state
- **`background_agents/coordination/lifecycle_logger.py`** - Lifecycle logger

### **Monitoring & Health**
- **`background_agents/monitoring/agent_memory_interface.py`** - Agent memory interface
- **`background_agents/monitoring/enhanced_memory_manager.py`** - Enhanced memory manager
- **`background_agents/monitoring/enhanced_shared_state_monitor.py`** - Enhanced shared state monitor
- **`background_agents/monitoring/heartbeat_health_agent.py`** - Heartbeat health agent
- **`background_agents/monitoring/langsmith_bridge.py`** - LangSmith bridge
- **`background_agents/monitoring/memory_manager.py`** - Memory manager
- **`background_agents/monitoring/performance_monitor.py`** - Performance monitor
- **`background_agents/monitoring/self_healing_agent.py`** - Self-healing agent

---

## 🚀 **Launch & Setup Scripts**

### **System Launch**
- **`launch_background_agents.py`** - Background agents launcher
- **`launch_pynarrative_system.py`** - PyNarrative system launcher
- **`setup_postgresql_environment.py`** - PostgreSQL environment setup
- **`cloud_infrastructure_setup.py`** - Cloud infrastructure setup
- **`cloud_infrastructure_setup.md`** - Cloud infrastructure setup documentation

### **Automated Testing**
- **`run_automated_tests.py`** - Automated test runner
- **`run_final_test.py`** - Final test runner
- **`prepare_submission.py`** - Submission preparation script

---

## 📈 **Visualization & UI**

### **Graph Visualization**
- **`advanced_graph_visualization_app.py`** - Advanced graph visualization application
- **`src/components/graph_visualization.py`** - Graph visualization component
- **`src/api/streaming_api.py`** - Streaming API for real-time updates

### **Data Models & Services**
- **`src/models/`** - Data models directory
- **`src/services/`** - Services directory
- **`src/db/`** - Database utilities directory

---

## 📝 **Documentation & Reports**

### **System Documentation**
- **`ADVANCED_GRAPH_VISUALIZATION_DOCUMENTATION.md`** - Advanced graph visualization documentation
- **`ADVANCED_GRAPH_VISUALIZATION_SUMMARY.md`** - Advanced graph visualization summary
- **`ADVANCED_QUERY_SYSTEM_COMPLETION_SUMMARY.md`** - Advanced query system completion summary
- **`AI_CAPSTONE_PROJECT_PLAN.md`** - AI capstone project plan
- **`AI_HELP_AGENT_DOCUMENTATION_IMPROVEMENTS.md`** - AI help agent documentation improvements
- **`AI_HELP_AGENT_FINAL_TEST.md`** - AI help agent final test
- **`CHARACTER_NARRATIVE_SYSTEM_DOCUMENTATION.md`** - Character narrative system documentation
- **`CLOUD_DEPLOYMENT.md`** - Cloud deployment documentation
- **`CLOUD_INFRASTRUCTURE_FILE_MAP.md`** - Cloud infrastructure file map
- **`CODE_CROSS_REFERENCE.md`** - Code cross-reference documentation
- **`ENHANCED_CODE_ANALYSIS_README.md`** - Enhanced code analysis README
- **`ENHANCED_RAG_DOCUMENTATION_SUMMARY.md`** - Enhanced RAG documentation summary
- **`FINAL_TEST_INSTRUCTIONS.md`** - Final test instructions
- **`IMMEDIATE_DEPLOYMENT_GUIDE.md`** - Immediate deployment guide
- **`IMMEDIATE_DEVELOPMENT_TASKS_COMPLETED.md`** - Immediate development tasks completed
- **`KNOWLEDGE_BASE_AUDIT_AND_VALIDATION_PLAN.md`** - Knowledge base audit and validation plan
- **`LIVE_DATA_COLLECTION_STRATEGY.md`** - Live data collection strategy
- **`MEMORY_MANAGEMENT_DOCUMENTATION_SUMMARY.md`** - Memory management documentation summary
- **`MEMORY_MANAGEMENT_SYSTEM_STATUS.md`** - Memory management system status
- **`MEMORY_STRESS_TEST_DOCUMENTATION.md`** - Memory stress test documentation
- **`MIGRATION_SUMMARY.md`** - Migration summary
- **`PERFORMANCE_MONITORING.md`** - Performance monitoring documentation
- **`PHASE_2_COMPLETION_SUMMARY.md`** - Phase 2 completion summary
- **`PYNARRATIVE_IMPLEMENTATION_SUMMARY.md`** - PyNarrative implementation summary
- **`PYNARRATIVE_INTEGRATION_DOCUMENTATION.md`** - PyNarrative integration documentation
- **`RAG_ENHANCEMENT_GUIDE.md`** - RAG enhancement guide
- **`REPOSITORY_UPLOAD_SYSTEM_COMPLETION_SUMMARY.md`** - Repository upload system completion summary
- **`SELF_HEALING_METRICS.md`** - Self-healing metrics
- **`STAKEHOLDER_DEMONSTRATION_GUIDE.md`** - Stakeholder demonstration guide
- **`STRESS_TEST_RESULTS_SUMMARY.md`** - Stress test results summary
- **`STRESS_TEST_SYSTEM_SUMMARY.md`** - Stress test system summary

### **Development Notes**
- **`agents.md`** - Agents documentation
- **`AI_help.md`** - AI help documentation
- **`heartbeat_agent.md`** - Heartbeat agent documentation
- **`langsmith_bridge.md`** - LangSmith bridge documentation
- **`live_test.md`** - Live test documentation
- **`new_agent.md`** - New agent documentation
- **`recommendations.md`** - Recommendations
- **`requested_features.md`** - Requested features
- **`shared_state.md`** - Shared state documentation
- **`shared_state_database_psql.md`** - Shared state database PostgreSQL documentation
- **`testing_methodology.md`** - Testing methodology
- **`ui_data_mapping.md`** - UI data mapping
- **`unfinished.md`** - Unfinished tasks

---

## 🔄 **Legacy & Reference Files**

### **Legacy Applications**
- **`ai_help_agent_streamlit_fixed.py`** - Fixed Streamlit AI help agent (legacy)
- **`ai_help_agent_user_test.py`** - AI help agent user test (legacy)
- **`enhanced_repository_upload_system.py`** - Enhanced repository upload system (legacy)
- **`repository_upload_interface.py`** - Repository upload interface (legacy)

### **Debug & Development**
- **`debug_advanced_query.py`** - Advanced query debugging
- **`demo_character_narratives.py`** - Character narratives demo
- **`demo_pynarrative_capabilities.py`** - PyNarrative capabilities demo

### **Database & Infrastructure**
- **`fix_database_constraint.py`** - Database constraint fix
- **`fix_database_constraint.sql`** - Database constraint fix SQL
- **`sitecustomize.py`** - Site customization

---

## 📁 **Data & Storage Directories**

### **Vector Stores**
- **`vectorstore_db/`** - Vector database storage
- **`client_embeddings/`** - Client embeddings storage

### **Logs & Data**
- **`logs/`** - Application logs
- **`feedback_logs/`** - Feedback logs
- **`test_results/`** - Test results
- **`temp/`** - Temporary files

### **Submission**
- **`submission_avalci_AE35/`** - Submission package

---

## 🎯 **File Categories Summary**

| Category | File Count | Purpose |
|----------|------------|---------|
| **Core Application** | 6 | Main application files and components |
| **Configuration** | 5 | App configuration and environment setup |
| **Documentation** | 15+ | System documentation and guides |
| **Testing** | 20+ | Test scripts and validation |
| **Infrastructure** | 15+ | Deployment and infrastructure (legacy) |
| **AI & RAG** | 10+ | AI systems and RAG components |
| **Monitoring** | 10+ | Performance and health monitoring |
| **Utilities** | 10+ | Helper scripts and utilities |
| **Data** | 5+ | Data storage and logs |

---

## 🚀 **Quick Start Files**

For immediate deployment to Streamlit Cloud:

1. **`src/main.py`** - Main application
2. **`requirements.txt`** - Dependencies
3. **`.streamlit/config.toml`** - Streamlit configuration
4. **`docs/streamlit-cloud/deployment.md`** - Deployment guide
5. **`docs/README.md`** - System overview

---

## 📊 **System Architecture Overview**

```
📁 System-Reference/
├── 📁 src/                    # 🎯 Core Application
│   ├── 📄 main.py            # Main Streamlit app
│   ├── 📁 components/        # UI & Processing components
│   ├── 📁 utils/             # Utilities & Helpers
│   ├── 📁 api/               # API endpoints
│   ├── 📁 models/            # Data models
│   ├── 📁 services/          # Business logic
│   └── 📁 db/                # Database utilities
├── 📁 docs/                  # 📚 Documentation
│   ├── 📄 README.md          # Main documentation
│   ├── 📁 streamlit-cloud/   # Cloud deployment docs
│   ├── 📁 architecture/      # System architecture
│   ├── 📁 components/        # Component docs
│   └── 📁 deployment/        # Deployment guides
├── 📁 background_agents/     # 🤖 AI & Agent Systems
│   ├── 📁 ai_help/           # AI help components
│   ├── 📁 coordination/      # Agent coordination
│   └── 📁 monitoring/        # Health & monitoring
├── 📁 config/                # ⚙️ Configuration
├── 📁 scripts/               # 🔧 Automation scripts
├── 📁 tests/                 # 🧪 Testing
├── 📁 docker/                # 🐳 Legacy Docker configs
├── 📁 k8s/                   # ☸️ Legacy Kubernetes configs
└── 📁 vectorstore_db/        # 🗄️ Vector database storage
```

This system represents a comprehensive cloud-native repository investigation platform optimized for Streamlit Cloud deployment with real-time processing, AI-powered assistance, and scalable architecture. 