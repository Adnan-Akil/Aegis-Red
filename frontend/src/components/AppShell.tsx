"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, FileText, ScrollText, User as UserIcon, Loader2 } from "lucide-react";
import { useAppContext } from "@/app/context";
import { supabase } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";
import { IntroTour, useTour } from "@/components/IntroTour";
import { useAttackSessions } from "@/lib/hooks/useAttackSessions";


export function AppShell({ children }: { children: React.ReactNode }) {
  const {
    userName, setUserName,
    headlessMode, setHeadlessMode,
    maxMutations, setMaxMutations,
    maxIterations, setMaxIterations
  } = useAppContext();

  const pathname = usePathname();
  const isHomePage = pathname === "/dashboard";

  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const { showTour, userId, closeTour } = useTour();

  // Globally prefetch and cache session data
  useAttackSessions();


  const initialProfile = { username: "", email: "", password: "••••••••" };
  const [profileData, setProfileData] = useState(initialProfile);
  const [editProfileData, setEditProfileData] = useState(initialProfile);

  useEffect(() => {
    const fetchProfile = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        setCurrentUser(user);
        let initialUsername = user.user_metadata?.username;

        if (!initialUsername) {
          try {
            const { data: profile } = await supabase
              .from("profiles").select("username").eq("id", user.id).single();
            if (profile?.username) initialUsername = profile.username;
          } catch (err) {
            console.warn("Failed to fetch from profiles table:", err);
          }
        }

        initialUsername = initialUsername || user.email?.split("@")[0] || "Operator";
        const newProfile = { username: initialUsername, email: user.email || "", password: "••••••••" };
        setProfileData(newProfile);
        setEditProfileData(newProfile);
        setUserName(newProfile.username);
      }
    };
    fetchProfile();
  }, []);

  const [isSaving, setIsSaving] = useState(false);

  const isProfileEdited =
    profileData.username !== editProfileData.username ||
    profileData.email !== editProfileData.email ||
    (editProfileData.password !== "••••••••" && editProfileData.password !== profileData.password);

  const handleProfileSave = async () => {
    if (!isProfileEdited) return;

    // ── Input validation before touching Supabase ──
    const usernameRe = /^[a-zA-Z0-9_\-]{1,32}$/;
    if (!usernameRe.test(editProfileData.username)) {
      console.error("[Profile] Invalid username format");
      return;
    }
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(editProfileData.email)) {
      console.error("[Profile] Invalid email format");
      return;
    }
    if (
      editProfileData.password !== "••••••••" &&
      editProfileData.password !== profileData.password &&
      editProfileData.password.length < 6
    ) {
      console.error("[Profile] Password too short");
      return;
    }

    setIsSaving(true);
    try {
      const updates: any = { data: { username: editProfileData.username } };
      if (editProfileData.email !== profileData.email) updates.email = editProfileData.email;
      if (editProfileData.password !== "••••••••" && editProfileData.password !== profileData.password)
        updates.password = editProfileData.password;

      const { error } = await supabase.auth.updateUser(updates);
      if (error) throw error;

      try {
        const { error: profileError } = await supabase
          .from("profiles")
          .upsert({ id: currentUser?.id, username: editProfileData.username, updated_at: new Date().toISOString() });
        if (profileError) console.warn("Profiles table upsert failed:", profileError.message);
      } catch (dbErr) {
        console.warn("DB profiles upsert error:", dbErr);
      }

      setProfileData(editProfileData);
      setUserName(editProfileData.username);
      setIsProfileOpen(false);
    } catch (err: any) {
      console.error("Error updating profile: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleProfileClose = () => setIsProfileOpen(false);
  const handleProfileOpen = () => { setEditProfileData(profileData); setIsProfileOpen(true); };
  const handleLogout = async () => { await supabase.auth.signOut(); };

  // Shared glass style
  const glassPanel = {
    background: "rgba(10,10,12,0.70)",
    backdropFilter: "blur(20px)",
    WebkitBackdropFilter: "blur(20px)",
  } as const;

  return (
    <div className="h-screen w-screen text-zinc-300 flex flex-col overflow-hidden relative">

      {/* ── Global Background Image ── */}
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage: "url('/bg_picture.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          filter: "blur(5px) brightness(0.52) saturate(0.85)",
          transform: "scale(1.05)",
        }}
      />
      <div className="fixed inset-0 z-0 pointer-events-none bg-black/40" />

      {/* ── Floating Pill Navbar ── */}
      <div className="fixed top-0 left-0 right-0 w-full flex justify-center pt-6 z-40 pointer-events-none">
        <nav
          className="flex items-center gap-12 px-12 py-3 rounded-full pointer-events-auto shadow-2xl"
          style={{
            ...glassPanel,
            border: "1px solid rgba(255,255,255,0.20)",
          }}
        >
          {/* Logo / Title */}
          <h1
            className="font-bold tracking-widest text-white select-none font-chaste drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)]"
            style={{
              fontFamily: "var(--font-chaste)",
              letterSpacing: "0.2em",
              fontSize: "1.2rem"
            }}
          >
            Aegis-Red
          </h1>

          <div className="w-px h-6 bg-white/10" />

          {/* Nav Icons */}
          <div className="flex items-center gap-6">
            {[
              { href: "/dashboard", Icon: Home, label: "Home", id: "tour-nav-home" },
              { href: "/reports", Icon: FileText, label: "Reports", id: "tour-nav-reports" },
              { href: "/logs", Icon: ScrollText, label: "Logs", id: "tour-nav-logs" },
            ].map(({ href, Icon, label, id }) => (
              <Link
                key={href}
                id={id}
                href={href}
                className="relative group flex items-center justify-center cursor-pointer gap-2"
              >
                {pathname === href && (
                  <span
                    className="absolute -bottom-3 left-1/2 -translate-x-1/2 h-0.5 rounded-full bg-white/80"
                    style={{
                      width: "20px",
                      boxShadow: "0 0 8px 2px rgba(255,255,255,0.4)"
                    }}
                  />
                )}
                <Icon
                  className={`transition-all duration-200 drop-shadow-[0_2px_4px_rgba(0,0,0,0.4)] ${
                    pathname === href
                      ? "text-white"
                      : "text-zinc-500 group-hover:text-zinc-200 group-hover:scale-110"
                  }`}
                  style={{ width: "20px", height: "20px" }}
                />
                <span
                  className={`uppercase tracking-widest font-mono transition-colors duration-200 drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)] ${
                    pathname === href ? "text-white font-semibold" : "text-zinc-500 group-hover:text-zinc-300"
                  }`}
                  style={{ fontSize: "10px" }}
                >
                  {label}
                </span>
              </Link>
            ))}
          </div>

          <div className="w-px h-6 bg-white/10" />

          {/* Profile */}
          <button
            id="tour-profile-btn"
            onClick={handleProfileOpen}
            className="flex items-center gap-2 group cursor-pointer"
          >
            <div
              className="rounded-full flex items-center justify-center border border-zinc-700/60 transition-all duration-200 hover:border-zinc-500 hover:scale-105 shadow-[0_2px_8px_rgba(0,0,0,0.4)] relative overflow-hidden"
              style={{
                background: "rgba(255,255,255,0.05)",
                backdropFilter: "blur(12px)",
                WebkitBackdropFilter: "blur(12px)",
                width: "32px",
                height: "32px"
              }}
            >
              <UserIcon
                className="text-zinc-400 group-hover:text-zinc-200 transition-colors drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]"
                style={{ width: "16px", height: "16px" }}
              />
            </div>
            <span
              className="uppercase tracking-widest font-mono text-zinc-500 group-hover:text-zinc-300 transition-colors drop-shadow-[0_1px_2px_rgba(0,0,0,0.4)]"
              style={{ fontSize: "10px" }}
            >
              Profile
            </span>
          </button>
        </nav>
      </div>

      {/* ── Main Content ── */}
      <div className="flex-1 overflow-hidden relative z-10">
        <main className="h-full w-full overflow-y-auto overflow-x-hidden relative">
          {children}
        </main>
      </div>

      {/* ── Profile Modal ── */}
      {isProfileOpen && (
        <div
          onClick={handleProfileClose}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 cursor-pointer backdrop-blur-md"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="border rounded-2xl p-6 w-full max-w-sm shadow-2xl flex flex-col cursor-default"
            style={{
              background: "rgba(20, 20, 24, 0.45)",
              backdropFilter: "blur(16px)",
              WebkitBackdropFilter: "blur(16px)",
              borderColor: "rgba(255,255,255,0.08)",
            }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-full flex items-center justify-center border border-zinc-700/60"
                style={{ background: "rgba(255,255,255,0.07)" }}>
                <UserIcon className="w-6 h-6 text-zinc-300" />
              </div>
              <div>
                <h2 className="text-lg font-medium text-white">{profileData.username}</h2>
                <p className="text-xs text-zinc-500">Administrator</p>
              </div>
            </div>

            <div className="flex flex-col gap-4 mb-8">
              {[
                { label: "Username", type: "text", key: "username" },
                { label: "Email", type: "email", key: "email" },
                { label: "Password", type: "password", key: "password" },
              ].map(({ label, type, key }) => (
                <div key={key} className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{label}</label>
                  <input
                    type={type}
                    value={(editProfileData as any)[key]}
                    onChange={(e) => setEditProfileData({ ...editProfileData, [key]: e.target.value })}
                    className="rounded-md px-3 py-2 text-sm text-zinc-200 outline-none transition-colors border"
                    style={{ background: "rgba(255,255,255,0.05)", borderColor: "rgba(255,255,255,0.08)" }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)"; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"; }}
                  />
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center mt-auto">
              <button onClick={handleLogout}
                className="px-4 py-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 text-sm font-medium rounded-md transition-colors">
                Logout
              </button>
              <button
                onClick={isProfileEdited ? handleProfileSave : handleProfileClose}
                disabled={isSaving}
                className={`px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 flex items-center justify-center min-w-[80px] ${
                  isProfileEdited
                    ? "bg-zinc-200 text-black hover:bg-white hover:shadow-lg"
                    : "bg-zinc-800/60 text-zinc-300 hover:bg-zinc-700/60"
                }`}
              >
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : (isProfileEdited ? "Save" : "Close")}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Intro Tour ── */}
      {showTour && <IntroTour onDone={closeTour} userId={userId} />}
    </div>
  );
}