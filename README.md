# django-model-to-entity

created for convert django model to pydantic entity.
you can use it instead of django-rest-framework serializer.
also it can convert your raw sql response to pydantic entity.

all you need to do it's create orm select with select related or prefetch related if you need! then pass your response and pydantic class
model to entity will convert it to pydantic entity for you.

for the dict to entity! you neet to choose select names based on your pydantic model and if you have related fields you shoud put dunder between your field and target like this:  phone__logo , phone__logo__name
dict to entity will convert this for you perfectly

about performance ---->> it's about 2x faster than django-rest-framework.
if you select with raw sql you can fly...


you can se how to use in example.py file
