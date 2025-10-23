from tortoise import fields
from tortoise.models import Model


# 일기 게시글 모델
class Post(Model):
    id = fields.IntField(pk=True) # AI는 명시 안해도 자동 생성됨

    # 메타데이터
    title = fields.CharField(max_length=100)
    date = fields.DateField()

    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.User", related_name="posts")

    def __str__(self):
        return self.title