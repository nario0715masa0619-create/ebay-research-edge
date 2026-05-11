with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# except ブロックを修正
old_except = '''            except Exception as e:
                print(f"[ERROR] Error: {e}")'''

new_except = '''            except Exception as e:
                import traceback
                print(f"[ERROR] Error: {e}")
                traceback.print_exc()'''

content = content.replace(old_except, new_except)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ except ブロックを修正しました')
