"""utils.py"""
# 프로젝트에서 공통으로 사용하는 유틸리티 함수들

import os
import re

from stopwords import STOPWORDS

def normalize_text(text):
    """소문자로 변환하고 한글, 영어, 숫자를 제외한 문자를 제거한다."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9가-힣\s]", " ",text)

    return text

def tokenize(text):
    """문자열을 단어 리스트로 변환한다."""

    return text.split()


def remove_stopwords(words):
    """불용어를 제거한다."""

    return [word for word in words if word not in STOPWORDS]


def preprocess(text):
    """하나의 문자열을 전처리하여 단어 리스트를 반환한다."""

    text = normalize_text(text)

    words = tokenize(text)

    words = remove_stopwords(words)

    return words


def get_file_mtime(path):
    """파일의 마지막 수정 시간을 반환한다."""

    return os.path.getmtime(path)


def safe_filename(filename):
    """txt 파일명을 pkl 파일명으로 변환한다."""

    name = os.path.splitext(filename)[0]

    return name + ".pkl"