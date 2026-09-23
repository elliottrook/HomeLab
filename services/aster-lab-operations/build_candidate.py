#!/usr/bin/env python3
"""Apply only lab integration hooks to a saved live gateway, preserving other work."""
import argparse
import ast
import hashlib
from pathlib import Path


def patch(source, template):
    if 'from lab_operations import' in source:
        raise ValueError('Live source already has lab integration; review instead of overwriting')
    if 'import hashlib\n' not in source:
        source = source.replace('import json\n', 'import json\nimport hashlib\n', 1)
    source = source.replace('from arr_report import', 'from lab_operations import LabOperations, OWNER as LAB_OWNER\n\nfrom arr_report import', 1)
    start = template.index('lab_operations = LabOperations()')
    end = template.index('\n\nclass ChatRequest', start)
    anchor = 'app = FastAPI(title="Aster Agent", version="1.0.0")'
    if source.count(anchor) != 1:
        raise ValueError('Unexpected gateway initialization')
    source = source.replace(anchor, anchor + '\n' + template[start:end], 1)
    start = template.index('# Execution tools are consumed')
    end = template.index('PERSONAS: dict[', start)
    if source.count('PERSONAS: dict[') != 1:
        raise ValueError('Unexpected persona registry')
    source = source.replace('PERSONAS: dict[', template[start:end] + 'PERSONAS: dict[', 1)
    start = template.index('    lab_response = lab_operations.chat(')
    end = template.index('    selected_tools = select_tools', start)
    anchor = '    selected_tools = select_tools(request.messages, allowed_tools)'
    if source.count(anchor) != 1:
        raise ValueError('Unexpected chat dispatch')
    source = source.replace(anchor, template[start:end] + anchor, 1)
    start = template.index('    if request.persona == "sysadmin" and lab_operations.enabled:')
    end = template.index('    read_only_context = await', start)
    anchor = '    read_only_context = await preload_read_only_context(request.messages, selected_tools)'
    if source.count(anchor) != 1:
        raise ValueError('Unexpected context preload')
    source = source.replace(anchor, template[start:end] + anchor, 1)
    ast.parse(source)
    return source


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('live',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    source=args.live.read_text()
    template=(Path(__file__).resolve().parents[1]/'aster-agent/aster_agent.py').read_text()
    candidate=patch(source,template)
    args.output.write_text(candidate)
    print('Expected live SHA256:', hashlib.sha256(source.encode()).hexdigest())
    print('Candidate SHA256:', hashlib.sha256(candidate.encode()).hexdigest())


if __name__ == '__main__': main()
