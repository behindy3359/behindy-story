"""
  -   
  : //
llmserver/prompts/prompt_manager.py
"""

from typing import Dict, Any
import os
import json
from pathlib import Path

ALLOWED_THEMES = ["", "", ""]

class PromptManager:
    """    -   """
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent
        self.story_prompts = self._load_story_prompts()
        self.validation_prompts = self._load_validation_prompts()
        self.evaluation_prompts = self._load_evaluation_prompts()
    
    def _load_story_prompts(self) -> Dict[str, str]:
        """   """
        try:
            openai_path = self.prompts_dir / "story_generation_openai.txt"
            claude_path = self.prompts_dir / "story_generation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_story_prompts()
    
    def _load_validation_prompts(self) -> Dict[str, str]:
        """JSON   """
        try:
            openai_path = self.prompts_dir / "json_validation_openai.txt"
            claude_path = self.prompts_dir / "json_validation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_validation_prompts()
    
    def _load_evaluation_prompts(self) -> Dict[str, str]:
        """   """
        try:
            openai_path = self.prompts_dir / "quality_evaluation_openai.txt"
            claude_path = self.prompts_dir / "quality_evaluation_claude.txt"
            
            return {
                "openai": self._read_prompt_file(openai_path),
                "claude": self._read_prompt_file(claude_path)
            }
        except Exception as e:
            return self._get_default_evaluation_prompts()
    
    def _read_prompt_file(self, file_path: Path) -> str:
        """  """
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        else:
            raise FileNotFoundError(f"  : {file_path}")
    
    def get_story_prompt(self, provider: str) -> str:
        """   """
        return self.story_prompts.get(provider, self.story_prompts.get("openai", ""))
    
    def get_validation_prompt(self, provider: str) -> str:
        """JSON   """
        return self.validation_prompts.get(provider, self.validation_prompts.get("openai", ""))
    
    def get_evaluation_prompt(self, provider: str) -> str:
        """   """
        return self.evaluation_prompts.get(provider, self.evaluation_prompts.get("openai", ""))
    
    def reload_prompts(self):
        """   """
        self.story_prompts = self._load_story_prompts()
        self.validation_prompts = self._load_validation_prompts()
        self.evaluation_prompts = self._load_evaluation_prompts()
    
    def create_user_prompt(self, context: Dict[str, Any], prompt_type: str = "generation") -> str:
        """   -   """
        if prompt_type == "generation":
            return self._create_generation_user_prompt(context)
        elif prompt_type == "continuation":
            return self._create_continuation_user_prompt(context)
        else:
            return ""
    
    def _create_generation_user_prompt(self, context: Dict[str, Any]) -> str:
        """    -  """
        station_name = context.get('station_name', '')
        line_number = context.get('line_number', 2)
        health = context.get('character_health', 80)
        sanity = context.get('character_sanity', 80)
        theme_preference = context.get('theme_preference')
        
        theme_constraint = f"""
 :  
-   3    : {', '.join(ALLOWED_THEMES)}
-     
"""
        
        theme_hint = ""
        if theme_preference and theme_preference in ALLOWED_THEMES:
            theme_hint = f"-  '{theme_preference}'  \n"
        
        return f"""  :

 ** **
- : {station_name}
- : {line_number}

 ** **
- : {health}/100
- : {sanity}/100

{theme_constraint}
{theme_hint}

** :**
- : ,  , ,  
- : , ,  ,    
- : , ,  ,   

{station_name}        JSON  ."""
    
    def _create_continuation_user_prompt(self, context: Dict[str, Any]) -> str:
        """    -   """
        station_name = context.get('station_name', '')
        line_number = context.get('line_number', 2)
        health = context.get('character_health', 80)
        sanity = context.get('character_sanity', 80)
        previous_choice = context.get('previous_choice', '')
        story_context = context.get('story_context', '')
        current_theme = context.get('theme', '')
        
        theme_consistency = f"""
 :  
-   '{current_theme}'  
-   
- {current_theme}   
"""
        
        return f"""  "{previous_choice}"    .

 :
- : {station_name} ({line_number})
-  :  {health}/100,  {sanity}/100
-  : {story_context or "  "}

{theme_consistency}

**  :**
- :    
- :     
- :     

JSON  :
{{
    "page_content": "   (150-250, {current_theme}  )",
    "options": [
        {{
            "content": " ",
            "effect": "health|sanity|none",
            "amount": -5~+5,
            "effect_preview": " "
        }}
    ],
    "is_last_page": false
}}"""
    
    
    def _get_default_story_prompts(self) -> Dict[str, str]:
        """   -  """
        return {
            "openai": f"""       .

 :  
-   3  : {', '.join(ALLOWED_THEMES)}
-     

  JSON  :
{{
    "story_title": "  (20 )",
    "page_content": "  (150-300)",
    "options": [
        {{
            "content": " ",
            "effect": "health|sanity|none",
            "amount": -10~+10,
            "effect_preview": " "
        }}
    ],
    "estimated_length": 5,
    "difficulty": "||",
    "theme": "{ALLOWED_THEMES[0]}|{ALLOWED_THEMES[1]}|{ALLOWED_THEMES[2]}",
    "station_name": "",
    "line_number": 
}}

 :
-  2-4,  -10~+10 
- theme      
-   
-     """,

            "claude": f"""     .

  : {', '.join(ALLOWED_THEMES)} .

JSON  :
{{
    "story_title": " ",
    "page_content": "  (150-300)",
    "options": [ ],
    "estimated_length": ,
    "difficulty": "||",
    "theme": "",
    "station_name": "",
    "line_number": 
}}

 :
-  2-4 
-     
-    
-   """
        }
    
    def _get_default_validation_prompts(self) -> Dict[str, str]:
        """   -   """
        return {
            "openai": f"""JSON    .

   .

  :  
- theme     : {', '.join(ALLOWED_THEMES)}
-     

 :
{{
    "is_valid": true/false,
    "errors": [" "],
    "fixed_json": null,
    "theme_valid": true/false
}}""",

            "claude": f"""JSON  .

   : {', '.join(ALLOWED_THEMES)} 

  JSON :
{{
    "is_valid": boolean,
    "errors": [""],
    "fixed_json": null,
    "theme_valid": boolean
}}"""
        }
    
    def _get_default_evaluation_prompts(self) -> Dict[str, str]:
        """   -   """
        return {
            "openai": f"""     .

6   ( 120):
1.  (20)
2.  (20)  
3.  (20)
4.   (20)
5.   (20)
6.    (20) -  ({', '.join(ALLOWED_THEMES)}) 

JSON :
{{
    "total_score": 85.5,
    "creativity": 18.0,
    "coherence": 17.5,
    "engagement": 16.0,
    "korean_quality": 19.0,
    "game_suitability": 15.0,
    "theme_consistency": 18.0,
    "feedback": " ",
    "passed": true,
    "theme_valid": true
}}

 : 70  +  """,

            "claude": f"""  .

6   (  ):
-  : {', '.join(ALLOWED_THEMES)}

JSON :
{{
    "total_score": ,
    "creativity": ,
    "coherence": ,
    "engagement": ,
    "korean_quality": ,
    "game_suitability": ,
    "theme_consistency": ,
    "feedback": "",
    "passed": boolean,
    "theme_valid": boolean
}}"""
        }
    
    @staticmethod
    def get_allowed_themes() -> list:
        """   """
        return ALLOWED_THEMES.copy()
    
    @staticmethod
    def is_theme_allowed(theme: str) -> bool:
        """   """
        return theme in ALLOWED_THEMES
    
    def validate_theme_in_content(self, content: str) -> Dict[str, Any]:
        """   """
        try:
            theme_keywords = {
                "": ["", "", "", "", ""],
                "": ["", "", "", "", ""],
                "": ["", "", "", "", ""]
            }
            
            detected_themes = []
            for theme, keywords in theme_keywords.items():
                if any(keyword in content for keyword in keywords):
                    detected_themes.append(theme)
            
            return {
                "detected_themes": detected_themes,
                "is_valid": len(detected_themes) > 0,
                "primary_theme": detected_themes[0] if detected_themes else None
            }
            
        except Exception as e:
            return {
                "detected_themes": [],
                "is_valid": False,
                "primary_theme": None,
                "error": str(e)
            }

_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """   """
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager