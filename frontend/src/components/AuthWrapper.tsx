"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { motion } from "framer-motion";
import type { User } from "@supabase/supabase-js";
import { Loader2 } from "lucide-react";
import { useAppContext } from "@/app/context";

export function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { setIsScanning, setStatusText, setScanUrl } = useAppContext();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const enforceSecurityPolicy = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.replace("/");
        return;
      }

      setUser(session.user);
      setLoading(false);
    };

    enforceSecurityPolicy();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (!session) {
        setIsScanning(false);
        setStatusText("");
        setScanUrl("");
        router.replace("/");
      }
    });

    return () => subscription.unsubscribe();
  }, [setIsScanning, setStatusText, setScanUrl, router]);

  if (loading) {
    return (
      <div className="h-screen w-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="h-full w-full"
    >
      {children}
    </motion.div>
  );
}
