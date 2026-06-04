# Product API Testing Guide

This guide tests the product, recipe, inventory, order, payment, and image flow
without using `jq`.

## Start Backend

### Local Python

From `backend/`, this runs the backend on your machine:

```bash
conda activate huync
uvicorn main:app --reload
```

### Docker Backend With Existing Tailscale DB

If `backend/.env` points to the shared Tailscale database, start only the
backend service. Do not start the Compose `db` service.

```bash
sudo docker compose up -d backend
```

Check that the backend container is running:

```bash
sudo docker compose ps backend
sudo docker logs matcha_backend --tail 50
```

Open API docs:

```text
http://localhost:8000/docs
http://localhost:8000/redoc
```

Basic health check:

```bash
curl http://localhost:8000/health
```

Database connectivity check:

```bash
curl http://localhost:8000/api/v1/status/db
```

Expected result:

```json
{"success":true,"data":{"status":"database_ready"}}
```

If this returns `database_unavailable`, the backend is running but cannot reach
the database configured in `backend/.env`. Check that Tailscale is connected,
the DB host is reachable, and the existing DB schema has already been updated
to use `products.category` and `products.image_url`.

## Shell Variables

`BASE` is only a shortcut so you do not type the full API prefix every time.

```bash
BASE=http://localhost:8000/api/v1
USER_ID=PASTE_REAL_USER_UUID_FROM_DB_HERE
```

These commands:

```bash
curl $BASE/products
curl $BASE/payments/methods
```

are the same as:

```bash
curl http://localhost:8000/api/v1/products
curl http://localhost:8000/api/v1/payments/methods
```

`USER_ID` must be a real `users.id` from the database because order, payment,
and inventory purchase rows have `created_by` foreign keys.

## Basic Reads

```bash
curl $BASE/products
curl $BASE/products/category
curl $BASE/ingredients
curl $BASE/payments/methods
```

Filter products by category name:

```bash
curl "$BASE/products?category=Matcha"
curl "$BASE/products/category?category=Matcha"
```

## Product API CURL Smoke Test

This section tests only the current product endpoints. The product table stores
`category` as a string and `image_url` as an external URL.

List products:

```bash
curl $BASE/products
```

List available products only:

```bash
curl "$BASE/products?is_available=true"
```

Filter by category:

```bash
curl "$BASE/products?category=Matcha"
curl "$BASE/products/category?category=Matcha"
```

Create a product:

```bash
curl -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -d '{"category":"Matcha","name":"Matcha Latte CURL Test","description":"Created from curl","selling_price":55000,"is_available":true,"image_url":"https://example.com/matcha-latte.png"}'
```

Copy the returned `data.id` and set:

```bash
PRODUCT_ID=PASTE_PRODUCT_ID_HERE
```

Get one product:

```bash
curl $BASE/products/$PRODUCT_ID
```

Update product fields:

```bash
curl -X PUT $BASE/products/$PRODUCT_ID \
  -H "Content-Type: application/json" \
  -d '{"category":"Matcha","name":"Matcha Latte Updated","description":"Updated from curl","selling_price":59000,"is_available":true,"image_url":"https://example.com/matcha-latte-updated.png"}'
```

Toggle availability:

```bash
curl -X PATCH $BASE/products/$PRODUCT_ID/availability \
  -H "Content-Type: application/json" \
  -d '{"is_available":false}'
```

Set or clear `image_url` by updating the product with
`PUT /products/{product_id}`.

Get product recipe:

```bash
curl $BASE/products/$PRODUCT_ID/recipe
```

Replace product recipe after you have a real ingredient ID:

```bash
INGREDIENT_ID=PASTE_INGREDIENT_ID_HERE

curl -X PUT $BASE/products/$PRODUCT_ID/recipe \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"ingredient_id\":\"$INGREDIENT_ID\",\"quantity_per_serving\":12.5}]}"
```

Soft-delete product:

```bash
curl -X DELETE $BASE/products/$PRODUCT_ID
```

Delete will return `409 product_linked_to_orders` if the product is already used
by order items.

## Product API Swagger Test

Open Swagger UI:

```text
http://localhost:8000/docs
```

In Swagger, use the `products` section and run these operations in order:

1. `GET /api/v1/products`
   - Click **Try it out**.
   - Leave filters empty, or set `category=Matcha`.
   - Click **Execute**.

2. `POST /api/v1/products`
   - Click **Try it out**.
   - Use this request body:

```json
{
  "category": "Matcha",
  "name": "Matcha Latte Swagger Test",
  "description": "Created from Swagger",
  "selling_price": 55000,
  "is_available": true,
  "image_url": "https://example.com/matcha-latte.png"
}
```

   - Click **Execute**.
   - Copy `data.id` from the response.

3. `GET /api/v1/products/{product_id}`
   - Paste the copied `data.id` into `product_id`.
   - Click **Execute**.

4. `PUT /api/v1/products/{product_id}`
   - Paste the same `product_id`.
   - Use this request body:

