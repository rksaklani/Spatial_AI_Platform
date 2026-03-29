/**
 * Organization API endpoints using RTK Query
 */

import { baseApi } from './baseApi';

export interface Organization {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  subscription_tier: string;
  max_seats: number;
  max_scenes: number;
  max_storage_gb: number;
  trial_expires_at?: string;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateOrganizationRequest {
  name: string;
  description?: string;
}

export interface UpdateOrganizationRequest {
  name?: string;
  description?: string;
}

export const organizationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get current user's active organization
    getCurrentOrganization: builder.query<Organization | null, void>({
      query: () => '/organizations/me/current',
      providesTags: ['Organization'],
    }),

    // List all organizations user is a member of
    getOrganizations: builder.query<Organization[], void>({
      query: () => '/organizations',
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Organization' as const, id })),
              { type: 'Organization', id: 'LIST' },
            ]
          : [{ type: 'Organization', id: 'LIST' }],
    }),

    // Get organization by ID
    getOrganizationById: builder.query<Organization, string>({
      query: (id) => `/organizations/${id}`,
      providesTags: (_result, _error, id) => [{ type: 'Organization', id }],
    }),

    // Create new organization
    createOrganization: builder.mutation<Organization, CreateOrganizationRequest>({
      query: (data) => ({
        url: '/organizations',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Organization', id: 'LIST' }, 'Organization'],
    }),

    // Update organization
    updateOrganization: builder.mutation<
      Organization,
      { id: string; data: UpdateOrganizationRequest }
    >({
      query: ({ id, data }) => ({
        url: `/organizations/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Organization', id },
        { type: 'Organization', id: 'LIST' },
      ],
    }),

    // Delete organization
    deleteOrganization: builder.mutation<void, string>({
      query: (id) => ({
        url: `/organizations/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Organization', id: 'LIST' }],
    }),

    // Switch active organization
    switchOrganization: builder.mutation<Organization, string>({
      query: (id) => ({
        url: `/organizations/me/switch/${id}`,
        method: 'POST',
      }),
      invalidatesTags: ['Organization'],
    }),
  }),
});

export const {
  useGetCurrentOrganizationQuery,
  useGetOrganizationsQuery,
  useGetOrganizationByIdQuery,
  useCreateOrganizationMutation,
  useUpdateOrganizationMutation,
  useDeleteOrganizationMutation,
  useSwitchOrganizationMutation,
} = organizationApi;
