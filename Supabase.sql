-- Enable pgcrypto extension for UUID generation
create extension IF not exists "pgcrypto";

-- Create the chat_logs table
create table if not exists public.chat_logs (
  id BIGSERIAL primary key,
  conversation_id UUID default gen_random_uuid () not null, -- To group messages into conversations
  email TEXT not null, -- Mandatory user email address
  user_id TEXT not null,
  user_message TEXT not null, -- User's message (supports lengthy text)
  chatbot_reply TEXT not null, -- AI response text
  response_time NUMERIC(5, 2) not null, -- Response time in seconds
  timestamp TIMESTAMPTZ not null default now(), -- Timestamp for each record
  sentiment_label TEXT, -- e.g., 'positive', 'neutral', 'negative'
  sentiment_score NUMERIC(3, 2), -- Sentiment score (-1.00 to 1.00)
  drop_off BOOLEAN default false, -- Indicates if the user dropped the conversation
  message_length INTEGER, -- Calculated length of the user message
  scraped_data JSONB -- Optional scraped data stored as JSONB
);

-- Indexes for high performance queries:
-- Index on timestamp to help filter/sort by time.
create index IF not exists idx_chat_logs_timestamp on public.chat_logs (timestamp);

-- Index on email to quickly locate records for a specific user.
create index IF not exists idx_chat_logs_email on public.chat_logs (email);

-- Composite index on email and timestamp for efficient retrieval of conversation history sorted by time.
create index IF not exists idx_chat_logs_email_timestamp on public.chat_logs (email, timestamp);

-- Indexes on other fields as needed
create index IF not exists idx_chat_logs_user on public.chat_logs (user_id);

create index IF not exists idx_chat_logs_conversation_id on public.chat_logs (conversation_id);

create index IF not exists idx_chat_logs_sentiment_score on public.chat_logs (sentiment_score);

create index IF not exists idx_chat_logs_drop_off on public.chat_logs (drop_off);

alter table public.chat_logs
add column if not exists scraped_data JSONB;
