import os
import requests
import base64
import json
import subprocess
import time
import uuid
from pathlib import Path
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
        self.excalidraw_skill_path = Path('.agents/skills/excalidraw-diagram')
        self.has_excalidraw_skill = self.excalidraw_skill_path.exists()
        
        # Ensure static/diagrams exists
        self.diagrams_dir = Path('static/diagrams')
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_flowchart_from_content(self, title, content, diagram_type='flowchart', use_excalidraw=True):
        """
        Generate a flowchart or diagram based on blog post content.
        
        Args:
            title: Blog post title
            content: Blog post content (first 2000 chars for context)
            diagram_type: Type of diagram (flowchart, mindmap, process, infographic)
            use_excalidraw: Whether to prefer Excalidraw over Mermaid
        
        Returns:
            dict with 'success', 'diagram_url', 'diagram_type', 'mermaid_code', etc.
        """
        try:
            print(f"[DIAGRAM] Generating {diagram_type} for: {title[:50]}")
            
            # Use Excalidraw if requested and available
            if use_excalidraw and self.has_excalidraw_skill:
                return self._generate_excalidraw(title, content, diagram_type)
            
            # Fallback to Mermaid
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
                    'mermaid_code': mermaid_code,
                    'format': 'mermaid'
                }
            else:
                return {'success': False, 'error': 'Failed to render diagram'}
                
        except Exception as e:
            print(f"[DIAGRAM] Error: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_excalidraw(self, title, content, diagram_type):
        """
        Generate an Excalidraw diagram using the installed skill.
        """
        if not self.ai_manager:
            return {'success': False, 'error': 'AI manager required for Excalidraw generation'}
            
        print(f"[DIAGRAM] Using Excalidraw skill for {diagram_type}")
        
        # Generate a unique ID for this diagram
        diagram_id = str(uuid.uuid4())[:8]
        json_path = self.diagrams_dir / f"{diagram_id}.excalidraw"
        png_path = self.diagrams_dir / f"{diagram_id}.png"
        
        content_excerpt = content[:3000] if len(content) > 3000 else content
        
        # Read the templates to pass to the prompt
        try:
            templates_path = self.excalidraw_skill_path / 'references' / 'element-templates.md'
            colors_path = self.excalidraw_skill_path / 'references' / 'color-palette.md'
            
            templates = templates_path.read_text(encoding='utf-8') if templates_path.exists() else ""
            colors = colors_path.read_text(encoding='utf-8') if colors_path.exists() else ""
        except Exception as e:
            print(f"[DIAGRAM] Could not read Excalidraw templates: {e}")
            templates = ""
            colors = ""
            
        prompt = f"""
Create an Excalidraw diagram ({diagram_type}) for this article.

Title: {title}
Content: {content_excerpt}

Requirements:
1. You must output ONLY valid JSON matching the Excalidraw format.
2. The diagram should be professional, clean, and use the standard colors.
3. Keep the diagram concise and focused on the main concepts.
4. Do NOT wrap the JSON in ```json markdown blocks, just output the raw JSON directly.

Format required:
{{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [ ... your elements here ... ],
  "appState": {{ "viewBackgroundColor": "#ffffff", "gridSize": 20 }},
  "files": {{}}
}}

Use these standard colors if possible:
{colors[:500]}

Follow standard element structure. Make sure text fits within shapes, use proper x,y coordinates to space things out evenly.
"""

        try:
            # Generate JSON using AI
            print("[DIAGRAM] Requesting Excalidraw JSON from AI...")
            response = self.ai_manager.generate_content(prompt, None, 'gpt-4o')
            
            # Clean up the response to get valid JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response.replace('```json', '', 1)
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            # Parse to verify it's valid JSON
            try:
                excalidraw_json = json.loads(response)
                
                # Check required fields
                if "type" not in excalidraw_json or excalidraw_json["type"] != "excalidraw":
                    excalidraw_json["type"] = "excalidraw"
                if "version" not in excalidraw_json:
                    excalidraw_json["version"] = 2
                if "elements" not in excalidraw_json:
                    return {'success': False, 'error': 'Generated JSON missing elements array'}
                    
            except json.JSONDecodeError as e:
                print(f"[DIAGRAM] Failed to parse AI response as JSON: {e}")
                # Save the raw response for debugging
                debug_path = self.diagrams_dir / f"{diagram_id}_debug.txt"
                debug_path.write_text(response, encoding='utf-8')
                return {'success': False, 'error': 'AI did not return valid JSON'}
                
            # Write JSON to file
            json_path.write_text(json.dumps(excalidraw_json, indent=2), encoding='utf-8')
            print(f"[DIAGRAM] Saved Excalidraw JSON to {json_path}")
            
            # Render to PNG
            print("[DIAGRAM] Rendering Excalidraw to PNG...")
            render_script = self.excalidraw_skill_path / 'references' / 'render_excalidraw.py'
            
            # Path needs to be absolute or relative to the cwd of the script
            # Run the render script via subprocess
            # Uses 'uv run' as recommended in the skill docs
            cmd = ["uv", "run", "python", str(render_script), str(json_path.absolute()), "--output", str(png_path.absolute())]
            
            try:
                result = subprocess.run(
                    cmd, 
                    cwd=str(self.excalidraw_skill_path / 'references'),
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                
                if result.returncode != 0:
                    print(f"[DIAGRAM] Render script failed: {result.stderr}")
                    return {'success': False, 'error': f'Render script failed: {result.stderr}'}
                    
                print(f"[DIAGRAM] Render complete: {png_path}")
                
            except Exception as e:
                print(f"[DIAGRAM] Failed to run render script: {e}")
                return {'success': False, 'error': f'Failed to run render script: {str(e)}'}
            
            # Return URL to the generated image
            # Since it's in static/diagrams, the URL is /static/diagrams/...
            diagram_url = f"/static/diagrams/{png_path.name}"
            
            return {
                'success': True,
                'diagram_url': diagram_url,
                'download_url': f"/static/diagrams/{png_path.name}",  # Same for now, could be an attachment endpoint
                'excalidraw_json_url': f"/static/diagrams/{json_path.name}",
                'diagram_type': diagram_type,
                'format': 'excalidraw'
            }
            
        except Exception as e:
            print(f"[DIAGRAM] Excalidraw generation error: {e}")
            import traceback
            traceback.print_exc()
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
