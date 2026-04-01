# ranking.py
# ============================================================
# TF-IDF を使ったテキスト類似度検索ユーティリティ。
# 用途例：
#   - 事業案一覧のキーワード絞り込み
#   - 課題リストのクエリ検索
#   - 将来的なクローラー取得記事のランキング
# ============================================================

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def rank_by_query(query: str, documents: list[dict], text_key: str = "text", top_n: int = 5) -> list[dict]:
    """
    query に対して documents を TF-IDF コサイン類似度でランキングし、
    上位 top_n 件を similarity スコア付きで返す。

    Parameters
    ----------
    query : str
        検索クエリ
    documents : list[dict]
        テキストフィールドを持つ辞書のリスト
    text_key : str
        documents の各要素でテキストとして使うキー名
    top_n : int
        返す件数の上限

    Returns
    -------
    list[dict]
        元の辞書に "similarity" キーを追加してスコア降順で返す
    """
    if not documents:
        return []

    texts = [doc.get(text_key, "") for doc in documents]
    corpus = [query] + texts

    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        # query（index 0）と各 document（index 1〜）のコサイン類似度
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    except Exception as e:
        print(f"[ranking] TF-IDF計算エラー: {e}")
        return documents[:top_n]

    ranked = []
    for doc, score in zip(documents, scores):
        item = dict(doc)
        item["similarity"] = round(float(score), 4)
        ranked.append(item)

    ranked.sort(key=lambda x: x["similarity"], reverse=True)
    return ranked[:top_n]


def deduplicate(documents: list[dict], text_key: str = "text", threshold: float = 0.85) -> list[dict]:
    """
    コサイン類似度が threshold 以上のドキュメントを重複とみなして除去する。
    既存リスト + 追加リストの結合後に呼ぶことを想定。

    Parameters
    ----------
    documents : list[dict]
        重複チェック対象のリスト（順番が前のものを優先して残す）
    text_key : str
        テキストフィールドのキー名
    threshold : float
        この値以上を重複とみなす（0.0〜1.0）

    Returns
    -------
    list[dict]
        重複を除いたリスト
    """
    if len(documents) <= 1:
        return documents

    texts = [doc.get(text_key, "") for doc in documents]
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)
    except Exception as e:
        print(f"[ranking] dedup TF-IDF計算エラー: {e}")
        return documents

    keep = []
    dropped = set()
    for i in range(len(documents)):
        if i in dropped:
            continue
        keep.append(documents[i])
        for j in range(i + 1, len(documents)):
            if sim_matrix[i][j] >= threshold:
                dropped.add(j)

    return keep