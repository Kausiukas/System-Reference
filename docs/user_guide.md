# User Guide

## Getting Started

### Installation

1. Follow the installation instructions in the [README](README.md)
2. Ensure all dependencies are installed
3. Configure your environment variables

### First Run

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Using the Application

### Uploading Documents

1. Click the "Upload Document" button in the sidebar
2. Select a supported file type:
   - Text files (.txt)
   - PDF documents (.pdf)
   - Word documents (.docx)
   - Markdown files (.md)
3. Click "Analyze Document" to start the analysis

### Understanding the Results

The analysis results are organized into four main tabs:

#### 1. Analysis Tab

- **Document Summary**: Overview of the business case
- **Key Parties**: Identified stakeholders and their roles
- **Situation Analysis**: Current business context
- **Problem Description**: Identified issues and challenges
- **Recommendations**: Actionable solutions

#### 2. Checklist Tab

- **Main Tasks**: High-level tasks derived from analysis
- **Subtasks**: Detailed steps for each main task
- **Dependencies**: Task relationships and prerequisites
- **Progress**: Completion status and tracking
- **Priorities**: Task importance levels

#### 3. Context Tab

- **Vector Store Context**: Relevant information from knowledge base
- **Web Search Context**: Additional insights from web search
- **Source References**: Links to original sources

#### 4. Metrics Tab

- **Performance Metrics**: Analysis speed and resource usage
- **Quality Metrics**: Analysis completeness and accuracy
- **Visualizations**: Charts and graphs of key metrics

### Working with Checklists

1. **View Tasks**:
   - Main tasks are listed with their priorities
   - Click to expand and view subtasks
   - Dependencies are shown with arrows

2. **Update Progress**:
   - Check boxes to mark tasks complete
   - Progress is automatically calculated
   - Dependencies are enforced

3. **Manage Priorities**:
   - High priority tasks are highlighted
   - Due dates are calculated based on priority
   - Dependencies affect task scheduling

### Using Metrics

1. **View Performance**:
   - Check analysis time and resource usage
   - Monitor quality scores
   - Track error rates

2. **Export Data**:
   - Download metrics as CSV
   - Export charts as images
   - Save reports as PDF

## Best Practices

### Document Preparation

1. **Format**:
   - Use clear, structured text
   - Include section headers
   - List key points with bullet points

2. **Content**:
   - Provide clear objectives
   - List all stakeholders
   - Include timeline and budget
   - Describe current situation
   - Outline specific problems

### Analysis Tips

1. **Context**:
   - Provide relevant background
   - Include industry context
   - Reference similar cases

2. **Stakeholders**:
   - List all involved parties
   - Specify roles and responsibilities
   - Include contact information

3. **Problems**:
   - Be specific about issues
   - Quantify impact where possible
   - Include root causes

## Troubleshooting

### Common Issues

1. **File Upload Errors**:
   - Check file format
   - Verify file size (max 10MB)
   - Ensure file is not corrupted

2. **Analysis Issues**:
   - Check internet connection
   - Verify API keys
   - Ensure sufficient resources

3. **Performance Problems**:
   - Close other applications
   - Check system resources
   - Reduce document size

### Getting Help

1. **Documentation**:
   - Check this user guide
   - Review API documentation
   - Read troubleshooting guide

2. **Support**:
   - Search existing issues
   - Create new issue
   - Contact support team

## Advanced Features

### Custom Analysis

1. **Prompt Templates**:
   - Modify analysis steps
   - Add custom criteria
   - Adjust evaluation metrics

2. **Integration**:
   - Connect with other tools
   - Export to project management
   - Sync with calendar

3. **Automation**:
   - Schedule regular analysis
   - Set up notifications
   - Configure auto-updates

### Data Management

1. **Storage**:
   - Configure local storage
   - Set up cloud backup
   - Manage document versions

2. **Security**:
   - Set access controls
   - Encrypt sensitive data
   - Audit access logs

3. **Backup**:
   - Schedule backups
   - Export data
   - Restore from backup 