"use client";

import { useState, useEffect, useRef } from "react";
import { Bell, X, Check, Pencil } from "lucide-react";
import { Notification } from "@/types";
import { createClient } from "@/utils/supabase/client";

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [editingSipId, setEditingSipId] = useState<string | null>(null);
  const [newSipDay, setNewSipDay] = useState<number>(15);
  const [saving, setSaving] = useState(false);
  // SIP confirmation (for SIP_CONFIRMATION notifications)
  const [confirmingOccurrenceId, setConfirmingOccurrenceId] = useState<string | null>(null);
  const [actualDate, setActualDate] = useState<string>("");
  const [confirmingSaving, setConfirmingSaving] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchNotifications = async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_BASE}/api/notifications`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setNotifications(data.notifications || []);
      setUnreadCount(data.unread_count || 0);
    } catch (e) {
      console.error("Failed to load notifications", e);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const markRead = async (id: string) => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      await fetch(`${API_BASE}/api/notifications/${id}/read`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      await fetchNotifications();
    } catch (e) {
      console.error("Failed to mark read", e);
    }
  };

  const confirmSipPlan = async (entityId: string, notifId: string, sipDay?: number) => {
    try {
      setSaving(true);
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const body: Record<string, unknown> = { status: "ACTIVE" };
      if (sipDay) body.sip_day = sipDay;

      await fetch(`${API_BASE}/api/sip-plans/${entityId}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });
      await markRead(notifId);
      setEditingSipId(null);
    } catch (e) {
      console.error("Failed to confirm SIP plan", e);
    } finally {
      setSaving(false);
    }
  };

  const ordinalSuffix = (d: number) => {
    if (d >= 11 && d <= 13) return `${d}th`;
    switch (d % 10) {
      case 1: return `${d}st`;
      case 2: return `${d}nd`;
      case 3: return `${d}rd`;
      default: return `${d}th`;
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-accent"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-red-500 rounded-full text-[10px] font-bold text-white flex items-center justify-center px-0.5">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-96 max-h-[80vh] overflow-y-auto bg-[#1a1814] border border-white/10 rounded-xl shadow-2xl z-50 flex flex-col animate-slide-up">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <h3 className="font-semibold text-white/90 text-sm">Notifications</h3>
            <button onClick={() => setOpen(false)} className="text-secondary hover:text-white">
              <X size={16} />
            </button>
          </div>

          {notifications.length === 0 ? (
            <div className="p-6 text-center text-secondary text-sm">No notifications</div>
          ) : (
            <div className="divide-y divide-white/5">
              {notifications.map((n) => (
                <div key={n.id} className={`p-4 ${n.status === "UNREAD" ? "bg-white/[0.03]" : ""}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        {n.status === "UNREAD" && (
                          <span className="w-2 h-2 bg-amber-400 rounded-full shrink-0" />
                        )}
                        <p className="text-sm font-semibold text-white/90">{n.title}</p>
                      </div>
                      <p className="text-xs text-secondary mt-0.5 leading-relaxed">{n.message}</p>

                      {/* SIP_PLAN_DETECTED card */}
                      {n.type === "SIP_PLAN_DETECTED" && n.entity_id && n.sip_status !== "ACTIVE" && (
                        <div className="mt-3">
                          {editingSipId === n.entity_id ? (
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-xs text-secondary">SIP day:</span>
                              <input
                                type="number" min={1} max={31} value={newSipDay}
                                onChange={(e) => setNewSipDay(parseInt(e.target.value))}
                                className="w-16 px-2 py-1 text-xs rounded bg-white/10 border border-white/20 text-white text-center"
                              />
                              <button
                                disabled={saving}
                                onClick={() => confirmSipPlan(n.entity_id!, n.id, newSipDay)}
                                className="px-3 py-1 text-xs rounded bg-amber-500 hover:bg-amber-400 text-black font-semibold transition-colors disabled:opacity-50"
                              >
                                {saving ? "Saving…" : "Confirm"}
                              </button>
                              <button onClick={() => setEditingSipId(null)} className="text-xs text-secondary hover:text-white">Cancel</button>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 mt-2">
                              <button
                                onClick={() => confirmSipPlan(n.entity_id!, n.id)}
                                className="px-3 py-1 text-xs rounded bg-green-600 hover:bg-green-500 text-white font-semibold transition-colors flex items-center gap-1"
                              >
                                <Check size={12} /> Confirm
                              </button>
                              <button
                                onClick={() => { setEditingSipId(n.entity_id!); setNewSipDay(n.sip_day || 15); }}
                                className="px-3 py-1 text-xs rounded border border-white/20 hover:border-white/40 text-white/70 hover:text-white transition-colors flex items-center gap-1"
                              >
                                <Pencil size={12} /> Edit Date
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {n.type === "SIP_PLAN_DETECTED" && n.sip_status === "ACTIVE" && (
                        <span className="mt-2 inline-block text-xs px-2 py-0.5 rounded-full bg-green-900/40 text-green-400 font-medium">✓ Confirmed</span>
                      )}

                      {/* SIP_CONFIRMATION card — monthly transaction reminder */}
                      {n.type === "SIP_CONFIRMATION" && n.entity_id && n.occurrence_status !== "CONFIRMED" && (
                        <div className="mt-3">
                          {confirmingOccurrenceId === n.entity_id ? (
                            <div className="flex flex-col gap-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-secondary">Actual date:</span>
                                <input
                                  type="date"
                                  value={actualDate}
                                  onChange={(e) => setActualDate(e.target.value)}
                                  className="px-2 py-1 text-xs rounded bg-white/10 border border-white/20 text-white"
                                />
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  disabled={confirmingSaving}
                                  onClick={async () => {
                                    setConfirmingSaving(true);
                                    try {
                                      const supabase = createClient();
                                      const { data: { session } } = await supabase.auth.getSession();
                                      if (!session) return;
                                      await fetch(`${API_BASE}/api/sip-occurrences/${n.entity_id}/confirm`, {
                                        method: "POST",
                                        headers: { Authorization: `Bearer ${session.access_token}`, "Content-Type": "application/json" },
                                        body: JSON.stringify({ actual_date: actualDate || undefined })
                                      });
                                      setConfirmingOccurrenceId(null);
                                      await fetchNotifications();
                                    } catch (e) { console.error(e); }
                                    finally { setConfirmingSaving(false); }
                                  }}
                                  className="px-3 py-1 text-xs rounded bg-green-600 hover:bg-green-500 text-white font-semibold flex items-center gap-1 disabled:opacity-50"
                                >
                                  <Check size={12} /> {confirmingSaving ? "Saving…" : "Yes, confirm"}
                                </button>
                                <button onClick={() => setConfirmingOccurrenceId(null)} className="text-xs text-secondary hover:text-white">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2 mt-2">
                              <button
                                onClick={() => {
                                  setConfirmingOccurrenceId(n.entity_id!);
                                  setActualDate(n.occurrence_expected_date || "");
                                }}
                                className="px-3 py-1 text-xs rounded bg-green-600 hover:bg-green-500 text-white font-semibold flex items-center gap-1"
                              >
                                <Check size={12} /> Yes, it went through
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {n.type === "SIP_CONFIRMATION" && n.occurrence_status === "CONFIRMED" && (
                        <span className="mt-2 inline-block text-xs px-2 py-0.5 rounded-full bg-green-900/40 text-green-400 font-medium">✓ Transaction recorded</span>
                      )}
                    </div>
                    <span className="text-[10px] text-secondary shrink-0">
                      {new Date(n.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
