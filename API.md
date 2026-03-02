# API Documentation

**Base URL**: `/api`  
**API Format**:  `json`  
**Authentication**: Django user account.  
**Test**: [Click here to jump to tests.](lightskyblue/socialdistribution/api/tests.py)  
**Note**: Some application functionality has not yet
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
# Yet to be augmented API
As per linked doc: [lightskyblue/socialdistribution/views/html_views.py](lightskyblue/socialdistribution/views/html_views.py)  
```
Endpoints:
-------------------------------------------------
- `GET /` (`feed`): main timeline; use for browsing posts.
  Request: none. Response: `my_author: Author`, `entries: QuerySet[Entry]`.
  Examples: `GET /`, refresh `GET /` after posting.

- `GET /authors/` (`authors_list`): browse local authors.
  Query: `q: str` (ex `"har"`) for username filtering.
  Response: `authors: QuerySet[Author]`, `my_author: Author`.
  Examples: `GET /authors/`, `GET /authors/?q=chris`.

- `POST /authors/<author_id>/follow/` and `/unfollow/`:
  follow/unfollow local authors; do not use for self or remote authors.
  Path: `author_id: int` (ex `12`). Response: `302` redirect.
  Examples: `POST /authors/12/follow/`, `POST /authors/12/unfollow/`.

- `GET /follow-requests/`, `POST /follow-requests/<request_id>/handle/`:
  review and handle follow requests.
  Path: `request_id: int` (ex `7`), Form: `action: str` (`accept|reject`).
  Response: list template or `302` redirect.
  Examples: `GET /follow-requests/`, `POST ... action=accept`.

- `GET /author/<username>/`, `/authors/<author_id>/(followers|following|friends)/`:
  view profile and social graph.
  Path: `username: str` or `author_id: int`.
  Response includes author objects and count/list context fields.
  Examples: `GET /author/harneetk/`, `GET /authors/12/friends/`.

- `GET|POST /profile/edit/`:
  edit current user profile only.
  Form: `display_name: str`, `bio: str`, `picture_url: url`, `github_url: url`.
  Response: form template or `302` redirect to own profile.
  Examples: `GET /profile/edit/`, `POST /profile/edit/`.

- `GET /entries/`, `GET|POST /entries/new/`,
  `GET /authors/<author_id>/entries/`, `GET /entries/<entry_id>/`:
  list own entries, create entries, view author entries, view one entry.
  Paths: `author_id: int`, `entry_id: int`.
  Create form: `title: str`, `content: str`, `image_url: url`,
  `visibility: str`, `content_type: str`.
  Examples: `GET /entries/`, `POST /entries/new/`, `GET /entries/33/`.

- `GET|POST /entries/<entry_id>/edit/` and `/delete/`:
  owner-only edit/delete operations.
  Path: `entry_id: int`; delete form optional `next: str`.
  Response: form/confirm template or `302` redirect.
  Examples: `GET /entries/33/edit/`, `POST /entries/33/delete/`.

- `POST /entries/<entry_id>/comment/`, `/entries/<entry_id>/like/`,
  `/comments/<comment_id>/like/`:
  comment/like toggles on accessible content.
  Paths: `entry_id: int`, `comment_id: int`.
  Form: `content: str` (comment), optional `next: str` (redirect target).
  Response: `302` redirect.
  Examples: `POST /entries/33/comment/`, `POST /entries/33/like/`.

Note:
- `home(request)` exists but root URL is currently wired to `feed`.
```