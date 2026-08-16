import { ValidationSummary } from "@/types";

export default function ValidationPanel({ validation }: { validation: ValidationSummary }) {
  const totalWarnings = validation.parser_warnings + validation.reconciliation_warnings + validation.nav_errors;
  
  if (totalWarnings === 0 && validation.unmatched_schemes === 0 && validation.stale_nav_schemes === 0) {
    return (
      <div className="p-4 rounded-md mt-4" style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success)' }}>
        <p className="text-success mb-0 font-medium">All validation checks passed.</p>
      </div>
    );
  }

  return (
    <div className="p-4 rounded-md mt-4 animate-fade-in" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid var(--warning)' }}>
      <h3 className="text-warning text-lg mb-2 flex items-center gap-2">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        Validation Warnings
      </h3>
      
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <span className="text-secondary text-sm">Parser Warnings</span>
          <div className="font-bold">{validation.parser_warnings}</div>
        </div>
        <div>
          <span className="text-secondary text-sm">Reconciliation Failures</span>
          <div className="font-bold">{validation.reconciliation_warnings}</div>
        </div>
        <div>
          <span className="text-secondary text-sm">Unmatched Schemes</span>
          <div className="font-bold">{validation.unmatched_schemes}</div>
        </div>
      </div>
      
      {validation.warnings.length > 0 && (
        <div style={{ maxHeight: '200px', overflowY: 'auto' }} className="mt-4">
          <ul className="text-sm" style={{ paddingLeft: '1.2rem' }}>
            {validation.warnings.map((w, i) => (
              <li key={i} className="mb-2 text-secondary">
                <span className="font-medium text-primary">Folio {w.folio}:</span> {w.message}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
