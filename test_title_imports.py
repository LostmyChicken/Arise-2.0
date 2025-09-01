#!/usr/bin/env python3
"""
Test title system imports
"""

def test_imports():
    """Test importing title system components"""
    try:
        print("Testing title system imports...")
        
        # Test TitleManager import
        from structure.title_system import TitleManager, TitleCategory, Title
        print("✅ TitleManager imported successfully")
        
        # Test title loading
        titles = TitleManager.TITLES
        print(f"✅ {len(titles)} titles loaded")
        
        # Test specific title
        novice_hunter = TitleManager.get_title_by_id('novice_hunter')
        if novice_hunter:
            print(f"✅ Sample title: {novice_hunter.get_display_name()}")
        
        # Test TitleCog import
        from commands.titles import TitleCog
        print("✅ TitleCog imported successfully")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()
