"""image_model_changefield

Revision ID: 9fc6d2b70647
Revises: 65d66846d870
Create Date: 2026-08-23 18:38:40.752209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9fc6d2b70647'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 创建枚举类型（检查是否已存在）
    op.execute("CREATE TYPE category AS ENUM ('GALLERY', 'TRAVEL', 'NATURE', 'PORTRAIT', 'ARCHITECTURE', 'ABSTRACT')")

    # 2. 标准化 category 数据：统一转为大写（与 enum 值匹配）
    op.execute("UPDATE images SET category = UPPER(category) WHERE category != UPPER(category)")

    # 3. 添加 author_id 列（可空，便于后续迁移数据）
    op.add_column('images', sa.Column('author_id', sa.Integer(), nullable=True))

    # 4. 数据迁移：将 user_name 映射到 author_id
    op.execute("""
        UPDATE images SET author_id = users.id
        FROM users
        WHERE images.user_name = users.username
    """)

    # 5. 将 author_id 改为 NOT NULL
    op.alter_column('images', 'author_id', nullable=False)

    # 6. 创建索引
    op.create_index(op.f('ix_images_author_id'), 'images', ['author_id'], unique=False)

    # 7. 迁移 category 到 ENUM（数据已标准化为大写，与 enum 值匹配）
    op.alter_column('images', 'category',
                    existing_type=sa.VARCHAR(length=100),
                    type_=postgresql.ENUM('GALLERY', 'TRAVEL', 'NATURE', 'PORTRAIT', 'ARCHITECTURE', 'ABSTRACT', name='category', create_type=False),
                    postgresql_using="category::category")

    # 8. 迁移 tags 到 ARRAY
    op.alter_column('images', 'tags',
                    existing_type=sa.VARCHAR(length=500),
                    type_=postgresql.ARRAY(sa.String()),
                    postgresql_using="STRING_TO_ARRAY(COALESCE(tags, ''), ',')")

    # 9. 修改 created_at 为 NOT NULL（images）
    op.alter_column('images', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))

    # 10. 修改 created_at 为 NOT NULL（users）
    op.alter_column('users', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=False,
                    existing_server_default=sa.text('now()'))

    # 10.1. 修改 tags 为 NOT NULL（与模型保持一致）
    op.alter_column('images', 'tags',
                    existing_type=postgresql.ARRAY(sa.String()),
                    nullable=False)

    # 11. 删除旧索引和 FK
    op.drop_index(op.f('ix_images_created_at'), table_name='images')
    op.drop_index(op.f('ix_images_user_name'), table_name='images')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_constraint(op.f('images_user_name_fkey'), 'images', type_='foreignkey')

    # 12. 创建新 FK
    op.create_foreign_key(None, 'images', 'users', ['author_id'], ['id'])

    # 13. 删除 user_name 列
    op.drop_column('images', 'user_name')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 添加 user_name 列
    op.add_column('images', sa.Column('user_name', sa.VARCHAR(), nullable=False, server_default=''))

    # 2. 数据迁移：将 author_id 映射回 user_name
    op.execute("""
        UPDATE images SET user_name = users.username
        FROM users
        WHERE images.author_id = users.id
    """)

    # 3. 恢复旧索引
    op.create_index(op.f('ix_images_user_name'), 'images', ['user_name'], unique=False)
    op.create_index(op.f('ix_images_created_at'), 'images', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # 4. 恢复旧 FK
    op.create_foreign_key(op.f('images_user_name_fkey'), 'images', 'users', ['user_name'], ['username'])

    # 5. 删除新 FK 和索引
    op.drop_constraint(None, 'images', type_='foreignkey')
    op.drop_index(op.f('ix_images_author_id'), table_name='images')

    # 6. 恢复 created_at 为 nullable（users）
    op.alter_column('users', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))

    # 7. 恢复 category 为 VARCHAR
    op.alter_column('images', 'category',
                    existing_type=postgresql.ENUM('GALLERY', 'TRAVEL', 'NATURE', 'PORTRAIT', 'ARCHITECTURE', 'ABSTRACT', name='category', create_type=False),
                    type_=sa.VARCHAR(length=100),
                    postgresql_using='category::text')

    # 8. 恢复 tags 为 VARCHAR
    op.alter_column('images', 'tags',
                    existing_type=postgresql.ARRAY(sa.String()),
                    type_=sa.VARCHAR(length=500),
                    postgresql_using="ARRAY_TO_STRING(tags, ',')")

    # 9. 恢复 created_at 为 nullable（images）
    op.alter_column('images', 'created_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    nullable=True,
                    existing_server_default=sa.text('now()'))

    # 10. 删除 author_id 列
    op.drop_column('images', 'author_id')

    # 11. 删除枚举类型
    op.execute("DROP TYPE IF EXISTS category")
