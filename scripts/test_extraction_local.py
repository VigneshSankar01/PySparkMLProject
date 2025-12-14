import re


def clean_sec_filing(content):
    """Extract readable text from SEC XBRL/XML filings."""
    if not content:
        return None
    
    try:
        text = re.sub(r'<\?[^>]+\?>', '', content)
        text = re.sub(r'xmlns[^=]*="[^"]*"', '', text)
        text = re.sub(r'<[^>]+>', ' ', text)
        
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&quot;', '"')
        text = text.replace('&#8217;', "'")
        text = text.replace('&#8220;', '"')
        text = text.replace('&#8221;', '"')
        text = text.replace('&#160;', ' ')
        
        text = re.sub(r'&#\d+;', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text if len(text) > 5000 else None
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("Simple Extraction Test (No Spark)")
    print("=" * 60)
    
    print("\nLoading sample_filing.txt...")
    with open("sample_filing.txt", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    print(f"Raw file size: {len(content):,} characters")
    
    print("Extracting text...")
    clean_text = clean_sec_filing(content)
    
    if clean_text:
        print(f"Clean text size: {len(clean_text):,} characters")
        print(f"\nFirst 500 chars:\n{clean_text[:500]}")
        print("\n... SUCCESS! Extraction works.")
    else:
        print("ERROR: Extraction returned None")
    
    print("=" * 60)
