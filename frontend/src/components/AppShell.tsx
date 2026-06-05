"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, FileText, ScrollText, User as UserIcon, Loader2 } from "lucide-react";
import { useAppContext } from "@/app/context";
import { supabase } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { 
    userName, setUserName,
    headlessMode, setHeadlessMode, 
    maxMutations, setMaxMutations, 
    maxIterations, setMaxIterations 
  } = useAppContext();
  
  const pathname = usePathname();

  // Profile Modal State
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const initialProfile = {
    username: "",
    email: "",
    password: "••••••••",
  };
  const [profileData, setProfileData] = useState(initialProfile);
  const [editProfileData, setEditProfileData] = useState(initialProfile);

  useEffect(() => {
    const fetchProfile = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        setCurrentUser(user);
        
        // Fetch from profiles table if available, otherwise fallback to Auth user metadata
        let initialUsername = user.user_metadata?.username;
        
        if (!initialUsername) {
          try {
            const { data: profile } = await supabase
              .from("profiles")
              .select("username")
              .eq("id", user.id)
              .single();
            if (profile?.username) {
              initialUsername = profile.username;
            }
          } catch (err) {
            console.warn("Failed to fetch from profiles table:", err);
          }
        }

        initialUsername = initialUsername || user.email?.split("@")[0] || "Operator";
        
        const newProfile = {
          username: initialUsername,
          email: user.email || "",
          password: "••••••••",
        };
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
    setIsSaving(true);

    try {
      const updates: any = {
        data: { username: editProfileData.username }
      };
      
      if (editProfileData.email !== profileData.email) {
        updates.email = editProfileData.email;
      }
      
      if (editProfileData.password !== "••••••••" && editProfileData.password !== profileData.password) {
        updates.password = editProfileData.password;
      }

      const { error } = await supabase.auth.updateUser(updates);
      if (error) throw error;

      // Persist to profiles table (if it exists)
      try {
        const { error: profileError } = await supabase
          .from("profiles")
          .upsert({ 
            id: currentUser?.id, 
            username: editProfileData.username,
            updated_at: new Date().toISOString()
          });
        if (profileError) {
          console.warn("Profiles table upsert failed (it may not exist):", profileError.message);
        }
      } catch (dbErr) {
        console.warn("DB profiles upsert error:", dbErr);
      }

      setProfileData(editProfileData);
      setUserName(editProfileData.username);
      setIsProfileOpen(false);
      console.log("Profile updated successfully!");
    } catch (err: any) {
      console.error("Error updating profile: " + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleProfileClose = () => {
    setIsProfileOpen(false);
  };

  const handleProfileOpen = () => {
    setEditProfileData(profileData); 
    setIsProfileOpen(true);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  return (
    <div className="h-screen w-screen bg-transparent text-zinc-300 flex overflow-hidden">
      {/* Sidebar - Fixed Left */}
      <aside className="w-16 h-full bg-zinc-950 border-r border-zinc-800/50 flex flex-col items-center py-8 z-20 shrink-0">
        <div className="flex-1 flex flex-col justify-center space-y-12">
          <Link href="/" className="relative group flex justify-center cursor-pointer">
            <Home className={`w-6 h-6 transition-colors ${pathname === '/' ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}`} />
            <div className="absolute left-14 px-2 py-1 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
              Home
            </div>
          </Link>
          <Link href="/reports" className="relative group flex justify-center cursor-pointer">
            <FileText className={`w-6 h-6 transition-colors ${pathname === '/reports' ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}`} />
            <div className="absolute left-14 px-2 py-1 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
              Reports
            </div>
          </Link>
          <Link href="/logs" className="relative group flex justify-center cursor-pointer">
            <ScrollText className={`w-6 h-6 transition-colors ${pathname === '/logs' ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-200'}`} />
            <div className="absolute left-14 px-2 py-1 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap">
              Logs
            </div>
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative z-10 overflow-hidden">
        {/* Top Bar */}
        <header className="w-full flex justify-between items-center px-8 pt-8 pb-4 shrink-0">
          <div>
            <h1 className="text-2xl font-bold tracking-wider text-white" style={{ fontFamily: 'var(--font-chaste)' }}>Aegis-Red</h1>
          </div>
          
          <div className="flex flex-col items-end relative">
            <div 
              onClick={handleProfileOpen}
              className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700 cursor-pointer hover:bg-zinc-700 transition-colors z-10"
            >
              <UserIcon className="w-5 h-5 text-zinc-300" />
            </div>
            
            {pathname === '/' && (
              <div className="absolute top-20 right-0 mt-2 z-20">
                {/* Settings Panel */}
                <div className="flex flex-col gap-4 w-52 bg-zinc-950/90 p-4 rounded-xl border border-zinc-800/80 backdrop-blur-md shadow-xl relative z-10">
                  
                  {/* Headless Toggle */}
                  <div className="flex items-center justify-between group relative z-50 pb-3 border-b border-zinc-800/50">
                    <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold whitespace-nowrap select-none">
                      {headlessMode ? 'Headless' : 'Headed'}
                    </span>
                    <button 
                      onClick={() => setHeadlessMode(!headlessMode)}
                      className={`w-8 h-4 rounded-full relative transition-colors cursor-pointer ${headlessMode ? 'bg-zinc-300' : 'bg-zinc-700'}`}
                    >
                      <div 
                        className={`w-3 h-3 bg-[#121212] rounded-full absolute top-0.5 transition-transform ${headlessMode ? 'translate-x-4' : 'translate-x-0.5'}`}
                      />
                    </button>
                    <div className="absolute top-0 right-full mr-3 w-48 p-2 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity text-right">
                      Determines whether the bot runs the browser invisibly in the background (Headless) or opens a visible window (Headed).
                    </div>
                  </div>

                  {/* Sliders */}
                  <div className="flex flex-col gap-1.5 relative group/mutation">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">
                      <span>Max Mutations</span>
                      <span className="text-zinc-300">{maxMutations}</span>
                    </div>
                    <input 
                      type="range" 
                      min="1" 
                      max="5" 
                      value={maxMutations} 
                      onChange={(e) => setMaxMutations(parseInt(e.target.value))} 
                      className="w-full accent-zinc-400 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer" 
                    />
                    <div className="absolute top-0 right-full mr-3 w-48 p-2 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover/mutation:opacity-100 pointer-events-none transition-opacity text-right">
                      Determines how many times the agent will attempt to dynamically mutate and retry a failed payload.
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5 relative group/iteration">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">
                      <span>Max Iterations</span>
                      <span className="text-zinc-300">{maxIterations}</span>
                    </div>
                    <input 
                      type="range" 
                      min="1" 
                      max="15" 
                      value={maxIterations} 
                      onChange={(e) => setMaxIterations(parseInt(e.target.value))} 
                      className="w-full accent-zinc-400 h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer" 
                    />
                    <div className="absolute top-0 right-full mr-3 w-48 p-2 bg-zinc-800 text-xs text-white rounded opacity-0 group-hover/iteration:opacity-100 pointer-events-none transition-opacity text-right">
                      Maximum number of conversational turns the agent will take before aborting the current attack vector.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Scrollable Children Container */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden relative">
          {children}
        </div>
      </main>

      {/* Profile Modal */}
      {isProfileOpen && (
        <div 
          onClick={handleProfileClose}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm cursor-pointer"
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-sm shadow-2xl flex flex-col cursor-default"
          >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center border border-zinc-700">
                <UserIcon className="w-6 h-6 text-zinc-300" />
              </div>
              <div>
                <h2 className="text-lg font-medium text-white">{profileData.username}</h2>
                <p className="text-xs text-zinc-500">Administrator</p>
              </div>
            </div>

            {/* Form */}
            <div className="flex flex-col gap-4 mb-8">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Username</label>
                <input 
                  type="text" 
                  value={editProfileData.username} 
                  onChange={(e) => setEditProfileData({...editProfileData, username: e.target.value})}
                  className="bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 outline-none focus:border-zinc-600 transition-colors"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Email</label>
                <input 
                  type="email" 
                  value={editProfileData.email} 
                  onChange={(e) => setEditProfileData({...editProfileData, email: e.target.value})}
                  className="bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 outline-none focus:border-zinc-600 transition-colors"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Password</label>
                <input 
                  type="password" 
                  value={editProfileData.password} 
                  onChange={(e) => setEditProfileData({...editProfileData, password: e.target.value})}
                  className="bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 outline-none focus:border-zinc-600 transition-colors"
                />
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-between items-center mt-auto">
              <button 
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500/10 text-red-500 hover:bg-red-500/20 text-sm font-medium rounded-md transition-colors"
              >
                Logout
              </button>

              <button 
                onClick={isProfileEdited ? handleProfileSave : handleProfileClose}
                disabled={isSaving}
                className={`px-6 py-2 text-sm font-medium rounded-md transition-colors flex items-center justify-center min-w-[80px] ${
                  isProfileEdited 
                    ? 'bg-zinc-200 text-black hover:bg-white' 
                    : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                }`}
              >
                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : (isProfileEdited ? 'Save' : 'Close')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}