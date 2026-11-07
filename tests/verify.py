#!/usr/bin/env python3
"""
tests/verify.py - 하위 호환 프록시 어댑터
표준 기계 채점기는 tests/verify_code.py로 승격되었습니다.
"""
import runpy
from pathlib import Path

if __name__ == '__main__':
    target = Path(__file__).parent / 'verify_code.py'
    runpy.run_path(str(target), run_name='__main__')
