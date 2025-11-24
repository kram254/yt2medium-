import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

class DiagramGenerator:
    """
    Generate flowcharts, mind maps, and infographics from blog post content.
    Uses AI to create diagram specifications and renders them as images.
    """
    
    def __init__(self, ai_manager=None):
        self.ai_manager = ai_manager
        self.napkin_api_key = os.getenv('NAPKIN_API_KEY')
        
    def generate_flowchart_from_content(self, title, content, diagram_type='flowchart'):
        """
        Generate a flowchart or diagram based on blog post content.
        
        Args:
            title: Blog post title
            content: Blog post content (first 2000 chars for context)
            diagram_type: Type of diagram (flowchart, mindmap, process, infographic)
        
        Returns:
            dict with 'success', 'diagram_url', 'diagram_type', 'mermaid_code'
        """
        try:
            print(f"[DIAGRAM] Generating {diagram_type} for: {title[:50]}")
            
            # Step 1: Use AI to analyze content and generate diagram specification
            mermaid_code = self._generate_diagram_spec(title, content, diagram_type)
            
            if not mermaid_code:
                return {'success': False, 'error': 'Failed to generate diagram specification'}
            
            print(f"[DIAGRAM] Generated Mermaid code: {len(mermaid_code)} chars")
            
            # Step 2: Render Mermaid diagram to image
            diagram_url = self._render_mermaid_to_image(mermaid_code)
            
            if diagram_url:
                return {
                    'success': True,
                    'diagram_url': diagram_url,
                    'diagram_type': diagram_type,
                    'mermaid_code': mermaid_code
                }
            else:
                return {'success': False, 'error': 'Failed to render diagram'}
                
        except Exception as e:
            print(f"[DIAGRAM] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_diagram_spec(self, title, content, diagram_type):
        """
        Use AI to generate Mermaid diagram specification from content.
        """
        # Limit content to avoid token limits
        content_excerpt = content[:2000] if len(content) > 2000 else content
        
        prompt = self._get_diagram_prompt(title, content_excerpt, diagram_type)
        
        if not self.ai_manager:
            print("[DIAGRAM] No AI manager available")
            return None
        
        try:
            # Generate Mermaid code using AI
            mermaid_code = self.ai_manager.generate_content(prompt, None, 'gpt-4o')
            
            # Extract Mermaid code from response (remove markdown code blocks if present)
            mermaid_code = self._extract_mermaid_code(mermaid_code)
            
            return mermaid_code
        except Exception as e:
            print(f"[DIAGRAM] AI generation error: {e}")
            return None
    
    def _get_diagram_prompt(self, title, content, diagram_type):
        """
        Generate prompt for AI to create diagram specification.
        """
        if diagram_type == 'flowchart':
            return f"""Create a Mermaid flowchart diagram for this article:

Title: {title}
Content: {content}

Generate ONLY valid Mermaid.js flowchart syntax that visualizes:
- Main concepts and their relationships
- Process flows or decision points
- Key steps or stages mentioned in the content
- Logical connections between ideas

Requirements:
- Use flowchart syntax (graph TD or graph LR)
- Keep it clear and not overly complex (max 15 nodes)
- Use descriptive but concise node labels
- Show clear flow direction with arrows
- Output ONLY the Mermaid code, no explanations

Example format:
graph TD
    A[Start] --> B[Main Concept]
    B --> C[Key Point 1]
    B --> D[Key Point 2]
    C --> E[Outcome]
    D --> E
"""
        elif diagram_type == 'mindmap':
            return f"""Create a Mermaid mind map diagram for this article:

Title: {title}
Content: {content}

Generate ONLY valid Mermaid.js mindmap syntax that shows:
- Central topic in the center
- Main themes branching out
- Sub-topics and details
- Hierarchical relationships

Requirements:
- Use mindmap syntax
- Keep it organized (max 4 levels deep)
- Use clear, concise labels
- Output ONLY the Mermaid code, no explanations

Example format:
mindmap
  root((Central Topic))
    Main Theme 1
      Subtopic A
      Subtopic B
    Main Theme 2
      Subtopic C
      Subtopic D
"""
        elif diagram_type == 'process':
            return f"""Create a Mermaid process/sequence diagram for this article:

Title: {title}
Content: {content}

Generate ONLY valid Mermaid.js sequence or process diagram that shows:
- Sequential steps or stages
- Interactions between components
- Timeline or workflow
- Input/output relationships

Requirements:
- Use appropriate Mermaid syntax (sequenceDiagram or graph)
- Show clear progression
- Include key steps from the content
- Output ONLY the Mermaid code, no explanations

Example format:
sequenceDiagram
    participant A as Component A
    participant B as Component B
    A->>B: Action 1
    B->>A: Response
    A->>B: Action 2
"""
        else:  # infographic
            return f"""Create a Mermaid diagram for an infographic about this article:

Title: {title}
Content: {content}

Generate ONLY valid Mermaid.js graph syntax that visualizes:
- Key statistics or facts
- Important data points
- Main takeaways
- Visual hierarchy of information

Requirements:
- Use graph TD or LR syntax
- Include key numbers, stats, or facts from content
- Create visually distinct sections
- Output ONLY the Mermaid code, no explanations

Example format:
graph TD
    A[Title: Key Stats] --> B[Stat 1: 80%]
    A --> C[Stat 2: 5x Growth]
    A --> D[Stat 3: 1000+ Users]
"""
    
    def _extract_mermaid_code(self, response):
        """
        Extract Mermaid code from AI response, removing markdown code blocks.
        """
        if not response:
            return None
        
        # Remove markdown code blocks
        response = response.strip()
        if response.startswith('```mermaid'):
            response = response.replace('```mermaid', '').replace('```', '').strip()
        elif response.startswith('```'):
            response = response.replace('```', '').strip()
        
        return response
    
    def _render_mermaid_to_image(self, mermaid_code):
        """
        Render Mermaid diagram to image using mermaid.ink service.
        """
        try:
            # Encode Mermaid code to base64
            encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
            
            # Use mermaid.ink free service to render
            diagram_url = f"https://mermaid.ink/img/{encoded}"
            
            print(f"[DIAGRAM] Rendered diagram URL: {diagram_url[:80]}...")
            return diagram_url
            
        except Exception as e:
            print(f"[DIAGRAM] Render error: {e}")
            return None
    
    def generate_multiple_diagrams(self, title, content):
        """
        Generate multiple diagram types for a blog post.
        Returns a list of diagram results.
        """
        diagram_types = ['flowchart', 'mindmap', 'process']
        results = []
        
        for dtype in diagram_types:
            result = self.generate_flowchart_from_content(title, content, dtype)
            if result.get('success'):
                results.append(result)
        
        return results


def get_diagram_generator(ai_manager=None):
    """
    Factory function to get DiagramGenerator instance.
    """
    return DiagramGenerator(ai_manager)
