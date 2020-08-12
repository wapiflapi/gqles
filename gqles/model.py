from dataclasses import dataclass

import pydantic

from eventsourcing.domain.model.entity import MetaDomainEntity


# FIXME: Before this goes into production it should be proven
# compatible with the whole eventsourcing library.

class ModelMetaclassWithMetaDomainEntity(
        pydantic.main.ModelMetaclass, MetaDomainEntity,
):
    pass

class Model(pydantic.BaseModel, metaclass=ModelMetaclassWithMetaDomainEntity):

    def __is_annotated(self, name):
        try:
            return name in self.__annotations__
        except AttributeError:
            return False

    def __init__(self, **kwargs):
        # Fun fact: pydantic.BaseModel doesn't call super().__init__.
        # Let's abuse that so we can filter out used kwargs.
        pydantic.BaseModel.__init__(self, **kwargs)
        # Now we call super, starting after BaseModel.
        super(pydantic.BaseModel, self).__init__(**{
            k: v for k, v in kwargs.items() if not self.__is_annotated(k)
        })

    def __setattr__(self, attr, value):
        # Since eventsourcing doesn't use pedantic we need to bypass
        # pydantic.BaseModel for attributes that aren't managed by it.
        return (
            super(Model, self) if self.__is_annotated(attr)
            else super(pydantic.BaseModel, self)
        ).__setattr__(attr, value)
