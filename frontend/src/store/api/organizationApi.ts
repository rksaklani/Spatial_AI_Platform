/**
 * Organization API endpoints using RTK Query
 * Requirements: 2.2, 2.3
 */

import { baseApi } from './baseApi';

interface Organization {
  id: string;
  name: string;
  created_at: string;
}

export const organizationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get all organizations for current user
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

    // Switch organization
    switchOrganization: builder.mutation<void, string>({
      query: (organizationId) => ({
        url: `/organizations/${organizationId}/switch`,
        method: 'POST',
      }),
      invalidatesTags: [
        { type: 'Scene', id: 'LIST' },
        { type: 'Organization', id: 'LIST' },
      ],
    }),
  }),
});

export const {
  useGetOrganizationsQuery,
  useSwitchOrganizationMutation,
} = organizationApi;
