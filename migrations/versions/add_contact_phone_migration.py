"""Add contact_phone to Donation model

Revision ID: add_contact_phone_v2
Create Date: 2024-03-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_contact_phone_v2'
down_revision = 'd2e598fddd78'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add the column as nullable
    op.add_column('donation', sa.Column('contact_phone', sa.String(20), nullable=True))
    
    # Step 2: Update existing records with a default phone number
    op.execute("UPDATE donation SET contact_phone = 'Not provided' WHERE contact_phone IS NULL")
    
    # Step 3: Make the column non-nullable
    op.alter_column('donation', 'contact_phone',
                    existing_type=sa.String(20),
                    nullable=False)

def downgrade():
    op.drop_column('donation', 'contact_phone') 