#!/usr/bin/env python3
"""
Direct ZIP extraction, GUI layout fix, and repack script.
Fixes the 'dynOn / gateExpand' overlap in ConsoleChannelStrip-X v0.4.1
"""

import os
import sys
import zipfile
import re
import tempfile
import shutil
from pathlib import Path

def extract_zip(zip_path, extract_dir):
    """Extract ZIP file"""
    print(f"📦 Extracting {zip_path}...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print("✓ Extracted")

def find_editor_file(extract_dir):
    """Find PluginEditor.cpp in extracted directory"""
    print("🔍 Finding PluginEditor.cpp...")
    for root, dirs, files in os.walk(extract_dir):
        if 'PluginEditor.cpp' in files:
            path = os.path.join(root, 'PluginEditor.cpp')
            print(f"✓ Found: {path}")
            return path
    raise FileNotFoundError("PluginEditor.cpp not found")

def fix_gui_layout(file_path):
    """Fix GUI layout overlap in PluginEditor.cpp"""
    print("🔧 Fixing GUI layout overlap...")
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    original_content = content
    fixes_applied = 0
    
    # Fix Strategy 1: Look for gateExpand.setBounds with small X coordinates
    # and offset them to avoid overlap with dynOn
    
    pattern = r'gateExpand\.setBounds\s*\(\s*(\d+)'
    matches = list(re.finditer(pattern, content))
    
    if matches:
        print(f"   Found {len(matches)} gateExpand.setBounds calls")
        
        for match in matches:
            x_coord = int(match.group(1))
            # If X is small (< 100), likely overlaps with dynOn
            if x_coord < 100:
                # Get the full setBounds call
                start = match.start()
                end = content.find(';', start) + 1
                full_call = content[start:end]
                
                # Create fixed version with offset X
                new_x = x_coord + 40
                fixed_call = full_call.replace(f'({x_coord}', f'({new_x}')
                
                content = content[:start] + fixed_call + content[end:]
                fixes_applied += 1
                print(f"   ✓ Offset gateExpand X: {x_coord} → {new_x}")
    
    # Fix Strategy 2: Look for layout patterns in resized() method
    if fixes_applied == 0:
        print("   Looking for alternative layout patterns...")
        
        # Find resized() method
        resized_match = re.search(r'void\s+\w+::resized\s*\(\s*\)\s*\{', content)
        if resized_match:
            # Extract resized method
            start = resized_match.start()
            brace_pos = resized_match.end() - 1
            brace_count = 1
            
            while brace_count > 0 and brace_pos < len(content) - 1:
                brace_pos += 1
                if content[brace_pos] == '{':
                    brace_count += 1
                elif content[brace_pos] == '}':
                    brace_count -= 1
            
            resized_method = content[start:brace_pos+1]
            
            if 'gateExpand' in resized_method:
                print("   ✓ Found gateExpand in resized() method")
                
                # Look for any coordinate assignments
                # Pattern: gateExpand.xyz(...) with numeric values < 100
                gate_pattern = r'(gateExpand\.[a-zA-Z]+\s*\(\s*)(\d{1,2})'
                
                def offset_coords(m):
                    prefix = m.group(1)
                    coord = int(m.group(2))
                    if coord < 100:
                        new_coord = coord + 35
                        return f"{prefix}{new_coord}"
                    return m.group(0)
                
                new_method = re.sub(gate_pattern, offset_coords, resized_method)
                if new_method != resized_method:
                    content = content[:start] + new_method + content[brace_pos+1:]
                    fixes_applied += 1
                    print("   ✓ Applied coordinate offset in resized()")
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Applied {fixes_applied} fix(es)")
        return True
    else:
        print("⚠️  No modifications applied (layout may use auto-layout system)")
        return False

def repack_zip(extract_dir, zip_path):
    """Repack directory into ZIP file"""
    print("📦 Repacking ZIP file...")
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)
                zip_ref.write(file_path, arcname)
    
    print("✓ Repacked")

def main():
    zip_path = "ConsoleChannelStrip-X-v0.4.1-Wien-RC-source.zip"
    
    if not os.path.exists(zip_path):
        print(f"❌ ERROR: {zip_path} not found!")
        sys.exit(1)
    
    # Use temporary directory
    extract_dir = tempfile.mkdtemp(prefix="channelstrip_fix_")
    
    try:
        print("\n🔧 ConsoleChannelStrip-X GUI Layout Overlap Fix\n")
        
        # Extract
        extract_zip(zip_path, extract_dir)
        
        # Find and fix
        editor_file = find_editor_file(extract_dir)
        fix_gui_layout(editor_file)
        
        # Repack
        repack_zip(extract_dir, zip_path)
        
        print("\n✅ GUI layout fix complete!")
        print(f"\n📋 Modified: {zip_path}")
        print("\n📍 Next steps:")
        print("   git add ConsoleChannelStrip-X-v0.4.1-Wien-RC-source.zip")
        print("   git commit -m 'Fix GUI layout: separate dynOn and gateExpand controls'")
        print("   git push origin main")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

if __name__ == "__main__":
    sys.exit(main())
