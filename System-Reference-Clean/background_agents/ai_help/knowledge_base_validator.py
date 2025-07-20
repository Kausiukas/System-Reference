"""
Knowledge Base Validator for AI Help Agent

Validates and normalizes knowledge base data formats to ensure
compatibility with the Enhanced RAG system.
"""

import json
import logging
from typing import Dict, List, Any, Union, Optional
from datetime import datetime
import hashlib


class KnowledgeBaseValidator:
    """Validates and normalizes knowledge base data formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_stats = {
            'total_items_processed': 0,
            'items_converted': 0,
            'items_failed': 0,
            'validation_errors': []
        }
    
    def validate_knowledge_base(self, knowledge_base: Dict[str, Any]) -> Dict[str, str]:
        """
        Ensure knowledge base is Dict[str, str] format
        
        Args:
            knowledge_base: Input knowledge base with potentially mixed data types
            
        Returns:
            Dict[str, str]: Normalized knowledge base with all string values
            
        Raises:
            ValueError: If validation fails and strict mode is enabled
        """
        self.logger.info(f"Validating knowledge base with {len(knowledge_base)} items")
        
        validated_kb = {}
        
        for key, value in knowledge_base.items():
            try:
                validated_kb[key] = self.convert_to_string_format(value)
                self.validation_stats['items_converted'] += 1
            except Exception as e:
                error_msg = f"Failed to convert key '{key}': {e}"
                self.logger.warning(error_msg)
                self.validation_stats['validation_errors'].append(error_msg)
                self.validation_stats['items_failed'] += 1
                
                # Use a fallback string representation
                validated_kb[key] = f"[CONVERSION_ERROR: {str(value)[:100]}]"
            
            self.validation_stats['total_items_processed'] += 1
        
        self.logger.info(f"Knowledge base validation complete: "
                        f"{self.validation_stats['items_converted']} converted, "
                        f"{self.validation_stats['items_failed']} failed")
        
        return validated_kb
    
    def validate_codebase_analysis(self, codebase_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize codebase analysis data
        
        Args:
            codebase_analysis: Raw codebase analysis data
            
        Returns:
            Dict[str, Any]: Normalized codebase analysis with string metadata
        """
        self.logger.info("Validating codebase analysis data")
        
        validated_analysis = {
            'full_files': {},
            'key_files': [],
            'total_files': codebase_analysis.get('total_files', 0),
            'analysis_timestamp': codebase_analysis.get('analysis_timestamp', datetime.now().isoformat())
        }
        
        # Validate full_files
        for file_path, file_info in codebase_analysis.get('full_files', {}).items():
            validated_file_info = self._validate_file_info(file_info)
            validated_analysis['full_files'][file_path] = validated_file_info
        
        # Validate key_files
        for key_file in codebase_analysis.get('key_files', []):
            validated_key_file = self._validate_key_file(key_file)
            validated_analysis['key_files'].append(validated_key_file)
        
        self.logger.info(f"Codebase analysis validation complete: "
                        f"{len(validated_analysis['full_files'])} full files, "
                        f"{len(validated_analysis['key_files'])} key files")
        
        return validated_analysis
    
    def _validate_file_info(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual file information"""
        validated_info = {
            'content': str(file_info.get('content', '')),
            'language': str(file_info.get('language', 'unknown')),
            'functions': self._convert_list_to_string(file_info.get('functions', [])),
            'classes': self._convert_list_to_string(file_info.get('classes', [])),
            'imports': self._convert_list_to_string(file_info.get('imports', [])),
            'summary': str(file_info.get('summary', '')),
            'lines': str(file_info.get('lines', 0)),
            'file_size': str(file_info.get('file_size', 0)),
            'complexity': str(file_info.get('complexity', 'unknown'))
        }
        
        # Add any additional fields as strings
        for key, value in file_info.items():
            if key not in validated_info:
                validated_info[key] = self.convert_to_string_format(value)
        
        return validated_info
    
    def _validate_key_file(self, key_file: Dict[str, Any]) -> Dict[str, Any]:
        """Validate key file information"""
        validated_key_file = {
            'path': str(key_file.get('path', '')),
            'type': str(key_file.get('type', 'unknown')),
            'functions': self._convert_list_to_string(key_file.get('functions', [])),
            'classes': self._convert_list_to_string(key_file.get('classes', [])),
            'imports': self._convert_list_to_string(key_file.get('imports', [])),
            'summary': str(key_file.get('summary', '')),
            'importance': str(key_file.get('importance', 'medium'))
        }
        
        # Add any additional fields as strings
        for key, value in key_file.items():
            if key not in validated_key_file:
                validated_key_file[key] = self.convert_to_string_format(value)
        
        return validated_key_file
    
    def convert_to_string_format(self, data: Any) -> str:
        """
        Convert any data type to string format for indexing
        
        Args:
            data: Data to convert
            
        Returns:
            str: String representation of the data
        """
        if data is None:
            return ""
        
        if isinstance(data, str):
            return data
        
        if isinstance(data, bool):
            return "true" if data else "false"
        
        if isinstance(data, (int, float)):
            return str(data)
        
        if isinstance(data, list):
            return self._convert_list_to_string(data)
        
        if isinstance(data, dict):
            return self._convert_dict_to_string(data)
        
        if isinstance(data, datetime):
            return data.isoformat()
        
        # For any other type, try JSON serialization first
        try:
            return json.dumps(data, default=str)
        except (TypeError, ValueError):
            # Fallback to string representation
            return str(data)
    
    def _convert_list_to_string(self, data_list: List[Any]) -> str:
        """Convert list to comma-separated string"""
        if not data_list:
            return ""
        
        # Convert each item to string
        string_items = []
        for item in data_list:
            if item is not None:
                string_items.append(str(item))
        
        return ", ".join(string_items)
    
    def _convert_dict_to_string(self, data_dict: Dict[str, Any]) -> str:
        """Convert dict to JSON string"""
        try:
            return json.dumps(data_dict, default=str)
        except (TypeError, ValueError):
            # Fallback to simple key-value format
            items = []
            for key, value in data_dict.items():
                items.append(f"{key}: {str(value)}")
            return "; ".join(items)
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize metadata dictionary for ChromaDB
        Args:
            metadata: Raw metadata dictionary
        Returns:
            Dict[str, Any]: Normalized metadata with supported value types
        """
        validated_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                validated_metadata[str(key)] = value
            else:
                validated_metadata[str(key)] = str(value)
        return validated_metadata
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            **self.validation_stats,
            'success_rate': (
                self.validation_stats['items_converted'] / 
                max(self.validation_stats['total_items_processed'], 1)
            ) * 100
        }
    
    def reset_stats(self):
        """Reset validation statistics"""
        self.validation_stats = {
            'total_items_processed': 0,
            'items_converted': 0,
            'items_failed': 0,
            'validation_errors': []
        }
    
    def validate_conversation_memory(self, conversation_memory: Any) -> List[Dict[str, str]]:
        """
        Validate conversation memory data
        
        Args:
            conversation_memory: Conversation memory object or data
            
        Returns:
            List[Dict[str, str]]: Normalized conversation data
        """
        if not conversation_memory:
            return []
        
        validated_conversations = []
        
        # Handle different conversation memory formats
        if hasattr(conversation_memory, 'conversation_history'):
            conversations = conversation_memory.conversation_history
        elif isinstance(conversation_memory, list):
            conversations = conversation_memory
        else:
            self.logger.warning("Unknown conversation memory format")
            return []
        
        for i, exchange in enumerate(conversations):
            try:
                validated_exchange = {
                    'question': str(exchange.get('question', '')),
                    'response': str(exchange.get('response', '')),
                    'timestamp': str(exchange.get('timestamp', datetime.now().isoformat())),
                    'user_id': str(exchange.get('user_id', 'unknown')),
                    'session_id': str(exchange.get('session_id', f'session_{i}')),
                    'confidence': str(exchange.get('confidence', 0.0)),
                    'sources': self._convert_list_to_string(exchange.get('sources', []))
                }
                validated_conversations.append(validated_exchange)
            except Exception as e:
                self.logger.warning(f"Failed to validate conversation exchange {i}: {e}")
                continue
        
        return validated_conversations


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DataFormatError(ValidationError):
    """Exception for data format issues"""
    pass


class ConversionError(ValidationError):
    """Exception for data conversion issues"""
    pass 