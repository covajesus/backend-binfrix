from sqlalchemy.orm import Session

from app.models.slider import Slider
from app.repositories.base import BaseRepository
from app.schemas.slider import SliderCreate, SliderUpdate
from app.services.base import BaseService


class SliderRepository(BaseRepository[Slider]):
    model = Slider


class SliderService(BaseService):
    def __init__(self, db: Session, tenant_id: str):
        super().__init__(db)
        self.repo = SliderRepository(db, tenant_id=tenant_id)

    def list_sliders(self) -> list[Slider]:
        return self.repo.list_all(order_by=(Slider.sort_order, Slider.created_at))

    def get_slider(self, slider_id: str) -> Slider:
        return self.repo.get_by_id(slider_id)

    def create_slider(self, payload: SliderCreate) -> Slider:
        slider = Slider(
            tenant_id=self.repo.tenant_id,
            title=payload.title.strip(),
            subtitle=payload.subtitle.strip(),
            cta=payload.cta.strip() or "Comprar",
            link_suffix=payload.link_suffix.strip().lstrip("/"),
            image_url=payload.image_url.strip(),
            theme=payload.theme if payload.theme in ("dark", "light") else "dark",
            sort_order=payload.sort_order,
            status=payload.status,
        )
        self.repo.add(slider)
        self.commit()
        return self.repo.refresh(slider)

    def update_slider(self, slider_id: str, payload: SliderUpdate) -> Slider:
        slider = self.repo.get_by_id(slider_id)
        data = payload.model_dump(exclude_unset=True)
        if "title" in data and data["title"] is not None:
            data["title"] = data["title"].strip()
        if "subtitle" in data and data["subtitle"] is not None:
            data["subtitle"] = data["subtitle"].strip()
        if "cta" in data and data["cta"] is not None:
            data["cta"] = data["cta"].strip() or "Comprar"
        if "link_suffix" in data and data["link_suffix"] is not None:
            data["link_suffix"] = data["link_suffix"].strip().lstrip("/")
        if "image_url" in data and data["image_url"] is not None:
            data["image_url"] = data["image_url"].strip()
        if "theme" in data and data["theme"] not in ("dark", "light"):
            data["theme"] = "dark"

        for field, value in data.items():
            setattr(slider, field, value)

        self.commit()
        return self.repo.refresh(slider)

    def delete_slider(self, slider_id: str) -> None:
        slider = self.repo.get_by_id(slider_id)
        self.repo.delete(slider)
        self.commit()
