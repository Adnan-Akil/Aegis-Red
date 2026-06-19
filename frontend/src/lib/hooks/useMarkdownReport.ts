import useSWR from 'swr';
import { supabase } from '@/lib/supabase';

const markdownFetcher = async (urlPath: string) => {
  if (!urlPath) return null;
  const { data } = await supabase.storage.from("attack-artifacts").createSignedUrl(urlPath, 60);
  if (!data?.signedUrl) {
    throw new Error("Failed to generate secure URL");
  }
  const res = await fetch(data.signedUrl);
  if (!res.ok) throw new Error("Failed to load text");
  const text = await res.text();
  // Apply standard preprocessing for tables
  return text
    .replace(/([^\n|])\n(\s*\|)/g, '$1\n\n$2') 
    .replace(/(\|\s*)\n([^\n|])/g, '$1\n\n$2');
};

export function useMarkdownReport(urlPath: string | null) {
  const { data, error, isLoading } = useSWR(
    urlPath ? `markdown:${urlPath}` : null,
    () => markdownFetcher(urlPath as string),
    {
      revalidateOnFocus: false,
      revalidateIfStale: false, // The artifact never changes once generated
    }
  );

  return {
    content: data,
    isLoading,
    isError: error
  };
}
