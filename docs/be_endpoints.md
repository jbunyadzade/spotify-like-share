# API Endpoints Documentation

## Endpoints Overview

---

### `/api/login`

**Method:** GET  
**Description:** Redirects the user to Spotify's OAuth authorization page.  
**Input:** None  
**Output:** Redirect to Spotify authorization URL

---

### `/api/callback`

**Method:** GET  
**Description:** Handles the callback from Spotify after user authentication. Retrieves an authorization code, exchanges it for an access token, and creates a JWT token stored in an HTTP-only cookie.
**Input:**

-   Query parameter `code`: Authorization code from Spotify

**Output:**

-   HTTP Redirect to `/home`
-   Sets an HTTP-only JWT cookie

---

### `/api/sync`

**Method:** POST  
**Description:** Syncs the user's liked songs from Spotify to a public playlist named "Public Likes." If the playlist does not exist, it is created.  
**Input:**

-   JWT token (from HTTP-only cookie)

**Output:**

-   `200 OK`: JSON message confirming sync success
-   `401 Unauthorized`: JSON error message if JWT is missing, expired, or invalid
-   `404 Not Found`: JSON error if user token info is not found
-   `500 Internal Server Error`: JSON error if track addition fails

**Example Responses:**

```json
{
    "message": "Liked songs have been synced to 'Public Likes'.",
    "playlist_id": "playlist123456"
}
```

```json
{
    "error": "JWT token not found in cookies"
}
```
