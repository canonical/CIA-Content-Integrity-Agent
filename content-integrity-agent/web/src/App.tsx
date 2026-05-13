import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./components/Layout";
import { SitesPage } from "./pages/SitesPage";
import { SitemapPage } from "./pages/SitemapPage";
import { ScanResultsPage } from "./pages/ScanResultsPage";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<SitesPage />} />
            <Route path="/sites/:siteId" element={<SitemapPage />} />
            <Route path="/scans/:scanId" element={<ScanResultsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}