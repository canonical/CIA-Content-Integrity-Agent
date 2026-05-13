import { useState } from "react";

interface Props {
  onSubmit: (data: { name: string; base_url: string; sitemap_url: string }) => void;
  onClose: () => void;
}

export function AddSiteModal({ onSubmit, onClose }: Props) {
  const [name, setName] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [sitemapUrl, setSitemapUrl] = useState("");

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4">Add Site</h2>
        <form onSubmit={(e) => { e.preventDefault(); onSubmit({ name, base_url: baseUrl.replace(/\/+$/, ""), sitemap_url: sitemapUrl || `${baseUrl.replace(/\/+$/, "")}/sitemap.xml` }); }} className="flex flex-col gap-3">
          <input className="border rounded px-3 py-2 text-sm" placeholder="Site name" value={name} onChange={(e) => setName(e.target.value)} required />
          <input className="border rounded px-3 py-2 text-sm" placeholder="Base URL (e.g. https://canonical.com)" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} required />
          <input className="border rounded px-3 py-2 text-sm" placeholder="Sitemap URL (auto-filled from base URL)" value={sitemapUrl} onChange={(e) => setSitemapUrl(e.target.value)} />
          <div className="flex justify-end gap-2 mt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">Add Site</button>
          </div>
        </form>
      </div>
    </div>
  );
}