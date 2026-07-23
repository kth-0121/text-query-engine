# Text Query Engine

> A lightweight Boolean Query Search Engine implemented in Python.

---

# 🇰🇷 한국어

## 프로젝트 소개

Text Query Engine은 여러 개의 텍스트 문서를 빠르게 검색하기 위한 **Boolean Query 기반 검색 엔진**입니다.

매번 모든 문서를 순차적으로 검색하는 대신, 문서를 미리 전처리하여 **역색인(Inverted Index)** 을 생성한 후 이를 이용해 빠르게 검색합니다.

또한 변경된 문서만 다시 인덱싱하는 **증분 인덱싱(Incremental Indexing)** 을 지원하여 대량의 문서에서도 효율적으로 동작합니다.

---

## 주요 기능

- 여러 개의 텍스트 문서 인덱싱
- 증분 인덱싱(변경된 문서만 재인덱싱)
- Boolean Query 검색
  - AND (`&&`)
  - OR (`||`)
  - NOT (`!`)
  - 괄호 (`()`)
- 파일명, 라인 번호, 원본 문장 출력
- Stopword 제거
- 유지보수가 쉬운 모듈 구조

---

## 프로젝트 구조

```text
text-query-engine/
│
├── main.py              # 프로그램 시작점
├── build_index.py       # 인덱스 생성 및 업데이트
├── search.py            # Boolean Query 검색
├── indexer.py           # 역색인 생성
├── storage.py           # 데이터 저장/불러오기
├── utils.py             # 전처리 유틸리티
├── stopwords.py         # 불용어 목록
│
├── documents/           # 원본 문서
│
└── index/
    ├── master.pkl       # 전체 역색인
    ├── metadata.pkl     # 파일 메타데이터
    └── files/           # 문서별 인덱스
```

---

## 프로그램 동작 과정

### 1. 인덱싱

문서를 읽은 후 다음 과정을 수행합니다.

```text
문서 읽기
    │
    ▼
소문자 변환
    │
    ▼
특수문자 제거
    │
    ▼
토큰화(Tokenize)
    │
    ▼
불용어 제거
    │
    ▼
역색인 생성
    │
    ▼
PKL 파일 저장
```

---

### 2. 검색

사용자가 검색어를 입력하면

```
(apple || banana) && !orange
```

다음 과정을 수행합니다.

1. Query Tokenize
2. Boolean 연산 계산
3. 역색인 검색
4. 결과 출력

출력 예시

```text
book1.txt
(3) Apple is a fruit.

book2.txt
(15) Banana and apple are popular.
```

---

## 역색인(Inverted Index)

일반적인 문서는

```text
book1

apple banana

book2

banana orange
```

처럼 저장됩니다.

하지만 검색 엔진에서는

```text
apple
    → (book1, line 1)

banana
    → (book1, line 1)
    → (book2, line 1)

orange
    → (book2, line 1)
```

처럼 **단어 → 문서 위치** 형태로 저장합니다.

이를 **역색인(Inverted Index)** 이라고 하며 검색 속도를 크게 향상시킵니다.

---

## 증분 인덱싱

프로그램은 변경된 문서만 다시 인덱싱합니다.

예를 들어

```
book1.txt   변경 없음
book2.txt   수정됨
book3.txt   변경 없음
```

이라면

```
book2.txt
```

만 다시 인덱싱합니다.

이를 통해 불필요한 작업을 줄이고 실행 시간을 단축합니다.

---

## Boolean Query 지원

지원 연산자

| 연산자 | 설명 |
|---------|------|
| && | AND |
| \|\| | OR |
| ! | NOT |
| () | 괄호 |

예시

```
apple
```

```
apple && banana
```

```
apple || orange
```

```
apple && !banana
```

```
(apple || banana) && !orange
```

---

## 각 모듈 설명

### main.py

프로그램의 시작점입니다.

메뉴를 출력하고 각 기능을 실행합니다.

---

### build_index.py

documents 폴더를 검사하여

- 새 문서
- 수정된 문서
- 삭제된 문서

를 확인하고 인덱스를 갱신합니다.

---

### indexer.py

문서를 읽고

- 전처리
- 단어 빈도 계산
- 역색인 생성

을 수행합니다.

---

### search.py

Boolean Query를 계산하여

- 검색
- 결과 출력

을 담당합니다.

---

### storage.py

PKL 파일 저장 및 로드를 담당합니다.

---

### utils.py

프로젝트 전체에서 사용하는

- 전처리
- 토큰화
- 파일명 변환

등의 공통 함수를 제공합니다.

---

### stopwords.py

검색 성능 향상을 위해 불필요한 단어를 제거하는 Stopword 목록입니다.

---

## 실행 방법

인덱스 생성

```bash
python build_index.py
```

검색 실행

```bash
python search.py
```

또는

```bash
python main.py
```

---

## 향후 개선 예정

- Phrase Query
- Wildcard Search
- TF-IDF Ranking
- BM25 Ranking
- PDF 검색
- DOCX 검색
- 웹 인터페이스
- 멀티스레드 인덱싱

---

# 🇺🇸 English

## Overview

Text Query Engine is a lightweight Boolean Query Search Engine written in Python.

Instead of scanning every document for every search, the engine preprocesses documents once, builds an **Inverted Index**, and performs fast searches using indexed data.

It also supports **Incremental Indexing**, allowing only newly added or modified documents to be re-indexed.

---

## Features

- Index multiple text documents
- Incremental indexing
- Boolean Query search
  - AND (`&&`)
  - OR (`||`)
  - NOT (`!`)
  - Parentheses (`()`)
- Display filename, line number, and original sentence
- Stopword removal
- Modular project architecture

---

## Project Structure

```text
text-query-engine/
│
├── main.py
├── build_index.py
├── search.py
├── indexer.py
├── storage.py
├── utils.py
├── stopwords.py
│
├── documents/
│
└── index/
    ├── master.pkl
    ├── metadata.pkl
    └── files/
```

---

## Workflow

### Indexing

```text
Document
    │
    ▼
Normalize text
    │
    ▼
Tokenize
    │
    ▼
Remove stopwords
    │
    ▼
Build inverted index
    │
    ▼
Save document index
```

---

### Searching

Example query

```
(apple || banana) && !orange
```

The engine

1. Tokenizes the query
2. Evaluates Boolean operators
3. Searches the master index
4. Displays matching results

---

## Inverted Index

Instead of storing

```text
book1

apple banana

book2

banana orange
```

the engine stores

```text
apple
    → (book1, line 1)

banana
    → (book1, line 1)
    → (book2, line 1)

orange
    → (book2, line 1)
```

This structure enables much faster searching.

---

## Future Work

- Phrase Query
- Wildcard Search
- TF-IDF
- BM25
- PDF Search
- DOCX Search
- Web Interface
- Multi-threaded Indexing

---

## Author

Developed as a course project for learning Information Retrieval and Search Engine fundamentals.