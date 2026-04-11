import { Outlet } from 'react-router-dom';
import { Header } from './Header';

interface LayoutProps {
  maxWidth?: string;
  maxHeight?: string;
}

/**
 * Layout Component
 * Shared layout wrapper with Header and consistent content sizing
 * Use this for all authenticated pages (excludes Login and NotFound)
 */
export function Layout({ 
  maxWidth = 'max-w-6xl',
  maxHeight = 'max-h-screen'
}: LayoutProps) {
  return (
    <div className={`min-h-screen bg-gray-100 flex flex-col ${maxHeight}`}>
      <Header />
      
      {/* Main Content Area */}
      <main className={`flex-1 w-full ${maxWidth} mx-auto px-4 py-8 overflow-y-auto`}>
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
