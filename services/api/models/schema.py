import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    JSON,
    ForeignKey,
    Boolean,
    Text,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from models.database import Base

def utc_now():
    return datetime.now(timezone.utc)

# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SALES = "sales"
    VIEWER = "viewer"

class PipelineStage(str, enum.Enum):
    LEAD = "lead"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"

class WebsiteStatus(str, enum.Enum):
    UNKNOWN = "unknown"
    WEBSITE_FOUND = "website_found"
    NO_WEBSITE = "no_website"

class LeadPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class LeadSignal(str, enum.Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OutreachChannel(str, enum.Enum):
    CALL = "call"
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class OutreachStatus(str, enum.Enum):
    INITIATED = "initiated"
    CONNECTED = "connected"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    SENT = "sent"
    DELIVERED = "delivered"
    REPLIED = "replied"
    BOUNCED = "bounced"
    FAILED = "failed"

class InteractionType(str, enum.Enum):
    CALL_CONVERSATION = "call_conversation"
    WHATSAPP_CHAT = "whatsapp_chat"
    EMAIL_THREAD = "email_thread"
    MEETING = "meeting"
    DEMO = "demo"

class ActivityType(str, enum.Enum):
    BUSINESS_DISCOVERED = "business_discovered"
    LEAD_CREATED = "lead_created"
    WEBSITE_VISITED = "website_visited"
    CALL_INITIATED = "call_initiated"
    WHATSAPP_OPENED = "whatsapp_opened"
    EMAIL_INITIATED = "email_initiated"
    INTERACTION_LOGGED = "interaction_logged"
    NOTE_ADDED = "note_added"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    REMINDER_CREATED = "reminder_created"
    REMINDER_COMPLETED = "reminder_completed"
    STATUS_CHANGED = "status_changed"
    PROPOSAL_SENT = "proposal_sent"

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExportStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# ─────────────────────────────────────────────────────────────
# 1. USER MODEL
# ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.SALES, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    verification_otp = Column(String(32), nullable=True)
    verification_otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    assigned_leads = relationship("Lead", back_populates="owner")
    notes = relationship("Note", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    outreaches = relationship("Outreach", back_populates="user")
    interactions = relationship("Interaction", back_populates="user")
    activities = relationship("Activity", back_populates="user")

# ─────────────────────────────────────────────────────────────
# 2. BUSINESS MODEL (Discovered Company Master Entity)
# ─────────────────────────────────────────────────────────────

class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), index=True, nullable=False) # Clean display name
    raw_business_name = Column(String(500), nullable=True)          # Exact untouched scraped name
    normalized_business_name = Column(String(255), index=True, nullable=True) # Canonical search key
    category = Column(String(255), index=True, nullable=True)
    
    # Normalization & Deduplication signals
    normalized_phone = Column(String(64), index=True, nullable=True)
    normalized_website = Column(String(255), index=True, nullable=True)
    
    # Location & Contact Information
    address = Column(String(500), nullable=True)
    city = Column(String(100), index=True, nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(32), nullable=True)
    
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    has_whatsapp = Column(Boolean, default=False, nullable=False)
    website_status = Column(Enum(WebsiteStatus), default=WebsiteStatus.UNKNOWN, index=True, nullable=False)
    
    # Contact tracking semantics & Prospect Qualification
    source_platform = Column(String(100), default="discover", nullable=True)
    qualification_status = Column(String(50), default="unqualified", index=True, nullable=False) # "unqualified", "reviewing", "qualified", "disqualified"
    last_outreach_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_contacted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    lead_profile = relationship("Lead", back_populates="business", uselist=False, cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="business", cascade="all, delete-orphan")
    sources = relationship("BusinessSource", back_populates="business", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="business", cascade="all, delete-orphan", order_by="desc(Note.created_at)")
    tasks = relationship("Task", back_populates="business", cascade="all, delete-orphan", order_by="asc(Task.due_date)")
    reminders = relationship("Reminder", back_populates="business", cascade="all, delete-orphan", order_by="asc(Reminder.due_at)")
    outreaches = relationship("Outreach", back_populates="business", cascade="all, delete-orphan", order_by="desc(Outreach.attempted_at)")
    interactions = relationship("Interaction", back_populates="business", cascade="all, delete-orphan", order_by="desc(Interaction.occurred_at)")
    activities = relationship("Activity", back_populates="business", cascade="all, delete-orphan", order_by="desc(Activity.created_at)")

# ─────────────────────────────────────────────────────────────
# 3. LEAD MODEL (Sales Prospect State & Pipeline Qualification)
# ─────────────────────────────────────────────────────────────

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    stage = Column(Enum(PipelineStage), default=PipelineStage.LEAD, nullable=False, index=True)
    priority = Column(Enum(LeadPriority), default=LeadPriority.MEDIUM, nullable=False, index=True)
    signal = Column(Enum(LeadSignal), default=LeadSignal.WARM, nullable=False, index=True)
    score = Column(Integer, default=50, nullable=False)
    source = Column(String(100), default="discover", nullable=False) # e.g. "discover", "import", "manual"
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="lead_profile")
    owner = relationship("User", back_populates="assigned_leads")

# ─────────────────────────────────────────────────────────────
# 4. CONTACT MODEL (Associated People)
# ─────────────────────────────────────────────────────────────

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True) # e.g. "Owner", "Manager", "Receptionist"
    is_decision_maker = Column(Boolean, default=False, nullable=False)
    
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(64), nullable=True)
    normalized_phone = Column(String(64), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="contacts")
    notes = relationship("Note", back_populates="contact")
    tasks = relationship("Task", back_populates="contact")
    reminders = relationship("Reminder", back_populates="contact")
    outreaches = relationship("Outreach", back_populates="contact")
    interactions = relationship("Interaction", back_populates="contact")
    activities = relationship("Activity", back_populates="contact")

