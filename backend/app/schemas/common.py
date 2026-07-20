from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    def persisted_values(self, *, exclude_unset: bool = True) -> dict:
        values = self.model_dump(exclude_unset=exclude_unset)
        return {key: self._value_for_persistence(value) for key, value in values.items()}

    @staticmethod
    def _value_for_persistence(value: object) -> object:
        if value is None:
            return value
        if isinstance(value, list):
            return [Schema._value_for_persistence(item) for item in value]
        if isinstance(value, dict):
            return {key: Schema._value_for_persistence(item) for key, item in value.items()}
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (str, int, float, bool, datetime, date, UUID)):
            return value
        return str(value)


class TimestampedSchema(Schema):
    id: UUID
    created_at: datetime
    updated_at: datetime
