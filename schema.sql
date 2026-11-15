-- Technoverse Portal Database Schema
-- Supabase PostgreSQL with Row Level Security (RLS)

-- 1. Enable Extensions
create extension if not exists pgcrypto;

-- 2. Members Table
create table if not exists members (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  roll text unique not null,
  email text unique not null,
  branch text,
  year int,
  role text not null default 'member' check (role in ('member','secretary','treasurer','technical_lead','event_coordinator','vice_president','president','club_coordinator')),
  pw_hash text not null,
  active boolean not null default true,
  photo_path text,
  theme text not null default 'dark',
  created_at timestamptz default now(),
  last_login timestamptz
);

-- 3. Files Repository (Must be created before task_attachments, resources, and expenses)
create table if not exists files (
  id bigserial primary key,
  name text not null,
  path text not null,
  folder text not null default 'General',
  link_url text,
  size bigint,
  mime text,
  uploader uuid references members(id),
  created_at timestamptz default now()
);

-- 4. Tasks Table
create table if not exists tasks (
  id bigserial primary key,
  code int generated always as identity (start with 100), -- display #TK-100
  title text not null,
  description text,
  assigned_to uuid references members(id),
  created_by uuid references members(id),
  priority text not null default 'medium' check (priority in ('low','medium','high','urgent')),
  status text not null default 'todo' check (status in ('todo','doing','done')),
  due_at timestamptz,
  sprint text,
  event_id bigint,
  created_at timestamptz default now()
);

-- 5. Task Attachments
create table if not exists task_attachments (
  id bigserial primary key,
  task_id bigint references tasks(id) on delete cascade,
  file_id bigint references files(id) on delete cascade
);

-- 6. Events Table
create table if not exists events (
  id bigserial primary key,
  title text not null,
  category text not null,
  flagship text default 'none' check (flagship in ('none','CodeX','AI Nexus','CyberShield','DataVerse')),
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  venue text,
  quota int default 0,
  auto_waitlist boolean default true,
  description text,
  poster_path text,
  budget_total numeric default 0,
  created_by uuid references members(id),
  created_at timestamptz default now()
);

create table if not exists event_registrations (
  id bigserial primary key,
  event_id bigint references events(id) on delete cascade,
  member_id uuid references members(id) on delete cascade,
  status text not null default 'registered' check (status in ('registered','waitlist')),
  created_at timestamptz default now(),
  unique (event_id, member_id)
);

-- 7. Attendance
create table if not exists attendance (
  id bigserial primary key,
  event_id bigint references events(id) on delete cascade,
  member_id uuid references members(id) on delete cascade,
  present boolean not null default false,
  marked_by uuid references members(id),
  marked_at timestamptz default now()
);

-- 8. Learning Resources
create table if not exists resources (
  id bigserial primary key,
  title text not null,
  track text not null,
  level text not null default 'beginner' check (level in ('beginner','intermediate','advanced')),
  summary text,
  file_id bigint references files(id),
  link_url text,
  created_by uuid references members(id),
  created_at timestamptz default now()
);

-- 9. Meeting Minutes & Action Items
create table if not exists minutes (
  id bigserial primary key,
  title text not null,
  held_at timestamptz not null,
  attendees uuid[] default '{}',
  summary text,
  created_by uuid references members(id),
  created_at timestamptz default now()
);

create table if not exists action_items (
  id bigserial primary key,
  minutes_id bigint references minutes(id) on delete cascade,
  text text not null,
  assignee uuid references members(id),
  due_at timestamptz,
  task_id bigint references tasks(id)
);

-- 10. Finance (Expenses & Sponsorships)
create table if not exists expenses (
  id bigserial primary key,
  event_id bigint references events(id),
  description text not null,
  amount numeric not null default 0,
  receipt_file_id bigint references files(id),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  submitted_by uuid references members(id),
  approved_by uuid references members(id),
  created_at timestamptz default now()
);

create table if not exists sponsorships (
  id bigserial primary key,
  sponsor text not null,
  amount numeric not null default 0,
  status text not null default 'pledged' check (status in ('pledged','received')),
  event_id bigint references events(id),
  created_at timestamptz default now()
);

-- 11. Join Requests
create table if not exists join_requests (
  id bigserial primary key,
  name text not null,
  roll text unique not null,
  branch text,
  year int,
  message text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  decided_by uuid references members(id),
  created_at timestamptz default now()
);

-- 12. Announcements & Notifications
create table if not exists announcements (
  id bigserial primary key,
  body text not null,
  pinned boolean default false,
  created_by uuid references members(id),
  created_at timestamptz default now()
);

create table if not exists notifications (
  id bigserial primary key,
  member_id uuid references members(id) on delete cascade,
  text text not null,
  read boolean default false,
  created_at timestamptz default now()
);

-- 13. Settings & Activity Log
create table if not exists settings (
  key text primary key,
  value text
);

create table if not exists activity (
  id bigserial primary key,
  member_id uuid references members(id),
  member_name text,
  role text,
  action text not null,
  section text not null,
  record_id text,
  summary text,
  old_value jsonb,
  new_value jsonb,
  created_at timestamptz default now()
);

-- 14. Storage Bucket (club-files)
insert into storage.buckets (id, name, public) 
values ('club-files', 'club-files', false) 
on conflict (id) do nothing;

-- 15. Enable Row Level Security (RLS)
-- Backend accesses database via SUPABASE_SERVICE_KEY (service_role key) which bypasses RLS
alter table members enable row level security;
alter table files enable row level security;
alter table tasks enable row level security;
alter table task_attachments enable row level security;
alter table events enable row level security;
alter table event_registrations enable row level security;
alter table attendance enable row level security;
alter table resources enable row level security;
alter table minutes enable row level security;
alter table action_items enable row level security;
alter table expenses enable row level security;
alter table sponsorships enable row level security;
alter table join_requests enable row level security;
alter table announcements enable row level security;
alter table notifications enable row level security;
alter table settings enable row level security;
alter table activity enable row level security;
