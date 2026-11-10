# Show Sourcing API

Show Sourcing has two ways for your own code and AI tools to reach your team's products and vendors:

1. **REST API (v1)**: plain JSON over HTTPS. Use it from any language, script or no-code tool.
2. **MCP server**: for Claude, ChatGPT, Claude Code and other MCP apps. See [MCP server](#mcp-server) below.

Both use the same token. Machine-readable spec: [https://showsourcing.app/openapi.json](https://showsourcing.app/openapi.json).
This page as plain text: [https://showsourcing.app/docs/api.md](https://showsourcing.app/docs/api.md).

## REST API (v1)

Base URL: `https://api.showsourcing.app/functions/v1/api`

All routes sit under `/v1`. Every request and response is JSON.

### Auth

The API uses the same token as the AI Connection. One token works for both.

1. In the app (iPhone, iPad, Mac or Android), open Settings > AI Connection & API.
2. Tap Create token. To add data, turn on "Can add products and vendors". The app shows the token once.
3. Send it in a header on every request:

```
Authorization: Bearer ss_xxxxxxxx
```

`X-API-Key: ss_xxxxxxxx` also works.

A token is tied to one team. It can only see that team's data.
A token is read-only unless you made it with write access.
Revoke a token in the app and it stops working at once.

A token stops working when its owner leaves the team. Make a new one.

#### Plans

- With a paid plan, you see everything.
- On a free trial or with no plan, reads show only your first 10 products and first 5 vendors. The response has a `plan_limit` note.
- Adding data (POST) needs a paid plan or a free trial. With no plan, POST returns 402.

### Routes

| Route | What it does |
|---|---|
| `GET /v1/products` | List and search products |
| `GET /v1/products/{id}` | One product, with photo links |
| `POST /v1/products` | Add a product (write token) |
| `GET /v1/vendors` | List and search vendors |
| `GET /v1/vendors/{id}` | One vendor |
| `POST /v1/vendors` | Add a vendor (write token) |

There is no update or delete in v1.

#### List products

`GET /v1/products?q=&limit=&offset=&updated_since=`

| Parameter | Meaning |
|---|---|
| `q` | Search text (max 200 characters). Matches vendor, category, notes, venue and the photo description. |
| `limit` | Rows to return. Default 50, maximum 200. |
| `offset` | Rows to skip. Default 0. |
| `updated_since` | ISO 8601 date. Only products changed at or after it. These come oldest change first, so you can page through changes. |

Without `updated_since`, newest products come first.

```bash
curl -H "Authorization: Bearer $SS_TOKEN" \
  "https://api.showsourcing.app/functions/v1/api/v1/products?q=lamp&limit=2"
```

```json
{
  "data": [
    {
      "id": "6f1c0a52-8d54-4a4b-9a43-0d7a1f3c9e10",
      "vendor": "Shenzhen ABC",
      "vendor_id": "95d5aa80-5433-487f-bbc1-29c3f2434d41",
      "category": "Lamps",
      "fob": 4.2,
      "currency": "USD",
      "price_term": "FOB",
      "moq": 500,
      "container_qty": 4000,
      "package_cbm": null,
      "country_of_origin": ["China"],
      "tariff_override": null,
      "tags": ["led", "desk"],
      "specs": "USB powered, 3 brightness levels",
      "venue": "Canton Fair",
      "status": null,
      "photo_count": 3,
      "photo_description": "a white desk lamp on a table",
      "created_at": "2026-11-01T10:00:00+00:00",
      "updated_at": "2026-11-02T09:30:00+00:00",
      "thumbnail": "https://api.showsourcing.app/storage/v1/object/sign/Media/..."
    }
  ],
  "count": 1,
  "total": 1,
  "limit": 2,
  "offset": 0,
  "has_more": false
}
```

`thumbnail` is a link to the first photo. It is set for the first 30 rows of a page. It expires after 7 days.
`photo_description` is written by a machine. It is often wrong. Do not treat it as fact.

#### Get one product

```bash
curl -H "Authorization: Bearer $SS_TOKEN" \
  "https://api.showsourcing.app/functions/v1/api/v1/products/6f1c0a52-8d54-4a4b-9a43-0d7a1f3c9e10"
```

It returns the same fields as the list, plus `photos`: up to 8 photo links (images only, no videos). The links expire after 7 days.

#### Add a product

`POST /v1/products` with a write token.

```bash
curl -X POST -H "Authorization: Bearer $SS_TOKEN" -H "Content-Type: application/json" \
  -d '{"vendor":"Shenzhen ABC","name":"LED desk lamp","category":"Lamps","fob":4.2,"currency":"USD","moq":500,"notes":"USB powered","tags":["led","desk"]}' \
  "https://api.showsourcing.app/functions/v1/api/v1/products"
```

It returns `201` and the new product. The product shows up on the team's phones through normal sync.

| Field | Type | Notes |
|---|---|---|
| `vendor` | string, max 200 | Vendor name. If the team has a vendor with this name (case ignored), the product links to it. If not, a new vendor with this name is created. |
| `vendor_id` | UUID | Link to an existing vendor. Use this or `vendor`. |
| `name` | string, max 200 | Product name. The app has no name field, so it is saved as the first line of the notes. |
| `category` | string, max 100 | |
| `fob` | number, 0 to 1,000,000,000 | FOB price per unit. |
| `currency` | string | 3-letter code. Default `USD`. |
| `price_term` | string | `FOB`, `CIF`, `EXW` or `DDP`. |
| `moq` | whole number | Minimum order quantity. |
| `container_qty` | whole number | Units per container. |
| `specs` or `notes` | string, max 5000 | Notes (the app calls this field Notes). If you send both, they are joined. |
| `tags` | array of strings, or one comma list | Max 30 tags, 50 characters each. |
| `country_of_origin` | array of strings, or one comma list | Max 10. |
| `venue` | string, max 200 | Show or place. |

Send at least one of `vendor`, `vendor_id`, `name`, `category`, `fob`, `specs`, `notes`.
Other fields return 400 `unknown_field`.
Photos are not part of v1. Add photos in the app.

#### List vendors

`GET /v1/vendors?q=&limit=&offset=`

`q` matches the vendor name. Rows come sorted by name. `limit` and `offset` work as for products.

```bash
curl -H "Authorization: Bearer $SS_TOKEN" \
  "https://api.showsourcing.app/functions/v1/api/v1/vendors?q=shenzhen"
```

```json
{
  "data": [
    {
      "id": "95d5aa80-5433-487f-bbc1-29c3f2434d41",
      "name": "Shenzhen ABC",
      "contacts": [{ "name": "Cindy Liu", "title": "Sales" }],
      "emails": ["cindy@abc.example"],
      "phones": [{ "type": "office", "number": "+86 755 0000 0000" }],
      "websites": ["https://abc.example"],
      "wechats": [],
      "addresses": ["12 Example Road, Shenzhen, Guangdong, China"],
      "notes": null,
      "product_count": 4,
      "created_at": "2026-10-20T08:00:00+00:00",
      "updated_at": "2026-10-20T08:00:00+00:00"
    }
  ],
  "count": 1, "total": 1, "limit": 50, "offset": 0, "has_more": false
}
```

#### Get one vendor

`GET /v1/vendors/{id}` returns the same fields, plus `photos`: up to 4 photo links (business card photos).

#### Add a vendor

`POST /v1/vendors` with a write token.

```bash
curl -X POST -H "Authorization: Bearer $SS_TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Shenzhen ABC","contact":"Cindy Liu","email":"cindy@abc.example","phone":"+86 755 0000 0000","website":"https://abc.example","address":{"street":"12 Example Road","city":"Shenzhen","country":"China"}}' \
  "https://api.showsourcing.app/functions/v1/api/v1/vendors"
```

It returns `201` and the new vendor.

| Field | Type | Notes |
|---|---|---|
| `name` | string, max 200 | Required. |
| `contact` / `contacts` | name string, or `{name, title}`; or an array of them | Max 20. |
| `email` / `emails` | string, or array of strings | Must look like an email address. Max 20. |
| `phone` / `phones` | number string, or `{number, type}`; or an array | `type` is `mobile`, `office`, `fax` or `other`. A plain string gets `office`. Max 20. |
| `website` / `websites` | string, or array of strings | Max 10. |
| `wechat` / `wechats` | string, or array of strings | WeChat IDs. Max 10. |
| `address` / `addresses` | string, or `{street, city, state, postal_code, country}`; or an array | Saved as one line. Max 10. |
| `notes` | string, max 5000 | |

If the team already has a vendor with the same name (case ignored), the API returns 409 `already_exists` with the existing id.
Other fields return 400 `unknown_field`.

### Errors

Every error has this shape:

```json
{ "error": { "code": "invalid_token", "message": "This token is not valid. It may be revoked." } }
```

| Status | Code | When |
|---|---|---|
| 400 | `invalid_request`, `invalid_json`, `invalid_id`, `unknown_field`, `vendor_not_found`, `vendor_not_linked` | Bad input. The message says which field. |
| 401 | `missing_token`, `invalid_token` | No token, an unknown token, or a revoked token. |
| 402 | `plan_required` | POST with no plan and no trial. |
| 403 | `read_only_token` | POST with a token that has no write access. |
| 403 | `no_team`, `team_changed` | The token has no team, or its owner left the team. |
| 404 | `not_found` | No such route, or no such row in your team. |
| 405 | `method_not_allowed` | For example DELETE. The `Allow` header lists what works. |
| 409 | `already_exists` | A vendor with this name exists. |
| 429 | `rate_limited` | Too many requests. The `Retry-After` header gives seconds. |
| 500 | `internal_error` | Our side. Try again. |

### Limits

- 120 requests per minute per token. Every response has `X-RateLimit-Limit` and `X-RateLimit-Remaining`.
- Request body: 100 KB.
- Photo links expire after 7 days. Ask again for new links.

## MCP server

The MCP server lets an AI app search your catalog in plain words ("which vendors had LED desk lamps under $5?").
You use your own AI account. We never see your AI key.

- Server URL: `https://api.showsourcing.app/functions/v1/mcp`
- Transport: Streamable HTTP (not STDIO).
- Auth: the same token, as `Authorization: Bearer ss_xxxxxxxx`. Apps that cannot send headers can put it in the URL instead: `https://api.showsourcing.app/functions/v1/mcp?key=ss_xxxxxxxx` (treat that URL like a password).
- Read only. The MCP server never adds, edits or deletes.

### Tools

| Tool | What it does |
|---|---|
| `search_products` | Search the team's products by vendor, category, specs, tags or photo description. Returns id, vendor, category, FOB price, MOQ and photo count. |
| `get_product` | The full record of one product, including LDP (landed duty paid, USD) and photos. |
| `show_products` | Shows up to 12 products as one photo grid (photo, vendor, price, MOQ). |
| `vendor_for_email` | Finds the vendor an email address belongs to (exact address first, then the company domain) and lists its products. |
| `list_vendors` | The team's vendors, with how many products each has. Optional name filter. |

### Connect

- **Claude**: Settings > Connectors > Add custom connector. Name: Show Sourcing. URL: the server URL with `?key=<your token>`. Leave the OAuth fields empty.
- **ChatGPT** (Mac app): Settings > Apps > Connect to a custom MCP. Type: Streamable HTTP. URL: the server URL. Under Headers add `Authorization` = `Bearer <your token>`.
- **Claude Code**:

```bash
claude mcp add --transport http show-sourcing https://api.showsourcing.app/functions/v1/mcp --header "Authorization: Bearer $SS_TOKEN"
```

The app shows these steps with your real token filled in, under Settings > AI Connection & API.

## Help

Questions or a missing endpoint: support@showsourcing.app.
