import React, { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  Home, 
  User, 
  CreditCard, 
  Calendar, 
  History, 
  Menu, 
  X,
  LogOut,
  Settings
} from 'lucide-react';

const Layout = ({ user, onLogout }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navigationItems = [
    { path: '/', label: 'Главная', icon: Home },
    { path: '/profile', label: 'Профиль', icon: User },
    { path: '/transactions', label: 'Бонусы', icon: CreditCard },
    { path: '/booking', label: 'Запись', icon: Calendar },
    { path: '/history', label: 'История', icon: History },
  ];

  const NavItem = ({ item, mobile = false }) => {
    const Icon = item.icon;
    const isActive = location.pathname === item.path;
    
    return (
      <NavLink
        to={item.path}
        onClick={() => mobile && setIsMobileMenuOpen(false)}
        className={`
          flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200
          ${isActive 
            ? 'bg-primary-600 text-white shadow-lg' 
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          }
          ${mobile ? 'w-full' : ''}
        `}
      >
        <Icon className="w-5 h-5" />
        <span className="font-medium">{item.label}</span>
      </NavLink>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white shadow-sm border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">🎯</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">Лояльность</h1>
              <p className="text-xs text-gray-500">Добро пожаловать, {user?.fullname}</p>
            </div>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 rounded-lg hover:bg-gray-100"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden bg-white border-b border-gray-200">
          <div className="px-4 py-2 space-y-1">
            {navigationItems.map((item) => (
              <NavItem key={item.path} item={item} mobile />
            ))}
            <button
              onClick={onLogout}
              className="flex items-center space-x-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 w-full transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Выйти</span>
            </button>
          </div>
        </div>
      )}

      <div className="lg:flex">
        {/* Desktop Sidebar */}
        <div className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0">
          <div className="flex flex-col flex-grow bg-white shadow-xl">
            {/* Logo */}
            <div className="flex items-center px-6 py-6 border-b border-gray-200">
              <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center mr-3">
                <span className="text-white font-bold">🎯</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Лояльность</h1>
                <p className="text-sm text-gray-500">Автосервис</p>
              </div>
            </div>

            {/* User Info */}
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-primary-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{user?.fullname}</p>
                  <p className="text-xs text-gray-500">{user?.phone}</p>
                </div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 py-6 space-y-2">
              {navigationItems.map((item) => (
                <NavItem key={item.path} item={item} />
              ))}
            </nav>

            {/* Bottom Actions */}
            <div className="px-4 py-4 border-t border-gray-200">
              <button
                onClick={onLogout}
                className="flex items-center space-x-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 w-full transition-colors"
              >
                <LogOut className="w-5 h-5" />
                <span className="font-medium">Выйти</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:pl-64 flex-1">
          <main className="py-6 px-4 sm:px-6 lg:px-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;
