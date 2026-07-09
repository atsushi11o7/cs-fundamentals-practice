"""
schema_example.py — データモデリングの構造を Python で表した最小例

DBは使わず、テーブル設計（エンティティ・リレーション）を dataclass で表現する。
「1対多は多側に外部キー」「多対多は中間テーブル」を構造で示すのが目的。
"""
from dataclasses import dataclass, field


@dataclass
class User:
    id: int
    name: str
    email: str


@dataclass
class Article:
    id: int
    user_id: int          # 1対多：どのユーザーの記事か（外部キー相当）
    title: str
    body: str


@dataclass
class Tag:
    id: int
    name: str


@dataclass
class ArticleTag:
    """多対多の中間テーブル相当。記事とタグのペアを持つ。"""
    article_id: int
    tag_id: int


class BlogData:
    """各テーブルをリストで保持し、リレーションをたどる例。"""

    def __init__(self):
        self.users = []
        self.articles = []
        self.tags = []
        self.article_tags = []

    def articles_of_user(self, user_id):
        """1対多をたどる：あるユーザーの記事一覧。"""
        return [a for a in self.articles if a.user_id == user_id]

    def tags_of_article(self, article_id):
        """多対多をたどる：ある記事に付いたタグ一覧。"""
        tag_ids = {
            at.tag_id for at in self.article_tags if at.article_id == article_id
        }
        return [t for t in self.tags if t.id in tag_ids]


if __name__ == "__main__":
    data = BlogData()
    data.users.append(User(1, "alice", "alice@example.com"))
    data.articles.append(Article(10, user_id=1, title="Hello", body="..."))
    data.articles.append(Article(11, user_id=1, title="World", body="..."))
    data.tags.append(Tag(100, "python"))
    data.tags.append(Tag(101, "db"))
    data.article_tags.append(ArticleTag(10, 100))
    data.article_tags.append(ArticleTag(10, 101))

    print([a.title for a in data.articles_of_user(1)])    # ['Hello', 'World']
    print([t.name for t in data.tags_of_article(10)])      # ['python', 'db']
