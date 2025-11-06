"""
DSPy module for extracting themes from survey responses
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import dspy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure DSPy with OpenAI
lm = dspy.LM('openai/gpt-4o-mini', api_key=os.getenv('OPENAI_API_KEY'))
dspy.configure(lm=lm)

class ThemeExtractor(dspy.Signature):
    """Extract key themes from a survey response.
    
    Themes should be concise 1-3 word concepts that capture the main topics 
    discussed in the response. Focus on actionable categories like:
    - Product features (UI, performance, integrations)
    - User concerns (pricing, support, documentation)
    - Sentiment indicators (positive, negative, neutral aspects)
    """
    
    response_text = dspy.InputField(desc="The survey response text to analyze")
    themes = dspy.OutputField(desc="List of 2-5 theme keywords extracted from the response")

class ThemeExtractorModule:
    def __init__(self):
        self.predictor = dspy.ChainOfThought(ThemeExtractor)
    
    def extract(self, response_text):
        """Extract themes from a single response"""
        if not response_text or response_text.strip() == '':
            return []
        
        result = self.predictor(response_text=response_text)
        
        # Parse themes (handle various formats)
        themes_str = result.themes
        
        # Try to extract list from string
        if isinstance(themes_str, str):
            # Remove brackets, quotes, and split
            themes_str = themes_str.strip('[]()').replace('"', '').replace("'", "")
            themes = [t.strip().lower() for t in themes_str.split(',')]
        else:
            themes = themes_str
        
        # Clean and normalize
        themes = [t.strip().lower() for t in themes if t.strip()]
        
        return themes[:5]  # Limit to top 5 themes

if __name__ == "__main__":
    # Test the extractor
    extractor = ThemeExtractorModule()
    
    test_responses = [
        "The user interface is really intuitive and clean. I love how easy it is to navigate between features.",
        "The pricing feels a bit high for small teams. Also, the mobile app could use some performance improvements.",
        "Customer support response times could be faster. Sometimes takes days to hear back."
    ]
    
    print("🧠 Testing DSPy Theme Extractor\n")
    
    for i, response in enumerate(test_responses, 1):
        print(f"Response {i}: {response[:60]}...")
        themes = extractor.extract(response)
        print(f"Themes: {themes}\n")
