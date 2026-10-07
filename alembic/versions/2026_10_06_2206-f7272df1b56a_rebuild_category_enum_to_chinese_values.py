"""rebuild category enum to chinese values

Revision ID: f7272df1b56a
Revises: ec2f092f4bd5
Create Date: 2026-10-06 22:06:41.033128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7272df1b56a'
down_revision: Union[str, Sequence[str], None] = 'ec2f092f4bd5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE category RENAME TO category_old")
    op.execute("CREATE TYPE category AS ENUM ('画廊','旅行','自然','人像','建筑','抽象')")
    op.execute(
        "ALTER TABLE images ALTER COLUMN category "
        "TYPE category USING category::text::category"
    )
    op.execute("DROP TYPE category_old")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE category RENAME TO category_new")
    op.execute(
        "CREATE TYPE category AS ENUM "
        "('GALLERY','TRAVEL','NATURE','PORTRAIT','ARCHITECTURE','ABSTRACT',"
        "'画廊','旅行','自然','人像','建筑','抽象')"
    )
    op.execute(
        "ALTER TABLE images ALTER COLUMN category "
        "TYPE category USING category::text::category"
    )
    op.execute("DROP TYPE category_new")
