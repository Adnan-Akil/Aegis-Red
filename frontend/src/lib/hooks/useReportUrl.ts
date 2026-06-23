import useSWR from 'swr';
import { supabase } from '@/lib/supabase';

const urlFetcher = async (urlPath: string) => {
  if (!urlPath) return null;
  // Create a signed URL valid for 1 hour (3600 seconds)
  const { data } = await supabase.storage.from("attack-artifacts").createSignedUrl(urlPath, 3600);
  if (!data?.signedUrl) {
    throw new Error("Failed to generate secure URL");
  }
  return data.signedUrl;
};

export function useReportUrl(urlPath: string | null) {
  const { data, error, isLoading } = useSWR(
    urlPath ? `report-url:${urlPath}` : null,
    () => urlFetcher(urlPath as string),
    {
      revalidateOnFocus: false,
      revalidateIfStale: false,
    }
  );

  return {
    url: data,
    isLoading,
    isError: error
  };
}
