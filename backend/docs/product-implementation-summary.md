# Product Implementation Summary

This summarizes the product/inventory work implemented on the backend.

## Product API Shape

The product API now uses `category` as a category name string instead of
exposing `category_id` in product JSON.

Example product response:

```json
{
  "id": "product-uuid",
  "category": "Matcha",
  "name": "Matcha Latte",
  "description": "Classic matcha latte",
  "selling_price": "55000.00",
  "is_available": true,
  "has_image": true,
  "image_url": "https://res.cloudinary.com/example/image/upload/matcha-latte.png"
}
```

Internally the database stores `products.category` as a plain string. There is
no product category ID and no `product_categories` table.

## Product Endpoints

Current product endpoints:

```text
GET    /api/v1/products
GET    /api/v1/products/category
GET    /api/v1/products/{product_id}
POST   /api/v1/products
PUT    /api/v1/products/{product_id}
PATCH  /api/v1/products/{product_id}/availability
DELETE /api/v1/products/{product_id}
GET    /api/v1/products/{product_id}/recipe
POST   /api/v1/products/{product_id}/recipe
PUT    /api/v1/products/{product_id}/recipe
```

Category CRUD route handlers were removed from product routes.

## Product Creation

`POST /api/v1/products` creates a product using a category name:

```json
{
  "category": "Matcha",
  "name": "Matcha Latte",
  "description": "Classic matcha latte",
  "selling_price": 55000,
  "is_available": true,
  "image_url": "https://res.cloudinary.com/example/image/upload/matcha-latte.png"
}
```

The same endpoint can also create the product recipe:

```json
{
  "category": "Matcha",
  "name": "Matcha Latte",
  "description": "Classic matcha latte",
  "selling_price": 55000,
  "is_available": true,
  "recipe": {
    "items": [
      {
        "ingredient_id": "ingredient-uuid",
        "quantity_per_serving": 12.5
      }
    ]
  }
}
```

Recipe validation checks:

- Product must exist for recipe-only endpoints.
- Ingredient IDs must exist and not be deleted.
- Duplicate ingredient IDs are rejected.
- Recipe quantities must be positive.

## Inventory Reduction Logic

Inventory is not reduced when an order is created.

Inventory is reduced when an order is completed:

```text
Order completion
  -> order items
  -> product_id
  -> product_recipes
  -> ingredients.current_stock
```

For each order item:

```text
required ingredient quantity = quantity_per_serving * ordered product quantity
```

On completion the service:

- Checks the order is not cancelled or already completed.
- Requires payment status `paid`, except the placeholder COD delivery rule.
- Loads product recipes.
- Locks ingredient rows with `FOR UPDATE`.
- Rejects completion if stock is insufficient.
- Deducts `ingredients.current_stock`.
- Creates `inventory_movements` with `movement_type = sale_deduction`.
- Creates `financial_records` for revenue and material cost.
- Commits once.

## Product Images

Product images are represented by a nullable `products.image_url` string column.
The backend stores the URL only; image bytes should live in an external image
host/CDN.

Image behavior:

- `POST /products` and `PUT /products/{product_id}` can set `image_url`.
- `PUT /products/{product_id}` can clear `image_url` by setting it to `null`.
- Product JSON includes `has_image = true` when `image_url` is present.

Normal product JSON never includes raw image bytes.

## Database Migration

The canonical SQL was updated:

```text
db/init/020_catalog_inventory.sql
```

Alembic migrations were added:

```text
alembic/versions/20260604_add_product_image_columns.py
alembic/versions/20260604_simplify_product_category_and_image_url.py
```

Existing databases need the simplify migration or equivalent SQL to replace
`products.category_id` with `products.category`, remove `product_categories`,
and replace encrypted image columns with `products.image_url`.

## Compatibility Fixes

The backend now avoids `datetime.UTC` because the `huync` environment uses
Python 3.10. The equivalent `timezone.utc` is used instead.

`app/models/__init__.py` was also consolidated so model exports do not duplicate
`User` and break linting.
