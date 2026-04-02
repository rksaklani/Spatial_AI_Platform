# Backend Updates for Nira Feature Parity

This document details all backend changes made to support the new features.

## 📋 Summary of Backend Changes

### 1. Configuration Updates
**File:** `backend/utils/config.py`

**Added:**
```python
frontend_url: str = "http://localhost:5173"
```

**Purpose:** Used for generating share URLs in password-protected sharing

---

### 2. Environment Variables
**File:** `backend/.env.example`

**Added:**
```bash
BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

**Purpose:** Configure URLs for API and frontend in different environments

---

### 3. Password-Protected Sharing API
**New File:** `backend/api/protected_sharing.py`

**Endpoints:**

#### Create Protected Share
```
POST /api/v1/scenes/{scene_id}/share/protected
```
**Request Body:**
```json
{
  "password": "string",
  "expires_in_days": 7
}
```
**Response:**
```json
{
  "share_id": "uuid",
  "share_url": "https://domain.com/protected/{share_id}",
  "expires_at": "2024-01-01T00:00:00Z"
}
```

#### Access Protected Share
```
POST /api/v1/protected-shares/{share_id}/access
```
**Request Body:**
```json
{
  "password": "string"
}
```
**Response:**
```json
{
  "scene_id": "string",
  "scene_name": "string",
  "access_granted": true
}
```

#### Revoke Protected Share
```
DELETE /api/v1/protected-shares/{share_id}
```

#### List Protected Shares
```
GET /api/v1/protected-shares/scene/{scene_id}
```

**Features:**
- SHA-256 password hashing
- Expiration date enforcement
- Access tracking (count and timestamp)
- Failed attempt logging
- Organization-level access control

**Database Collection:**
```javascript
db.protected_shares {
  _id: "share_id",
  scene_id: "string",
  organization_id: "string",
  created_by: "user_id",
  password_hash: "sha256_hash",
  created_at: "datetime",
  expires_at: "datetime",
  access_count: 0,
  failed_attempts: 0,
  last_accessed_at: "datetime"
}
```

---

### 4. Annotation API Enhancements
**File:** `backend/api/annotations.py`

**New Functions:**

#### Slope Calculation
```python
def calculate_slope(p1: Position3D, p2: Position3D) -> dict:
    """
    Calculate slope between two 3D points.
    
    Returns:
        {
            "slope_percent": float,
            "slope_degrees": float,
            "horizontal_distance": float,
            "vertical_distance": float
        }
    """
```

**Formula:**
- Horizontal distance: `sqrt((x2-x1)² + (y2-y1)²)`
- Vertical distance: `z2 - z1`
- Slope %: `(vertical / horizontal) × 100`
- Slope °: `atan(vertical / horizontal) × 180/π`

#### Volume Calculation
```python
def calculate_volume(points: List[Position3D]) -> dict:
    """
    Calculate volume using bounding box method.
    
    Returns:
        {
            "volume": float,
            "width": float,
            "depth": float,
            "height": float
        }
    """
```

**Formula:**
- Width: `max(x) - min(x)`
- Depth: `max(y) - min(y)`
- Height: `max(z) - min(z)`
- Volume: `width × depth × height`

**Updated Endpoint:**
```
POST /api/v1/scenes/{scene_id}/annotations
```

Now supports `measurement_type`:
- `"distance"` - existing
- `"area"` - existing
- `"slope"` - NEW
- `"volume"` - NEW

**Example Request for Slope:**
```json
{
  "annotation_type": "measurement",
  "position": {"x": 0, "y": 0, "z": 0},
  "content": "Slope measurement",
  "measurement_data": {
    "measurement_type": "slope",
    "value": 0,
    "unit": "%",
    "points": [
      {"x": 0, "y": 0, "z": 0},
      {"x": 10, "y": 0, "z": 2}
    ]
  }
}
```

**Example Response:**
```json
{
  "annotation_id": "uuid",
  "measurement_data": {
    "measurement_type": "slope",
    "value": 20.0,
    "unit": "%",
    "points": [...]
  },
  "metadata": {
    "slope_percent": 20.0,
    "slope_degrees": 11.31,
    "horizontal_distance": 10.0,
    "vertical_distance": 2.0
  }
}
```

**Example Request for Volume:**
```json
{
  "annotation_type": "measurement",
  "position": {"x": 0, "y": 0, "z": 0},
  "content": "Volume measurement",
  "measurement_data": {
    "measur