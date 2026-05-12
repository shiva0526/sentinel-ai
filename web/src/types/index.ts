import { LucideIcon } from "lucide-react";

export type PipelineStatus =
  | "Idle"
  | "Scanning"
  | "Extracting"
  | "Battling"
  | "Patching"
  | "Delivering"
  | "Success"
  | "Error";

export interface ScanResult {
  status: string;
  detected_threat: string;
  file_fixed: string;
  vulnerable_code: string;
  secure_patch: string;
  git_branch: string;
  pr_url?: string;
}

export interface PipelineStage {
  id: number;
  label: string;
  desc: string;
  status_key: string;
  icon: LucideIcon;
}
