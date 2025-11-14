import sys
sys.path.append('.')
from src.dspy_modules.contradiction_detector import ContradictionGraphBuilder

builder = ContradictionGraphBuilder()

try:
    print("🧪 Testing Contradiction Detection Across Multiple Themes\n")
    print("=" * 80 + "\n")
    
    # Test multiple themes
    themes_to_test = [
        "positive sentiment",  # Mix of positive responses
        "user interface",      # Some like it, some want improvements
        "performance",         # Mix of good and bad
        "mobile app"          # Mix of issues
    ]
    
    total_contradictions = 0
    
    for theme in themes_to_test:
        print(f"\n{'='*80}")
        print(f"TESTING THEME: {theme}")
        print('='*80)
        
        count = builder.find_contradictions_for_theme(theme)
        total_contradictions += count
        
        print(f"\nFound {count} contradictions in '{theme}' theme")
    
    print("\n" + "="*80)
    print(f"\n📊 TOTAL CONTRADICTIONS ACROSS ALL THEMES: {total_contradictions}\n")
    
    if total_contradictions > 0:
        builder.get_contradiction_stats()
        builder.verify_contradictions()

finally:
    builder.close()
