from pydantic import BaseModel, EmailStr, Field


class CustomerRegister(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str = ""
    city: str = ""


class CustomerLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class CustomerShippingAddressOut(BaseModel):
    id: str
    label: str
    address: str
    city: str
    region: str
    phone: str
    is_default: bool


class CustomerAccountOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    shipping_addresses: list[CustomerShippingAddressOut] = []

    model_config = {"from_attributes": True}


class CustomerShippingAddressCreate(BaseModel):
    label: str = ""
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=120)
    region: str = ""
    phone: str = ""
    is_default: bool = False


class CustomerShippingAddressUpdate(BaseModel):
    label: str | None = None
    address: str | None = Field(default=None, min_length=1, max_length=500)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    region: str | None = None
    phone: str | None = None
    is_default: bool | None = None


class CustomerAuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: CustomerAccountOut


class CustomerProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = None
    city: str | None = None
