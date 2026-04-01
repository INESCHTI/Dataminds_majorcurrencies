/**
 * Multi-Timezone Optimization Page
 */
import MultiTimezonePanelSimple from '@/components/MultiTimezonePanelSimple';

export default function MultiTimezonePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 p-6">
      <div className="container mx-auto">
        <MultiTimezonePanelSimple />
      </div>
    </div>
  );
}
