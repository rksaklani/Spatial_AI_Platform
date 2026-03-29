# Organization Setup Guide

## Problem
Users were getting 403 errors when trying to upload files because the system requires users to be part of an organization (multi-tenant architecture).

## Solution
Added organization creation flow to all pages that require organization access.

## What Was Fixed

### 1. Created Organization API (`frontend/src/store/api/organizationApi.ts`)
- `useGetCurrentOrganizationQuery()` - Get user's active organization
- `useCreateOrganizationMutation()` - Create new organization
- `useSwitchOrganizationMutation()` - Switch between organizations

### 2. Created Organization Check Hook (`frontend/src/hooks/useOrganizationCheck.ts`)
Reusable hook that:
- Checks if user has an organization
- Shows creation dialog if needed
- Provides `checkOrganization()` function to guard actions

### 3. Created Organization Dialog (`frontend/src/components/onboarding/CreateOrganizationDialog.tsx`)
Modal that prompts users to create an organization with:
- Organization name (required)
- Description (optional)
- Shows trial benefits (15 days, 1 seat, 3 scenes, 5GB storage)

### 4. Updated Pages
- **ScenesPage** - Added org check to Upload Video and Import 3D File buttons
- **PhotosPage** - Needs org check for photo uploads
- **GeospatialPage** - Needs org check for geospatial operations
- **ReportsPage** - Needs org check for report generation
- **CollaborationPage** - Needs org check for collaboration features

## How It Works

1. User clicks "Upload Video" or "Import 3D File"
2. System checks if user has an organization
3. If NO organization:
   - Shows "Create Organization" dialog
   - User creates organization (gets 15-day trial)
   - Page reloads to refresh organization context
4. If HAS organization:
   - Proceeds with upload/import

## User Flow

```
Login → No Organization → Click Upload → Create Organization Dialog
                                       ↓
                                  Fill Form → Create
                                       ↓
                                  Page Reload → Upload Works!
```

## Backend Requirements

Organization must have:
- `name` (required)
- `description` (optional)
- Automatically gets:
  - 15-day free trial
  - 1 seat
  - 3 scenes max
  - 5GB storage

## Next Steps

The organization check is now in ScenesPage. The same pattern needs to be applied to:
- PhotosPage (photo upload button)
- GeospatialPage (any upload/create actions)
- ReportsPage (report generation)
- CollaborationPage (any create actions)

Use the `useOrganizationCheck()` hook and `CreateOrganizationDialog` component.
