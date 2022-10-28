from model_to_entity import EntityMaker

class ProductV2(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    is_bookmarked: Optional[bool] = None
    default_variant: Optional[Variant] = None
    colors: Optional[list] = None
    product_variants: Optional[Variant] = None
    phone_model: Optional[PhoneModel] = None
    sub_phones: Optional[SubPhone] = None
    phone: Optional[Phone] = None
    info: Optional[dict] = None
    badges: Optional[list] = None
    types: Optional[list] = None
    cover: Optional[File] = None
    media: Optional[File] = []
    attributes: Optional[list] = []
    extra_data: Optional[list] = []
    brand: Optional[dict] = {}
    description: Optional[dict] = {}
    comments: Optional[dict] = {}
    user_review: Optional[list] = []
    related_products: Optional[list] = []




product_db = ProductDB.objects.select_related('phone', 'category', 'cover', 'default_variant',
                                                          'default_variant__color',
                                                          'default_variant__shop',

                                                          'default_variant__warranty',
                                                          'default_variant__sub_phone').prefetch_related(
                'media').prefetch_related(
                Prefetch('product_variants',
                         queryset=VariantDB.objects.select_related('color', 'warranty', 'shop').filter(
                             status='marketable'))).get(id=product_id,
                                                        is_deleted=False)
 product = EntityMaker().model_to_entity(product_db, ProductV2)
