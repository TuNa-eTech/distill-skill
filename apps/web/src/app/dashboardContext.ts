import { useOutletContext } from 'react-router'
import type { RoleOption } from '../features/dashboard/types'

export type DashboardContextValue = {
  role: string
  roleLabel: string
  roles: RoleOption[]
  roleSummary: RoleOption | null
  rolesLoading: boolean
  rolesError: string | null
}

export function useDashboardContext() {
  return useOutletContext<DashboardContextValue>()
}
