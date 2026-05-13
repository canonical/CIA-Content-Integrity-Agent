export interface Site {
  id: number;
  name: string;
  base_url: string;
  sitemap_url: string;
  created_at: string | null;
  last_scanned_at: string | null;
}

export interface SitemapUrl {
  url: string;
  lastmod: string | null;
}

export type ScanStatus =
  | "pending"
  | "crawling"
  | "analyzing"
  | "suggesting"
  | "routing"
  | "complete"
  | "failed"
  | "cancelled";

export interface Scan {
  id: number;
  site_id: number;
  route_url: string;
  status: ScanStatus;
  progress: number;
  current_agent: string | null;
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
  results?: PipelineResults;
}

export interface PipelineResults {
  failures: LinkFailure[];
  page_meta: Record<string, PageMeta>;
  owners: Record<string, Owner>;
  suggestions: Record<string, FixSuggestion[]>;
  notifications: Notification[];
  audit_log: AuditLogEntry[];
}

export interface LinkFailure {
  source_page: string;
  broken_url: string;
  status_code: number | null;
  error_message: string | null;
  severity: string;
  line_number: number | null;
}

export interface PageMeta {
  url: string;
  copydoc_url: string | null;
  title: string | null;
  page_owner_email: string | null;
  last_modified: string | null;
}

export interface Owner {
  email: string;
  display_name: string;
  team: string;
  department: string;
  mattermost_username: string | null;
}

export interface FixSuggestion {
  original_url: string;
  suggested_url: string | null;
  suggestion_text: string;
  confidence: number;
  reasoning: string;
}

export interface Notification {
  recipient: Owner;
  subject: string;
  body: string;
  email_preview: string;
  action_taken: string;
  related_failures: LinkFailure[];
  suggestions: FixSuggestion[];
}

export interface AuditLogEntry {
  timestamp: string;
  agent_name: string;
  action: string;
  input_summary: string;
  output_summary: string;
  confidence: number | null;
}