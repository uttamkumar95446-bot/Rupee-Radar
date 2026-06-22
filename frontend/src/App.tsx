import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import UploadPage from "./pages/UploadPage";
import DashboardPage from "./pages/DashboardPage";
import TransactionsPage from "./pages/TransactionsPage";
import ErrorBoundary from "./components/ErrorBoundary";
import { ToastProvider } from "./components/ToastProvider";
import OnboardingGuide from "./components/OnboardingGuide";

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<UploadPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/transactions" element={<TransactionsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
        <OnboardingGuide />
      </ToastProvider>
    </ErrorBoundary>
  );
}
