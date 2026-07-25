from src.memory.supabase_manager import SupabaseManager

sm = SupabaseManager()

result = sm.supabase.table("attack_sessions").select("*").eq("user_id", "21a514e3-c2dd-490b-ad0c-7c0202a63256").order("created_at", desc=True).limit(30).execute()
sessions = result.data
print(f"Total sessions in Supabase for active user: {len(sessions)}")
for s in sessions:
    print(f"  {str(s.get('id','?'))[:8]} | {s.get('target_url','?')[:30]} | {s.get('status','?')} | {str(s.get('created_at','?'))[:19]}")
