# Product Image Encryption Plan

## Decision

Yes, products need DB support for an image if the backend is responsible for
storing product images. Because the image must be encrypted before storage, do
not expose the DB value directly through normal product JSON.

Use a nullable encrypted binary image column on `products`, plus small metadata
columns needed to validate and serve the image:

- `image bytea` - encrypted image bytes.
- `image_content_type varchar(100)` - MIME type such as `image/png`.
- `image_size_bytes integer` - original plaintext upload size.
- `image_updated_at timestamptz` - last image replacement/removal time.

The column can be named `image`, but it must store ciphertext, not raw image
bytes. API responses should expose `image_url` and/or `has_image`, not the
encrypted `image` value.

## API Shape

Keep existing product create/update JSON endpoints for text fields. Add image
specific endpoints so product metadata updates are not mixed with multipart file
uploads:

- `PUT /api/v1/products/{product_id}/image`
  - Accepts multipart field `file`.
  - Validates product exists and is not deleted.
  - Validates content type and max size.
  - Encrypts bytes in the service layer.
  - Stores ciphertext and metadata in `products`.
  - Returns the standard success response with `ProductRead`.

- `GET /api/v1/products/{product_id}/image`
  - Decrypts the stored bytes.
  - Streams/returns the image with the stored `Content-Type`.
  - Returns `404` if product or image is missing.

- `DELETE /api/v1/products/{product_id}/image`
  - Clears `image`, `image_content_type`, `image_size_bytes`, and updates
    `image_updated_at`.
  - Returns the standard success response with `ProductRead`.

Update `ProductRead` with non-sensitive image fields:

- `has_image: bool`
- `image_url: str | None`
- Optional metadata only if useful to frontend: `image_content_type`,
  `image_size_bytes`, `image_updated_at`.

Do not include base64 image data in product list responses. Lists should stay
small.

## Encryption

Add a small image crypto helper, for example:

- `backend/app/core/image_crypto.py`

Use authenticated symmetric encryption. Recommended implementation:

- Use `cryptography.fernet.Fernet`.
- Add `product_image_encryption_key` to `Settings`.
- Require a real key outside development/test environments.
- Provide a test key fixture or deterministic test setting override.

Implementation rules:

- Encrypt in the service layer before calling the repository.
- Decrypt only in the image read endpoint/service.
- Never log plaintext bytes, ciphertext bytes, or the encryption key.
- Store Fernet ciphertext directly in the `image` column.
- Add `cryptography` as a direct requirement if the project relies on it.

## Database Work

Update the canonical init SQL because this repo uses `backend/db/init/*.sql` as
the database definition:

- `backend/db/init/020_catalog_inventory.sql`
  - Add `image bytea`.
  - Add `image_content_type varchar(100)`.
  - Add `image_size_bytes integer`.
  - Add `image_updated_at timestamptz`.
  - Add a check constraint for non-negative image size:
    `image_size_bytes IS NULL OR image_size_bytes >= 0`.

Add an Alembic revision under `backend/alembic/versions/` for existing
databases:

- `upgrade()` adds the four columns and check constraint.
- `downgrade()` removes the constraint and columns.

Update the ORM:

- `backend/app/models/product.py`
  - Add matching SQLAlchemy columns.
  - Use `LargeBinary` for `image`.
  - Use `Integer` for `image_size_bytes`.
  - Keep `image` nullable so existing products remain valid.

## Backend Code Changes

Schemas:

- `backend/app/schemas/product.py`
  - Add image read fields to `ProductRead`.
  - Use a validator/computed field if needed to derive `has_image`.
  - Do not add `image` to `ProductCreate` or `ProductUpdate`.

Repository:

- `backend/app/repositories/product_repo.py`
  - Add `update_product_image(...)`.
  - Add `clear_product_image(...)`.
  - Reuse existing `get_product(...)` for image reads.

Service:

- `backend/app/services/product_service.py`
  - Add upload validation.
  - Enforce allowed content types: `image/jpeg`, `image/png`, `image/webp`.
  - Enforce a max plaintext size, for example 2 MB or a configurable setting.
  - Encrypt on upload.
  - Decrypt on read.
  - Clear image metadata on delete.

Routes:

- `backend/app/api/v1/products.py`
  - Add the three image endpoints.
  - Use FastAPI `UploadFile` and `File`.
  - Return `Response` or `StreamingResponse` for image reads.
  - Preserve `app.core.responses` format for non-streaming responses.

Settings:

- `backend/app/core/config.py`
  - Add `product_image_encryption_key`.
  - Add `product_image_max_size_bytes`, defaulting to `2097152`.
  - Add allowed image content types if configurability is desired.

## Tests

Unit tests:

- Image crypto encrypts/decrypts bytes correctly.
- Decryption fails with the wrong key or malformed ciphertext.
- Product image upload rejects unsupported MIME types.
- Product image upload rejects files over the max size.
- `ProductRead` never serializes encrypted image bytes.

Repository/service tests:

- Uploading an image stores ciphertext different from plaintext.
- Getting an image returns the original plaintext bytes and content type.
- Deleting an image clears all image columns.
- Missing product and missing image paths return `404`.

Integration tests if DB coverage is available:

- `PUT /products/{id}/image` then `GET /products/{id}/image` round trips.
- Product list includes image metadata/url only, not image bytes.
- Existing product create/update endpoints still work without image payloads.

## Implementation Order

1. Add config and image crypto helper with unit tests.
2. Add DB init SQL and Alembic revision.
3. Add ORM columns and schema read fields.
4. Add repository functions for storing and clearing encrypted image data.
5. Add service validation, encryption, decryption, and clear behavior.
6. Add product image routes.
7. Add/adjust tests.
8. Run formatting, linting, and relevant backend tests.

## Open Questions Before Coding

- Should normal product JSON expose `image_url`, `has_image`, or both?
- Is 2 MB an acceptable max image size?
- Are JPEG, PNG, and WebP enough for product images?
- Should image upload require admin/staff auth once route protection is wired?
