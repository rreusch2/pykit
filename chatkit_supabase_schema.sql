-- ChatKit Tables for Supabase
-- Run this in your Supabase SQL Editor
-- Compatible with existing Predictive Play database structure

-- DROP existing tables if they exist (clean slate)
DROP TABLE IF EXISTS chatkit_attachments CASCADE;
DROP TABLE IF EXISTS chatkit_thread_items CASCADE;
DROP TABLE IF EXISTS chatkit_threads CASCADE;

-- Threads table
CREATE TABLE chatkit_threads (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Thread items (messages, widgets, tool calls, etc.)
CREATE TABLE chatkit_thread_items (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES chatkit_threads(id) ON DELETE CASCADE,
    item_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE
);

-- Attachments
CREATE TABLE chatkit_attachments (
    id TEXT PRIMARY KEY,
    thread_id TEXT REFERENCES chatkit_threads(id) ON DELETE CASCADE,
    attachment_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chatkit_threads_profile_id ON chatkit_threads(profile_id);
CREATE INDEX IF NOT EXISTS idx_chatkit_threads_created_at ON chatkit_threads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chatkit_thread_items_thread_id ON chatkit_thread_items(thread_id);
CREATE INDEX IF NOT EXISTS idx_chatkit_thread_items_created_at ON chatkit_thread_items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chatkit_attachments_thread_id ON chatkit_attachments(thread_id);

-- Row Level Security (RLS) Policies
ALTER TABLE chatkit_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatkit_thread_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatkit_attachments ENABLE ROW LEVEL SECURITY;

-- Threads policies
CREATE POLICY "Users can view own threads" ON chatkit_threads
    FOR SELECT USING (auth.uid() = profile_id);

CREATE POLICY "Users can insert own threads" ON chatkit_threads
    FOR INSERT WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "Users can update own threads" ON chatkit_threads
    FOR UPDATE USING (auth.uid() = profile_id);

CREATE POLICY "Users can delete own threads" ON chatkit_threads
    FOR DELETE USING (auth.uid() = profile_id);

-- Users can only access thread items in their threads
CREATE POLICY "Users can view own thread items" ON chatkit_thread_items
    FOR SELECT USING (auth.uid() = profile_id);

CREATE POLICY "Users can insert own thread items" ON chatkit_thread_items
    FOR INSERT WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "Users can update own thread items" ON chatkit_thread_items
    FOR UPDATE USING (auth.uid() = profile_id);

CREATE POLICY "Users can delete own thread items" ON chatkit_thread_items
    FOR DELETE USING (auth.uid() = profile_id);

-- Users can only access their own attachments
CREATE POLICY "Users can view own attachments" ON chatkit_attachments
    FOR SELECT USING (auth.uid() = profile_id);

CREATE POLICY "Users can insert own attachments" ON chatkit_attachments
    FOR INSERT WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "Users can delete own attachments" ON chatkit_attachments
    FOR DELETE USING (auth.uid() = profile_id);

-- Service role bypass (for server operations)
CREATE POLICY "Service role can manage all threads" ON chatkit_threads
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Service role can manage all thread items" ON chatkit_thread_items
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "Service role can manage all attachments" ON chatkit_attachments
    FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
CREATE TRIGGER update_chatkit_threads_updated_at
    BEFORE UPDATE ON chatkit_threads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

