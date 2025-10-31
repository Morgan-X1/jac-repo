"""
Code Context Graph (CCG) Builder
Constructs a graph of code relationships from parsed files
"""

import re
from collections import defaultdict
from typing import Dict, List, Set


class CodeContextGraph:
    """
    Represents relationships between code entities:
    - Functions calling other functions
    - Classes inheriting from other classes
    - Modules importing from other modules
    """
    
    def __init__(self):
        self.nodes = {}  # {entity_id: entity_data}
        self.edges = defaultdict(list)  # {from_id: [to_ids]}
        self.edge_types = {}  # {(from, to): type}
        self.file_entities = defaultdict(list)  # {file_path: [entity_ids]}
        
    def add_node(self, entity_id: str, entity_data: dict):
        """Add a code entity (function, class, etc.)"""
        self.nodes[entity_id] = entity_data
        file_path = entity_data.get('file_path', '')
        if file_path:
            self.file_entities[file_path].append(entity_id)
    
    def add_edge(self, from_id: str, to_id: str, edge_type: str):
        """Add a relationship between entities"""
        if from_id in self.nodes and to_id in self.nodes:
            self.edges[from_id].append(to_id)
            self.edge_types[(from_id, to_id)] = edge_type
    
    def get_stats(self) -> dict:
        """Get graph statistics"""
        return {
            'node_count': len(self.nodes),
            'edge_count': sum(len(edges) for edges in self.edges.values()),
            'file_count': len(self.file_entities),
            'avg_connections': sum(len(edges) for edges in self.edges.values()) / max(len(self.nodes), 1)
        }
    
    def get_entity(self, entity_id: str) -> dict:
        """Get entity data"""
        return self.nodes.get(entity_id, {})
    
    def get_callers(self, entity_id: str) -> List[str]:
        """Get all entities that call/reference this entity"""
        callers = []
        for from_id, to_ids in self.edges.items():
            if entity_id in to_ids:
                callers.append(from_id)
        return callers
    
    def get_callees(self, entity_id: str) -> List[str]:
        """Get all entities this entity calls/references"""
        return self.edges.get(entity_id, [])
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'nodes': self.nodes,
            'edges': dict(self.edges),
            'edge_types': {f"{k[0]}->{k[1]}": v for k, v in self.edge_types.items()},
            'stats': self.get_stats()
        }


def build_code_context_graph(parsed_files: List[dict]) -> dict:
    """
    Build Code Context Graph from parsed files
    
    Args:
        parsed_files: List of parsed file data from parser_engine
        
    Returns:
        Dictionary representation of the CCG
    """
    ccg = CodeContextGraph()
    
    # Pass 1: Add all entities as nodes
    for pfile in parsed_files:
        if pfile.get('error'):
            continue
            
        file_path = pfile.get('path', '')
        file_type = pfile.get('type', '')
        
        # Python files
        if file_type == 'python':
            # Add functions
            for func_name in pfile.get('funcs', []):
                entity_id = f"{file_path}::{func_name}"
                ccg.add_node(entity_id, {
                    'name': func_name,
                    'type': 'function',
                    'language': 'python',
                    'file_path': file_path
                })
            
            # Add classes
            for class_name in pfile.get('classes', []):
                entity_id = f"{file_path}::{class_name}"
                ccg.add_node(entity_id, {
                    'name': class_name,
                    'type': 'class',
                    'language': 'python',
                    'file_path': file_path
                })
        
        # Jac files
        elif file_type == 'jac':
            # Add nodes
            for node_name in pfile.get('nodes', []):
                entity_id = f"{file_path}::node:{node_name}"
                ccg.add_node(entity_id, {
                    'name': node_name,
                    'type': 'node',
                    'language': 'jac',
                    'file_path': file_path
                })
            
            # Add walkers
            for walker_name in pfile.get('walkers', []):
                entity_id = f"{file_path}::walker:{walker_name}"
                ccg.add_node(entity_id, {
                    'name': walker_name,
                    'type': 'walker',
                    'language': 'jac',
                    'file_path': file_path
                })
            
            # Add abilities
            for ability_name in pfile.get('abilities', []):
                entity_id = f"{file_path}::ability:{ability_name}"
                ccg.add_node(entity_id, {
                    'name': ability_name,
                    'type': 'ability',
                    'language': 'jac',
                    'file_path': file_path
                })
        
        # JavaScript files
        elif file_type == 'javascript':
            for func_name in pfile.get('funcs', []):
                entity_id = f"{file_path}::{func_name}"
                ccg.add_node(entity_id, {
                    'name': func_name,
                    'type': 'function',
                    'language': 'javascript',
                    'file_path': file_path
                })
            
            for class_name in pfile.get('classes', []):
                entity_id = f"{file_path}::{class_name}"
                ccg.add_node(entity_id, {
                    'name': class_name,
                    'type': 'class',
                    'language': 'javascript',
                    'file_path': file_path
                })
        
        # Rust files
        elif file_type == 'rust':
            for func_name in pfile.get('funcs', []):
                entity_id = f"{file_path}::{func_name}"
                ccg.add_node(entity_id, {
                    'name': func_name,
                    'type': 'function',
                    'language': 'rust',
                    'file_path': file_path
                })
            
            for struct_name in pfile.get('structs', []):
                entity_id = f"{file_path}::{struct_name}"
                ccg.add_node(entity_id, {
                    'name': struct_name,
                    'type': 'struct',
                    'language': 'rust',
                    'file_path': file_path
                })
    
    # Pass 2: Detect relationships (simplified - can be enhanced with AST analysis)
    # For now, we'll detect simple patterns in code content
    for pfile in parsed_files:
        if pfile.get('error') or 'content' not in pfile:
            continue
        
        file_path = pfile.get('path', '')
        content = pfile.get('content', '')
        
        # Get all entities in this file
        current_entities = ccg.file_entities.get(file_path, [])
        
        # Look for function calls (simple pattern matching)
        for entity_id in current_entities:
            entity = ccg.get_entity(entity_id)
            entity_name = entity.get('name', '')
            
            # Check if this entity is referenced in other files
            for other_file_path, other_entities in ccg.file_entities.items():
                if other_file_path == file_path:
                    continue
                
                # Read other file to check for references
                for other_entity_id in other_entities:
                    other_entity = ccg.get_entity(other_entity_id)
                    
                    # Simple heuristic: if entity name appears in content, assume call
                    # This is simplified - real implementation would use AST
                    if entity_name in content and len(entity_name) > 3:
                        ccg.add_edge(other_entity_id, entity_id, 'calls')
    
    return ccg.to_dict()


