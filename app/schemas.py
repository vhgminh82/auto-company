from pydantic import BaseModel


class CrawlRequest(BaseModel):
    query: str
    country: str = ""
    region: str = ""
    industry: str = ""
    max_companies: int = 50


class CompanyOut(BaseModel):
    id: int
    name: str
    address: str
    city: str
    state: str
    website: str
    contact: str
    email: str
    email_2: str
    phone: str
    short_description: str
    facebook: str
    facebook_alt: str
    youtube: str
    x: str
    linkedin: str
    truth: str
    country: str
    industry: str
    source_url: str

    class Config:
        from_attributes = True
