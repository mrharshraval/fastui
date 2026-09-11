/**
 * Auto-generated Contract Type Aliases from frozen services/api OpenAPI specification.
 * DO NOT manually edit. Re-generate via openapi-typescript on openapi.json.
 */

import type { components, operations, paths } from './schema';

export type { components, operations, paths };

// Schemas / DTOs
export type Schemas = components['schemas'];

// Auth DTOs
export type RegisterRequest = Schemas['RegisterRequest'];
export type VerifyOTPRequest = Schemas['VerifyOTPRequest'];
export type LoginRequest = Schemas['LoginRequest'];
export type TokenResponse = Schemas['TokenResponse'];
export type TokenData = Schemas['TokenData'];
export type UserProfileUpdateRequest = Schemas['UserProfileUpdateRequest'];
export type PasswordUpdateRequest = Schemas['PasswordUpdateRequest'];
export type PasswordResetRequest = Schemas['PasswordResetRequest'];
export type PasswordResetConfirm = Schemas['PasswordResetConfirm'];

// Businesses DTOs
export type BusinessResponse = Schemas['BusinessResponse'];
export type BusinessUpdateRequest = Schemas['BusinessUpdateRequest'];
export type BulkDeleteRequest = Schemas['BulkDeleteRequest'];
export type BulkDeleteResponse = Schemas['BulkDeleteResponse'];

// Prospects DTOs
export type BulkQualifyRequest = Schemas['BulkQualifyRequest'];
export type BulkQualifyResponse = Schemas['BulkQualifyResponse'];
export type QualifyProspectRequest = Schemas['QualifyProspectRequest'];

// Leads DTOs
export type LeadCreateRequest = Schemas['LeadCreateRequest'];
export type BulkAddToLeadsResponse = Schemas['BulkAddToLeadsResponse'];
export type BulkStageRequest = Schemas['BulkStageRequest'];
export type BulkStageResponse = Schemas['BulkStageResponse'];

// Pipeline DTOs
export type PipelineDealResponse = Schemas['PipelineDealResponse'];

// Engagement DTOs (Activities, Reminders, Notes, Contacts, Tasks, Outreach)
export type ActivityResponse = Schemas['ActivityResponse'];
export type ActivityCreateRequest = Schemas['ActivityCreateRequest'];
export type ReminderResponse = Schemas['ReminderResponse'];
export type ReminderCreateRequest = Schemas['ReminderCreateRequest'];
export type ReminderUpdateRequest = Schemas['ReminderUpdateRequest'];
export type ContactResponse = Schemas['ContactResponse'];
export type NoteResponse = Schemas['NoteResponse'];
export type NoteCreateRequest = Schemas['NoteCreateRequest'];
export type TaskResponse = Schemas['TaskResponse'];
export type TaskCreateRequest = Schemas['TaskCreateRequest'];
export type TaskUpdateRequest = Schemas['TaskUpdateRequest'];
export type OutreachResponse = Schemas['OutreachResponse'];
export type OutreachCreateRequest = Schemas['OutreachCreateRequest'];

// Demos DTOs
export type DemoResponse = Schemas['DemoResponse'];
export type DemoCreateRequest = Schemas['DemoCreateRequest'];

// Enrichment DTOs
export type EnrichedBusinessProfile = Schemas['EnrichedBusinessProfile'];
export type EnrichmentTriggerResponse = Schemas['EnrichmentTriggerResponse'];
export type BusinessEnrichmentStatusResponse = Schemas['BusinessEnrichmentStatusResponse'];

// Discovery / Prospecting DTOs
export type ProspectingQuery = Schemas['ProspectingQuery'];
export type JobCreateResponse = Schemas['JobCreateResponse'];
export type JobStatusResponse = Schemas['JobStatusResponse'];

// Exports DTOs
export type ExportCreateRequest = Schemas['ExportCreateRequest'];
export type ExportCreateResponse = Schemas['ExportCreateResponse'];
export type ExportStatusResponse = Schemas['ExportStatusResponse'];
export type ExportType = Schemas['ExportType'];
export type ExportScope = Schemas['ExportScope'];

// Notifications DTOs
export type VapidPublicKeyResponse = Schemas['VapidPublicKeyResponse'];
export type PushSubscriptionCreate = Schemas['PushSubscriptionCreate'];
export type PushSubscriptionResponse = Schemas['PushSubscriptionResponse'];
export type TestNotificationRequest = Schemas['TestNotificationRequest'];
export type BroadcastNotificationRequest = Schemas['BroadcastNotificationRequest'];
export type BroadcastNotificationResponse = Schemas['BroadcastNotificationResponse'];

// Dashboard Stats DTOs
export type DashboardStatsResponse = Schemas['DashboardStatsResponse'];

// Validation Error
export type ValidationError = Schemas['ValidationError'];
export type HTTPValidationError = Schemas['HTTPValidationError'];
