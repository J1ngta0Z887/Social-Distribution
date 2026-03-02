# API Documentation

**Base URL**: `/api`  
**API Format**:  `json`  
**Authentication**: Django user account.  
Some application functionality has not yet
been augmented as an API, instead acting as a
html view route. This will be changed by part 2
submission.


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
---
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
---
### Get Who Authors Following
Endpoint: `GET /author/{AUTHOR_SERIAL}/following`
Requires Authentication?: Yes

**Example Request:**
```http
GET /author/1/following
OR
GET /author/author%20name/following
```

**Example Response:**
```json
{
  "type": "following",
  "authors": [
    {
      "type": "author",
      "id": "https://example.com/authors/3",
      "host": "https://example.com/api",
      "displayName": "john doe",
      "bio": "beautiful weather today, huh?",
      "github": "https://github.com/johndoe",
      "profileImage": "https://example.com/images/johnscat.jpg",
      "web": "https://example.com/authors/john%20doe"
    }
  ]
}
```
---
### Get User Information of Someone Author is Following
Endpoint: `GET /author/{AUTHOR_SERIAL}/following/{FOREIGN_AUTHOR_FQID}`
Requires Authentication?: Yes

**Example Request:**
```http
GET /author/1/following/3
OR
GET /author/author%20name/following/john%20doe
```

**Example Response:**
```json
{
  "type": "author",
  "id": "https://example.com/authors/3",
  "host": "https://example.com/api",
  "displayName": "john doe",
  "bio": "beautiful weather today, huh?",
  "github": "https://github.com/johndoe",
  "profileImage": "https://example.com/images/johnscat.jpg",
  "web": "https://example.com/authors/john%20doe"
}
```
---
### Get Who's Following Author
Endpoint: `GET /author/{AUTHOR_SERIAL}/followers`
Requires Authentication?: No

**Example Request:**
```http
GET /author/3/followers
OR
GET /author/john%20doe/followers
```

**Example Response:**
```json
{
  "type": "followers",
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
### Get Author Follow Requests
Endpoint: `/authors/{AUTHOR_SERIAL}/follow_requests`
Requires Authentication?: Yes

**Example Request:**
```http
GET /authors/1/follow_requests
OR
GET /author/author%20name/follow_requests
```

**Example Response:**
```json
{
  "type": "requests",
  "requests": [
    {
      "type": "follow",
      "summary": "authors name wants to follow john doe",
      "actor": {
        "type": "author",
        "id": "https://example.com/authors/1",
        "host": "https://example.com/api",
        "displayName": "authors name",
        "bio": "authors detailed bio",
        "github": "https://github.com/authorname",
        "profileImage": "https://example.com/images/john.jpg",
        "web": "https://example.com/authors/author%20name"
      },
      "object": {
        "type": "author",
        "id": "https://example.com/authors/3",
        "host": "https://example.com/api",
        "displayName": "john doe",
        "bio": "beautiful weather today, huh?",
        "github": "https://github.com/johndoe",
        "profileImage": "https://example.com/images/johnscat.jpg",
        "web": "https://example.com/authors/john%20doe"
      }
    }
  ]
}
```
---