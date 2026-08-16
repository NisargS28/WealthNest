import { NavStatus } from "@/types";

export default function NavStatusBadge({ status }: { status: NavStatus }) {
  let badgeClass = "badge-neutral";
  let display: string = status;

  if (status === "AVAILABLE") {
    badgeClass = "badge-success";
  } else if (status === "STALE_DATA" || status === "AMBIGUOUS") {
    badgeClass = "badge-warning";
    display = status === "STALE_DATA" ? "STALE" : "AMBIGUOUS";
  } else if (status === "NAV_UNAVAILABLE" || status === "SCHEME_UNMATCHED" || status === "API_ERROR") {
    badgeClass = "badge-error";
    display = status === "SCHEME_UNMATCHED" ? "UNMATCHED" : "UNAVAILABLE";
  }

  return (
    <span className={`badge ${badgeClass}`}>
      {display}
    </span>
  );
}
