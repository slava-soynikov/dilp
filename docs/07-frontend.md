# Frontend

React 18 + Vite + FluentUI. Source lives under [`frontend/src`](../frontend/src).

## Directory Layout

```
src/
  App.tsx              ← route table
  main.tsx             ← React root + providers
  auth/
    AuthContext.tsx    ← tokens, current user, login/logout
    RequireAuth.tsx    ← redirects to /login when missing
    RequireRole.tsx    ← role-gated route wrapper
    tokenStore.ts      ← localStorage tokens
  api/
    client.ts          ← fetch wrapper (refresh on 401, error parsing)
    auth.ts | users.ts | children.ts | parents.ts |
    consents.ts | tenants.ts | groups.ts | programmes.ts |
    logs.ts | reports.ts
  components/
    AppShell.tsx       ← layout with nav
    AuthLayout.tsx     ← layout for unauthenticated pages
    FormField.tsx
    ConfirmDialog.tsx
    PinDisplayDialog.tsx
  pages/
    LoginPage.tsx      RegisterPage.tsx
    ForgotPasswordPage.tsx  ResetPasswordPage.tsx
    DashboardPage.tsx  ProfilePage.tsx
    ChildrenPage.tsx
    GroupsPage.tsx
    ProgrammesPage.tsx
    CurriculumPage.tsx       ← child curriculum view
    LessonContentPage.tsx    ← teacher/admin: CMS content + file attachments
    LessonViewerPage.tsx     ← child/anyone: renders Mini-CMS content + "Join meeting" button if meeting_url is set
    OrganizationPage.tsx     ← admin: tenants / schools
    AdminPage.tsx            ← admin: teacher invites
    LogsPage.tsx             ← admin/auditor: activity + audit logs
    ReportsPage.tsx          ← admin/auditor/teacher: Sprint 7 reports
    ParentDashboardPage.tsx  ← parent: per-child progress dashboard
  i18n/
    ru.ts              ← Russian strings (current default and only locale; the UI was switched from German in commit 2762e50)
```

## Routing

Defined in `App.tsx`. High level:

| Path | Wrapper | Notes |
|------|---------|-------|
| `/login`, `/register`, `/forgot-password`, `/reset-password` | `AuthLayout` | Public. |
| `/` | `RequireAuth` | Dashboard, role-aware content. |
| `/profile` | `RequireAuth` | Edit own profile. |
| `/children` | `RequireRole("parent")` | Manage children, see PINs. |
| `/groups` | `RequireRole("teacher","admin")` | Group + member management. |
| `/programmes` | `RequireRole("admin","teacher")` | CRUD programmes/modules/lessons. |
| `/curriculum` | `RequireRole("child")` | Child curriculum tree. |
| `/lessons/:id` | `RequireAuth` | Lesson viewer: renders Mini-CMS Markdown body, lists file attachments for download, and shows a "Join meeting" button if `meeting_url` is set on the lesson. |
| `/lesson-contents` | `RequireRole("admin","teacher")` | CMS editor: create/edit lesson Markdown bodies, manage file attachments. |
| `/organization` | `RequireRole("admin")` | Tenant + school management. |
| `/admin` | `RequireRole("admin")` | Invite teachers. |
| `/logs` | `RequireRole("admin","auditor")` | Activity + audit log viewer with tabs and filters. |
| `/reports` | `RequireRole(anyOf=["admin","auditor","teacher"])` | Sprint 7 reports: global tab (active users + activity overview, admin/auditor only) and drill-down tab (group progress + programme funnel; teachers see only their own scope). |
| `/parent-dashboard`, `/parent-dashboard/:childId` | `RequireRole("parent")` | Per-child programme/module summary with completion bars; switches between the parent's children. 404 from the API surfaces as "child not found". |

`RequireRole` accepts any number of role names and admits the user if they hold at least one. Used for routes that should be visible to multiple roles (e.g. `/logs` for both admin and auditor).

## API Client

`api/client.ts` exposes a single `api<T>(path, opts)` helper:

- Injects the access token from `tokenStore`.
- On `401`, attempts one silent refresh via `/auth/refresh` and retries.
- Parses `{ detail }` errors into thrown `ApiError` instances.

Per-domain modules wrap it with typed signatures, e.g.:

```ts
// api/programmes.ts
export const programmesApi = {
  list: () => api<Programme[]>("/programmes"),
  create: (body: ProgrammeCreate) => api<Programme>("/programmes", { method: "POST", body }),
  ...
};
```

## Auth Context

`AuthContext` exposes:

- `user`, `roles`, `isLoading`
- `login(email, password)` / `logout()`
- automatic bootstrap from localStorage on mount

Components consume it via `useAuth()`.

## Internationalisation

`i18n/ru.ts` holds Russian strings keyed by namespace and is the single locale shipped today. The codebase is structured to add more locales (English, Ukrainian) without changes to components — pages import a single `t` object, which can later be wrapped in a runtime locale switch.

## UI Conventions

- FluentUI v9 components (`Button`, `Input`, `Dialog`, `Combobox` …).
- Page-level state lives in the page component; complex flows extract local hooks.
- All destructive actions go through `ConfirmDialog`.
- Child PINs surface exactly once through `PinDisplayDialog` after creation.

## What's Missing

- No frontend unit/E2E test runner is configured yet (planned for Sprint 9).
- Reporting dashboards await Sprint 7.