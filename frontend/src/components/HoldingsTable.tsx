import { HoldingPreview, StoredHolding } from "@/types";
import NavStatusBadge from "./NavStatusBadge";

interface Props {
  holdings: (HoldingPreview | StoredHolding)[];
}

export default function HoldingsTable({ holdings }: Props) {
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Scheme</th>
            <th className="text-right">Units</th>
            <th className="text-right">NAV</th>
            <th className="text-right">Current Value</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((h, i) => (
            <tr key={i}>
              <td>
                <div className="font-medium mb-1" style={{ maxWidth: "400px", whiteSpace: "normal" }}>
                  {h.scheme_name}
                </div>
                <div className="text-xs text-secondary flex gap-2">
                  <span>{h.amc}</span>
                  {h.isin && <span>• {h.isin}</span>}
                </div>
              </td>
              <td className="text-right font-medium">{h.total_units}</td>
              <td className="text-right">
                {h.nav ? (
                  <div>
                    <div className="font-medium">₹ {h.nav}</div>
                    <div className="text-xs text-secondary">{h.nav_date}</div>
                  </div>
                ) : (
                  <span className="text-secondary">-</span>
                )}
              </td>
              <td className="text-right font-bold text-success">
                {h.current_value ? `₹ ${parseFloat(h.current_value).toLocaleString('en-IN', {minimumFractionDigits: 2})}` : "-"}
              </td>
              <td>
                <NavStatusBadge status={h.nav_status} />
              </td>
            </tr>
          ))}
          {holdings.length === 0 && (
            <tr>
              <td colSpan={5} className="text-center text-secondary py-8">
                No holdings found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