# ─────────────────────────────────────────────────────────────
# 5. BUSINESS SOURCE MODEL (Multi-Source Provenance)
# ─────────────────────────────────────────────────────────────

class BusinessSource(Base):
    __tablename__ = "business_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    discovery_job_id = Column(Integer, ForeignKey("discovery_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    
    platform = Column(String(100), nullable=False, index=True) # e.g. "google_maps", "yelp", "website", "manual"
    source_url = Column(String(500), nullable=True)
    external_id = Column(String(255), nullable=True, index=True) # Unique ID from scraping source (e.g. Google Place ID)
    raw_payload = Column(JSON, nullable=True)
    
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_business_source_platform_external_id"),
        Index("ix_business_sources_business_platform", "business_id", "platform"),
    )

    # Relationships
    business = relationship("Business", back_populates="sources")
    discovery_job = relationship("DiscoveryJob", back_populates="sources")

# ─────────────────────────────────────────────────────────────
# 6. NOTE MODEL (Dedicated User Notes)
# ─────────────────────────────────────────────────────────────

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="notes")
    contact = relationship("Contact", back_populates="notes")
    user = relationship("User", back_populates="notes")

# ─────────────────────────────────────────────────────────────
# 7. TASK MODEL (Actionable Work To-Dos)
# ─────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(LeadPriority), default=LeadPriority.MEDIUM, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="tasks")
    contact = relationship("Contact", back_populates="tasks")
    user = relationship("User", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task")

# ─────────────────────────────────────────────────────────────
# 8. REMINDER MODEL (Time-based Notification Trigger)
# ─────────────────────────────────────────────────────────────

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="reminders")
    contact = relationship("Contact", back_populates="reminders")
    user = relationship("User", back_populates="reminders")
    task = relationship("Task", back_populates="reminders")

# ─────────────────────────────────────────────────────────────
# 9. OUTREACH MODEL (Outbound Attempts: Call / WhatsApp / Email)
# ─────────────────────────────────────────────────────────────

class Outreach(Base):
    __tablename__ = "outreaches"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    channel = Column(Enum(OutreachChannel), nullable=False, index=True)
    status = Column(Enum(OutreachStatus), default=OutreachStatus.INITIATED, nullable=False, index=True)
    recipient = Column(String(255), nullable=False) # target phone, email, or whatsapp
    subject = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    attempted_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="outreaches")
    contact = relationship("Contact", back_populates="outreaches")
    user = relationship("User", back_populates="outreaches")
    interactions = relationship("Interaction", back_populates="outreach")

# ─────────────────────────────────────────────────────────────
# 10. INTERACTION MODEL (Two-Way Engagement & Conversation)
# ─────────────────────────────────────────────────────────────

class Interaction(Base):
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    outreach_id = Column(Integer, ForeignKey("outreaches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    type = Column(Enum(InteractionType), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True) # for calls / meetings
    summary = Column(Text, nullable=True)
    outcome = Column(String(255), nullable=True)
    sentiment = Column(String(50), nullable=True) # e.g. "positive", "neutral", "negative"
    occurred_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="interactions")
    contact = relationship("Contact", back_populates="interactions")
    user = relationship("User", back_populates="interactions")
    outreach = relationship("Outreach", back_populates="interactions")

# ─────────────────────────────────────────────────────────────
# 11. ACTIVITY MODEL (Chronological Audit Log / Timeline)
# ─────────────────────────────────────────────────────────────

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    type = Column(Enum(ActivityType), nullable=False, index=True)
    channel = Column(String(50), nullable=True) # e.g. "call", "whatsapp", "email", "website", "note", "crm"
    outcome = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Generic entity reference for audit traceability without polymorphic bloat
    entity_type = Column(String(50), nullable=True, index=True) # "outreach", "interaction", "note", "task", "reminder", "lead"
    entity_id = Column(Integer, nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="activities")
    user = relationship("User", back_populates="activities")
    contact = relationship("Contact", back_populates="activities")

# ─────────────────────────────────────────────────────────────
# 12. DISCOVERY & EXPORT JOB MODELS
# ─────────────────────────────────────────────────────────────

class DiscoveryJob(Base):
    __tablename__ = "discovery_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    query = Column(JSON, nullable=False)
    
    # Progress metrics
    progress_percent = Column(Integer, default=0, nullable=False)
    total_discovered = Column(Integer, default=0, nullable=False)
    total_processed = Column(Integer, default=0, nullable=False)
    new_leads = Column(Integer, default=0, nullable=False)
    existing_businesses = Column(Integer, default=0, nullable=False)
    duplicates = Column(Integer, default=0, nullable=False)
    skipped = Column(Integer, default=0, nullable=False)
    errors = Column(Integer, default=0, nullable=False)
    
    error_message = Column(String(500), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    sources = relationship("BusinessSource", back_populates="discovery_job")

class ExportJob(Base):
    __tablename__ = "export_jobs"
    
    id = Column(String(36), primary_key=True, index=True) # UUID string
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(ExportStatus), default=ExportStatus.QUEUED, nullable=False, index=True)
    progress_percent = Column(Integer, default=0, nullable=False)
    records_processed = Column(Integer, default=0, nullable=False)
    total_records = Column(Integer, default=0, nullable=False)
    download_url = Column(String(500), nullable=True)
    error_message = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
