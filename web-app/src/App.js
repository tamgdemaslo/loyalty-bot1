import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './styles/index.css';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import TransactionsPage from './pages/TransactionsPage';
import BookingPage from './pages/BookingPage';
import HistoryPage from './pages/HistoryPage';

// Components
import Layout from './components/Layout';
import LoadingSpinner from './components/LoadingSpinner';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Проверяем сохраненные данные пользователя
    const savedUser = localStorage.getItem('loyalty_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('loyalty_user');
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('loyalty_user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('loyalty_user');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <Router>
      <div className="App">
        <Routes>
          {!user ? (
            // Неавторизованные пользователи
            <>
              <Route 
                path="/login" 
                element={<LoginPage onLogin={handleLogin} />} 
              />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </>
          ) : (
            // Авторизованные пользователи
            <Route path="/" element={<Layout user={user} onLogout={handleLogout} />}>
              <Route index element={<DashboardPage user={user} />} />
              <Route path="profile" element={<ProfilePage user={user} />} />
              <Route path="transactions" element={<TransactionsPage user={user} />} />
              <Route path="booking" element={<BookingPage user={user} />} />
              <Route path="history" element={<HistoryPage user={user} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          )}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