def generate_mermaid_diagram(ccg_dict: dict, max_nodes: int = 20) -> str:
    """
    Generate Mermaid diagram from CCG
    
    Args:
        ccg_dict: CCG dictionary from build_code_context_graph
        max_nodes: Maximum nodes to include (to avoid overwhelming diagrams)
        
    Returns:
        Mermaid diagram string
    """
    nodes = ccg_dict.get('nodes', {})
    edges = ccg_dict.get('edges', {})
    
    # Limit to most connected nodes
    node_connections = {node_id: len(edges.get(node_id, [])) for node_id in nodes}
    top_nodes = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
    top_node_ids = {node_id for node_id, _ in top_nodes}
    
    # Build Mermaid syntax
    mermaid = "graph TD\n"
    
    # Add nodes with styling
    for node_id in top_node_ids:
        node_data = nodes[node_id]
        name = node_data.get('name', node_id)
        node_type = node_data.get('type', 'unknown')
        
        # Clean node_id for Mermaid (remove special chars)
        clean_id = node_id.replace('::', '_').replace(':', '_').replace('/', '_').replace('.', '_')
        
        # Style based on type
        if node_type == 'class':
            mermaid += f'    {clean_id}["{name}\\n(class)"]\n'
            mermaid += f'    style {clean_id} fill:#e1f5ff,stroke:#01579b\n'
        elif node_type in ['node', 'walker']:
            mermaid += f'    {clean_id}{{"{name}\\n({node_type})"}}\n'
            mermaid += f'    style {clean_id} fill:#fff3e0,stroke:#e65100\n'
        else:
            mermaid += f'    {clean_id}("{name}\\n({node_type})")\n'
            mermaid += f'    style {clean_id} fill:#f3e5f5,stroke:#4a148c\n'
    
    # Add edges
    added_edges = set()
    for from_id in top_node_ids:
        to_ids = edges.get(from_id, [])
        for to_id in to_ids:
            if to_id in top_node_ids and (from_id, to_id) not in added_edges:
                clean_from = from_id.replace('::', '_').replace(':', '_').replace('/', '_').replace('.', '_')
                clean_to = to_id.replace('::', '_').replace(':', '_').replace('/', '_').replace('.', '_')
                mermaid += f'    {clean_from} --> {clean_to}\n'
                added_edges.add((from_id, to_id))
    
    return mermaid


def query_ccg(ccg_dict: dict, query_type: str, entity_name: str) -> dict:
    """
    Query the CCG for specific relationships
    
    Args:
        ccg_dict: CCG dictionary
        query_type: 'callers', 'callees', 'info'
        entity_name: Name of entity to query
        
    Returns:
        Query results
    """
    nodes = ccg_dict.get('nodes', {})
    edges = ccg_dict.get('edges', {})
    
    # Find entity by name
    matching_entities = [
        (eid, data) for eid, data in nodes.items() 
        if data.get('name') == entity_name
    ]
    
    if not matching_entities:
        return {'error': f'Entity "{entity_name}" not found'}
    
    results = []
    for entity_id, entity_data in matching_entities:
        if query_type == 'info':
            results.append(entity_data)
        
        elif query_type == 'callees':
            callees = edges.get(entity_id, [])
            callee_data = [nodes.get(cid) for cid in callees if cid in nodes]
            results.append({
                'entity': entity_data,
                'calls': callee_data
            })
        
        elif query_type == 'callers':
            callers = []
            for from_id, to_ids in edges.items():
                if entity_id in to_ids:
                    callers.append(nodes.get(from_id))
            results.append({
                'entity': entity_data,
                'called_by': callers
            })
    
    return {'results': results}


if __name__ == "__main__":
    # Example usage
    sample_parsed_files = [
        {
            'path': 'main.py',
            'type': 'python',
            'funcs': ['main', 'init_app', 'run_server'],
            'classes': ['Application']
        },
        {
            'path': 'models.py',
            'type': 'python',
            'funcs': ['load_model', 'save_model'],
            'classes': ['Model', 'Dataset']
        }
    ]
    
    ccg = build_code_context_graph(sample_parsed_files)
    print("CCG Stats:", ccg['stats'])
    print("\nMermaid Diagram:")
    print(generate_mermaid_diagram(ccg))