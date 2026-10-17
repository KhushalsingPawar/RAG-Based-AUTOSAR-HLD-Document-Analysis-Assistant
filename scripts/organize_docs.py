import shutil
import os

files = ['Architecture', 'implementation_plan', 'PRD', 'README_Documentation']
for f in files:
    src_md = f + '.md'
    src_txt = f + '_extracted.txt'
    if os.path.exists(src_md):
        shutil.copy(src_md, f'docs/word_originals/{f}.docx')
        if os.path.exists(src_txt):
            with open(src_txt, 'r', encoding='utf-8') as s:
                content = s.read()
            with open(src_md, 'w', encoding='utf-8') as d:
                d.write(content)
            with open(f'docs/{f}.md', 'w', encoding='utf-8') as d:
                d.write(content)
            os.remove(src_txt)

if os.path.exists('Project_Feature_guide.pdf'):
    shutil.copy('Project_Feature_guide.pdf', 'docs/Project_Feature_guide.pdf')

for temp_file in ['inspect_docs.py', 'extract_pdf.py', 'test_emb.py', 'Project_Feature_guide_extracted.txt']:
    if os.path.exists(temp_file):
        os.remove(temp_file)

print('Documentation organized successfully!')
