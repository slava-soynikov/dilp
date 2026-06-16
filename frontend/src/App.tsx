import { Navigate, Route, Routes } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import VerifyEmailPage from "./pages/VerifyEmailPage";
import DashboardPage from "./pages/DashboardPage";
import ProfilePage from "./pages/ProfilePage";
import ChildrenPage from "./pages/ChildrenPage";
import AdminPage from "./pages/AdminPage";
import ProgrammesPage from "./pages/ProgrammesPage";
import LessonContentPage from "./pages/LessonContentPage";
import LessonViewerPage from "./pages/LessonViewerPage";
import CurriculumPage from "./pages/CurriculumPage";
import GroupsPage from "./pages/GroupsPage";
import OrganizationPage from "./pages/OrganizationPage";
import LogsPage from "./pages/LogsPage";
import ReportsPage from "./pages/ReportsPage";
import ParentDashboardPage from "./pages/ParentDashboardPage";
import { RequireAuth } from "./auth/RequireAuth";
import { RequireRole } from "./auth/RequireRole";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />

      <Route
        path="/"
        element={
          <RequireAuth>
            <DashboardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        }
      />
      <Route
        path="/children"
        element={
          <RequireAuth>
            <RequireRole role="parent">
              <ChildrenPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/admin"
        element={
          <RequireAuth>
            <RequireRole role="admin">
              <AdminPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/organization"
        element={
          <RequireAuth>
            <RequireRole role="admin">
              <OrganizationPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/groups"
        element={
          <RequireAuth>
            <GroupsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/programmes"
        element={
          <RequireAuth>
            <ProgrammesPage />
          </RequireAuth>
        }
      />
      <Route
        path="/lesson-contents"
        element={
          <RequireAuth>
            <LessonContentPage />
          </RequireAuth>
        }
      />
      <Route
        path="/curriculum"
        element={
          <RequireAuth>
            <RequireRole role="child">
              <CurriculumPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/lessons/:id"
        element={
          <RequireAuth>
            <LessonViewerPage />
          </RequireAuth>
        }
      />

      <Route
        path="/logs"
        element={
          <RequireAuth>
            <RequireRole anyOf={["admin", "auditor"]}>
              <LogsPage />
            </RequireRole>
          </RequireAuth>
        }
      />

      <Route
        path="/reports"
        element={
          <RequireAuth>
            <RequireRole anyOf={["admin", "auditor", "teacher"]}>
              <ReportsPage />
            </RequireRole>
          </RequireAuth>
        }
      />

      <Route
        path="/parent-dashboard"
        element={
          <RequireAuth>
            <RequireRole role="parent">
              <ParentDashboardPage />
            </RequireRole>
          </RequireAuth>
        }
      />
      <Route
        path="/parent-dashboard/:childId"
        element={
          <RequireAuth>
            <RequireRole role="parent">
              <ParentDashboardPage />
            </RequireRole>
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}