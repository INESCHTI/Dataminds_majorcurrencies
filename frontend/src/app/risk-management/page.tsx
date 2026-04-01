/**
 * Risk Management Page
 * Position sizing and risk controls
 */
import RiskManagementPanelSimple from '@/components/RiskManagementPanelSimple';

export default function RiskManagementPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="container mx-auto">
        <RiskManagementPanelSimple />
      </div>
    </div>
  );
}
