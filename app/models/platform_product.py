from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PlatformProduct(Base):
    """Productos SaaS de Binfrix (autolavado, ecommerce-b2c, pagos, etc.)."""

    __tablename__ = "platform_products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    licenses: Mapped[list["TenantLicense"]] = relationship(back_populates="platform_product")
