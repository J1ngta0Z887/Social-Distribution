# API Documentation

## Overview

Base URL: `/api`  
API Format:  `json`
Authentication: Django user based.
---



### List All Authors
Endpoint: `GET /authors`
Requires Authentication?: No

Returns a paginated list of all authors in the system.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `size` | integer | 10 | Items per page |

**Example Request:**
```http
GET /authors?page=1&size=5
```

**Example Response:**
```json
{
  "type": "authors",
  "page": 1,
  "size": 5,
  "authors": [
    {
      "type": "author",
      "id": "https://example.com/authors/1",
      "host": "https://example.com/api",
      "displayName": "authors name",
      "bio": "authors detailed bio",
      "github": "https://github.com/authorname",
      "profileImage": "https://example.com/images/john.jpg",
      "web": "https://example.com/authors/author%20name"
    }
  ]
}
```
---
### List Author
Endpoint: `GET /author/{AUTHOR_SERIAL}`
Requires Authentication?: No

**Example Request:**
```http
GET /authors/1
OR
GET /authors/author%20name
```

**Example Response:**
```json

{
  "type": "author",
  "id": "https://example.com/authors/1",
  "host": "https://example.com/api",
  "displayName": "authors name",
  "bio": "authors detailed bio",
  "github": "https://github.com/authorname",
  "profileImage": "https://example.com/images/john.jpg",
  "web": "https://example.com/authors/author%20name"
}
```

Endpoint: `PUT /author/{AUTHOR_SERIAL}`
Requires Authentication?: Yes

**Example Request:**
```http
PUT /authors/1
OR
PUT /authors/author%20name
```
Request body:
```json
{
  "displayName": "updated author name",
  "github": "https://github.com/newauthorname",
  "profileImage": "https://example.com/images/new.jpg"
}
```

**Example Response:**
```json

{
  "type": "author",
  "id": "https://example.com/authors/1",
  "host": "https://example.com/api",
  "displayName": "updated author name",
  "bio": "authors detailed bio",
  "github": "https://github.com/newauthornams",
  "profileImage": "https://example.com/images/new.jpg",
  "web": "https://example.com/authors/new%20author%20name"
}
```
