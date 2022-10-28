import django.db.models
import pydantic
from django.db.models import Model
from pydantic import BaseModel
import typing


class EntityMaker:
    imported = {}

    @classmethod
    def importer(cls, components, name):
        components = components.split('.')
        components.append(name)

        if ".".join(components) in list(cls.imported.keys()):
            return cls.imported[".".join(components)]
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        cls.imported.update({".".join(components): mod})
        return mod

    def _set_relational_field(
            self,
            entity_instance: BaseModel,
            entity_types,
            sub_entity,
            model_values
    ):
        result_values = []
        for model_value in model_values:
            # todo: list of entity
            _type, bounded_type = self.get_type(entity_types, sub_entity)

            if not _type:
                return

            sub_entity_class = self.importer(_type.__module__, _type.__name__)
            sub_entity_instance = sub_entity_class()
            sub_entity_instance = self.model_to_entity(
                model_value,
                entity_class=sub_entity_class,
                entity_instance=sub_entity_instance
            )
            result_values.append(sub_entity_instance)
        if len(result_values) > 1:
            entity_instance.__setattr__(sub_entity, result_values)
        else:
            try:
                entity_instance.__setattr__(sub_entity, result_values[0])
            except:
                pass

    def model_to_entity(
            self,
            model_instance: Model,
            entity_class=None,
            entity_instance: BaseModel = None,
            **kwargs,
    ):
        r"""convert django model to pydantic entity (BaseModel)
        :params model:
            django model
        :params entity_class:
            pydantic entity class name
        :params entity_instance:
        :param \**kwargs:
            set sub model name to get it if set true get it lazy and if set it false remove it even exist in
            model cache and don't set it for move only exist in cache value
        """
        if entity_instance is None:
            entity_instance = entity_class()
        if model_instance is None:
            return
        model_relations = [{n.get_cache_name(): n} for n in
                           model_instance._meta.get_fields()
                           if type(
                n) == django.db.models.fields.related.ForeignKey or type(
                n) == django.db.models.fields.related.ManyToManyField or type(n) == django.db.models.ManyToOneRel]
        model_keys = model_instance.__dict__.keys()
        entity_keys = entity_instance.__dict__.keys()
        entity_types = typing.get_type_hints(entity_instance)
        if hasattr(entity_instance, "model_to_entity_improvement"):
            entity_instance.model_to_entity_improvement(model_instance)

        for model_key in model_keys:
            if model_key in entity_keys and not (model_key in kwargs and not kwargs[model_key]):
                entity_instance.__setattr__(model_key, model_instance.__getattribute__(model_key))

        for model_relation in model_relations:
            relation_key = list(model_relation.keys())[0]
            relation_value = list(model_relation.values())[0]
            if relation_key not in entity_keys:
                continue

            if relation_key in kwargs and kwargs[relation_key]:
                # execute query
                value = model_instance.__getattribute__(relation_key)
                self._set_relational_field(entity_instance, entity_types, relation_key, [value])
            elif relation_key in kwargs and not kwargs[relation_key]:
                # delete some keys
                self._set_relational_field(entity_instance, entity_types, relation_key, [None])
            elif relation_value.is_cached(model_instance):
                # get only exist, dont execute query
                value = relation_value.get_cached_value(model_instance)
                self._set_relational_field(entity_instance, entity_types, list(model_relation.keys())[0], [value])
            elif hasattr(model_instance,
                         "_prefetched_objects_cache") and relation_key in model_instance._prefetched_objects_cache:
                values = model_instance._prefetched_objects_cache[relation_key]
                self._set_relational_field(entity_instance, entity_types, relation_key, values)
        return entity_instance

    @staticmethod
    def get_type(entity_types, sub_entity):
        bounded_type = False
        _type = None
        if type(entity_types[sub_entity]) == typing._GenericAlias:
            for union_item in entity_types[sub_entity].__args__:
                if issubclass(union_item, BaseModel):
                    _type = union_item
        elif type(entity_types[sub_entity]) == pydantic.main.ModelMetaclass:
            _type = entity_types[sub_entity]
        # for optional types __ we must take the inner type of field
        elif type(entity_types[sub_entity].__args__[0]) == pydantic.main.ModelMetaclass:
            _type = entity_types[sub_entity].__args__[0]
        elif hasattr(entity_types[sub_entity].__args__[0], "__bound__"):
            _type = entity_types[sub_entity].__args__[0]
            bounded_type = True
        return _type, bounded_type

    def _dict_set_relational_field(
            self,
            entity_instance: BaseModel,
            entity_types,
            sub_entity,
            model_values
    ):
        _type, bounded_type = self.get_type(entity_types, sub_entity)
        if not _type:
            return
        if bounded_type:
            sub_entity_class = self.importer(_type.__bound__.__forward_arg__, _type.__name__)
        else:
            sub_entity_class = self.importer(_type.__module__, _type.__name__)
        sub_entity_instance = sub_entity_class()
        sub_entity_instance = self.dict_to_entity(
            data=model_values,
            entity_class=sub_entity_class,
            entity_instance=sub_entity_instance
        )

        entity_instance.__setattr__(sub_entity, sub_entity_instance)

    def dict_to_entity(
            self,
            data: dict,
            entity_class=None,
            entity_instance: BaseModel = None,
            **kwargs,
    ):
        if entity_instance is None:
            entity_instance = entity_class()
        entity_types = typing.get_type_hints(entity_instance)
        data_keys = list(data.keys())
        next_data = {}
        for key in data_keys:
            splited_key = key.split("__")
            if len(splited_key) > 1:
                try:
                    next_data[splited_key[0]].update({"__".join(splited_key[1:]): data[key]})
                except KeyError:
                    next_data[splited_key[0]] = {"__".join(splited_key[1:]): data[key]}
            else:
                try:
                    print("key:", key, "val:", data[key])
                    entity_instance.__setattr__(key, data[key])
                except Exception as e:
                    pass
        for data in next_data.keys():
            self._dict_set_relational_field(entity_instance, entity_types, data, next_data[data])
        return entity_instance