```json
{
  "category": "Matcha",
  "name": "Matcha Latte Swagger Updated",
  "description": "Updated from Swagger",
  "selling_price": 59000,
  "is_available": true,
  "image_url": "https://example.com/matcha-latte-updated.png"
}
```

5. `PATCH /api/v1/products/{product_id}/availability`
   - Use this request body:

```json
{
  "is_available": false
}
```

6. `GET /api/v1/products/{product_id}/recipe`
   - Returns the product recipe items, or an empty list if none exists.

7. `PUT /api/v1/products/{product_id}/recipe`
   - Requires a real `ingredients.id`.
   - Use this request body:

```json
{
  "items": [
    {
      "ingredient_id": "PASTE_REAL_INGREDIENT_UUID_HERE",
      "quantity_per_serving": 12.5
    }
  ]
}
```

8. `DELETE /api/v1/products/{product_id}`
    - Soft-deletes the product.
    - This returns `409 product_linked_to_orders` if the product is already used
      by order items.

## Create Ingredient

```bash
curl -X POST $BASE/ingredients \
  -H "Content-Type: application/json" \
  -d '{"name":"Matcha powder","unit":"g","current_stock":0,"cost_per_unit":1200,"minimum_threshold":100}'
```

Copy the returned `data.id` and set:

```bash
INGREDIENT_ID=PASTE_INGREDIENT_ID_HERE
```

## Create Product

Products store `category` as a plain string. There is no product category ID.

```bash
curl -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -d '{"category":"Matcha","name":"Matcha Latte","description":"Classic matcha latte","selling_price":55000,"is_available":true}'
```

Copy the returned `data.id` and set:

```bash
PRODUCT_ID=PASTE_PRODUCT_ID_HERE
```

## Create Product With Recipe

`POST /products` can also create the product recipe in the same request:

```bash
curl -X POST $BASE/products \
  -H "Content-Type: application/json" \
  -d "{\"category\":\"Matcha\",\"name\":\"Matcha Latte Recipe Test\",\"description\":\"With recipe\",\"selling_price\":55000,\"is_available\":true,\"recipe\":{\"items\":[{\"ingredient_id\":\"$INGREDIENT_ID\",\"quantity_per_serving\":12.5}]}}"
```

## Add Or Replace Product Recipe

`POST` and `PUT` currently both replace the full recipe for a product.

```bash
curl -X POST $BASE/products/$PRODUCT_ID/recipe \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"ingredient_id\":\"$INGREDIENT_ID\",\"quantity_per_serving\":12.5}]}"
```

```bash
curl -X PUT $BASE/products/$PRODUCT_ID/recipe \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"ingredient_id\":\"$INGREDIENT_ID\",\"quantity_per_serving\":12.5}]}"
```

Read recipe:

```bash
curl $BASE/products/$PRODUCT_ID/recipe
```

## Set Product Image URL

The DB stores only an external image URL, not image bytes.

```bash
curl -X PUT $BASE/products/$PRODUCT_ID \
  -H "Content-Type: application/json" \
  -d '{"category":"Matcha","name":"Matcha Latte","description":"Classic matcha latte","selling_price":55000,"is_available":true,"image_url":"https://res.cloudinary.com/example/image/upload/matcha-latte.png"}'
```

Read product and confirm `has_image` and `image_url`:

```bash
curl $BASE/products/$PRODUCT_ID
```

Clear image URL by setting it to `null`:

```bash
curl -X PUT $BASE/products/$PRODUCT_ID \
  -H "Content-Type: application/json" \
  -d '{"category":"Matcha","name":"Matcha Latte","description":"Classic matcha latte","selling_price":55000,"is_available":true,"image_url":null}'
```

## Add Stock

```bash
curl -X POST $BASE/ingredients/$INGREDIENT_ID/purchases \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d "{\"ingredient_id\":\"$INGREDIENT_ID\",\"quantity\":1000,\"cost_per_unit\":1200,\"supplier_name\":\"Test supplier\",\"notes\":\"Initial stock\",\"purchased_at\":\"2026-06-04T10:00:00+07:00\"}"
```

## Create Order, Pay, Complete

```bash
curl -X POST $BASE/orders \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d "{\"order_type\":\"instore\",\"items\":[{\"product_id\":\"$PRODUCT_ID\",\"quantity\":1}]}"
```

Copy returned `data.id`:

```bash
ORDER_ID=PASTE_ORDER_ID_HERE
```

Create payment:

```bash
curl -X POST $BASE/payments \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d "{\"order_id\":\"$ORDER_ID\",\"method\":\"cash\",\"amount\":55000,\"amount_received\":60000}"
```

Complete order. Inventory reduction happens here, not when the order is first
created:

```bash
curl -X POST $BASE/orders/$ORDER_ID/complete
```

Inspect results:

```bash
curl $BASE/orders/$ORDER_ID
curl $BASE/inventory/movements
curl $BASE/inventory/purchases
```

## Existing DB Migration

If the DB already existed with `products.category_id` and encrypted image
columns, apply the simplify Alembic migration or equivalent SQL before testing
product endpoints.
