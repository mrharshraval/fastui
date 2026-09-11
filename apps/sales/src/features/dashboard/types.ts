export interface StatsModel {
  total_leads?: number;
  pipeline_value?: number;
  active_companies?: number;
  conversion_rate?: number;
}

export interface FollowUpAction {
  id: string;
  contactName: string;
  company: string;
  lastInteraction: string;
  nextAction: string;
  dueDate: string;
  bucket: "overdue" | "due_today" | "upcoming" | "waiting" | "inactive";
  done: boolean;
  dealValue?: string;
}

export interface ActivityFeedModel {
  id: string;
  action: string;
  type: "calls" | "emails";
  lead: string;
  company: string;
  time: string;
}
