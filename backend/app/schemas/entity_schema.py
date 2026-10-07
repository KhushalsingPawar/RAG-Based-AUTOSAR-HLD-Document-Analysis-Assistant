from pydantic import BaseModel
from typing import List, Optional


class SoftwareComponent(BaseModel):
    name: str
    page_number: int
    description: Optional[str] = None


class InterfaceEntity(BaseModel):
    name: str
    page_number: int
    interface_type: Optional[str] = None
    description: Optional[str] = None


class PortEntity(BaseModel):
    name: str
    page_number: int
    port_type: Optional[str] = None
    interface_name: Optional[str] = None


class SignalEntity(BaseModel):
    name: str
    page_number: int
    data_type: Optional[str] = None
    description: Optional[str] = None


class DependencyEntity(BaseModel):
    source: str
    target: str
    page_number: int
    relationship: Optional[str] = None


class FunctionalFlow(BaseModel):
    name: str
    page_number: int
    description: Optional[str] = None


class AutosarEntities(BaseModel):
    software_components: List[SoftwareComponent]
    interfaces: List[InterfaceEntity]
    ports: List[PortEntity]
    signals: List[SignalEntity]
    dependencies: List[DependencyEntity]
    functional_flows: List[FunctionalFlow]