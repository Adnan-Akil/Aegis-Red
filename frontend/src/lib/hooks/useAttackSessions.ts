import useSWR from 'swr';
import { supabase } from '@/lib/supabase';

const fetcher = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error("Not authenticated");

  const { data, error } = await supabase
    .from("attack_sessions")
    .select("*")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  if (error) throw error;
  return data;
};

export function useAttackSessions() {
  const { data, error, isLoading, mutate } = useSWR('attack_sessions', fetcher, {
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
  });

  return {
    sessions: data || [],
    isLoading,
    isError: error,
    mutate
  };
}
