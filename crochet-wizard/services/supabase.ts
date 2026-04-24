import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://nnkhqzuaxrjwwzqjbczm.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ua2hxenVheHJqd3d6cWpiY3ptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5MjA5MDQsImV4cCI6MjA5MjQ5NjkwNH0.0ZXHlxRDG4MZyHsVxDvYxhgbYRZKEHG2oaQWSUew2mE';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);