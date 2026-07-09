"""
データモデリングの構造確認。
実行： uv run pytest 01_data_layer/data_modeling -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema_example import Article, ArticleTag, BlogData, Tag, User


def make_blog():
    data = BlogData()
    data.users.append(User(1, "alice", "alice@example.com"))
    data.users.append(User(2, "bob", "bob@example.com"))
    data.articles.append(Article(10, user_id=1, title="Hello", body="..."))
    data.articles.append(Article(11, user_id=1, title="World", body="..."))
    data.articles.append(Article(12, user_id=2, title="Other", body="..."))
    data.tags.append(Tag(100, "python"))
    data.tags.append(Tag(101, "db"))
    data.article_tags.append(ArticleTag(10, 100))
    data.article_tags.append(ArticleTag(10, 101))
    return data


def test_one_to_many_articles_of_user():
    data = make_blog()
    # 1対多：user 1 の記事だけを外部キー user_id でたどれる
    titles = [a.title for a in data.articles_of_user(1)]
    assert titles == ["Hello", "World"]


def test_one_to_many_isolates_other_user():
    data = make_blog()
    assert [a.title for a in data.articles_of_user(2)] == ["Other"]


def test_many_to_many_tags_of_article():
    data = make_blog()
    # 多対多：中間テーブル article_tags を介してタグをたどる
    names = [t.name for t in data.tags_of_article(10)]
    assert names == ["python", "db"]


def test_article_without_tags_returns_empty():
    data = make_blog()
    assert data.tags_of_article(11) == []
