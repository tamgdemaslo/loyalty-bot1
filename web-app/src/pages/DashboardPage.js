import React, { useState, useEffect } from 'react';
import { 
  CreditCard, 
  TrendingUp, 
  Calendar, 
  Gift,
  Award,
  ArrowRight,
  Wallet,
  Star
} from 'lucide-react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import { userService, transactionService, analyticsService } from '../services/api';
import { formatBonuses, formatMoney, getLevelName, getLevelColor, formatRelativeDate } from '../utils/formatters';

const DashboardPage = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    balance: 0,
    level: 1,
    totalSpent: 0,
    recentTransactions: [],
    stats: null
  });
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    if (!user?.agent_id) return;

    try {
      setLoading(true);
      setError('');

      // Загружаем данные параллельно
      const [userInfo, transactions, stats] = await Promise.all([
        userService.getUserInfo(user.agent_id),
        transactionService.getTransactions(user.agent_id, { limit: 5 }),
        analyticsService.getUserStats(user.agent_id).catch(() => null)
      ]);

      setData({
        balance: userInfo.user?.balance || 0,
        level: userInfo.user?.level_id || 1,
        totalSpent: userInfo.user?.total_spent || 0,
        recentTransactions: transactions.transactions || [],
        stats
      });
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" text="Загружаем ваши данные..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={loadDashboardData}
            className="btn-primary mt-4"
          >
            Попробовать еще раз
          </button>
        </div>
      </div>
    );
  }

  const levelColor = getLevelColor(data.level);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center lg:text-left">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">
          Добро пожаловать, {user.fullname}!
        </h1>
        <p className="text-gray-600 mt-1">
          Ваша панель управления бонусной программой
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Balance Card */}
        <div className="card-hover bg-gradient-to-br from-primary-500 to-primary-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-primary-100 text-sm font-medium">Баланс бонусов</p>
              <p className="text-3xl font-bold">{formatBonuses(data.balance)}</p>
            </div>
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
              <Wallet className="w-6 h-6" />
            </div>
          </div>
          <Link 
            to="/transactions" 
            className="flex items-center mt-4 text-primary-100 hover:text-white transition-colors"
          >
            <span className="text-sm">Управлять бонусами</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {/* Level Card */}
        <div className={`card-hover bg-gradient-to-br from-${levelColor}-500 to-${levelColor}-600 text-white`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-${levelColor}-100 text-sm font-medium`}>Уровень</p>
              <p className="text-2xl font-bold">{getLevelName(data.level)}</p>
            </div>
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
              <Award className="w-6 h-6" />
            </div>
          </div>
          <Link 
            to="/profile" 
            className={`flex items-center mt-4 text-${levelColor}-100 hover:text-white transition-colors`}
          >
            <span className="text-sm">Подробнее</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {/* Total Spent Card */}
        <div className="card-hover bg-gradient-to-br from-green-500 to-green-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm font-medium">Потрачено</p>
              <p className="text-2xl font-bold">{formatMoney(data.totalSpent)}</p>
            </div>
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
          <Link 
            to="/history" 
            className="flex items-center mt-4 text-green-100 hover:text-white transition-colors"
          >
            <span className="text-sm">История покупок</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>

        {/* Next Visit Card */}
        <div className="card-hover bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">Следующий визит</p>
              <p className="text-lg font-bold">Записаться</p>
            </div>
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
              <Calendar className="w-6 h-6" />
            </div>
          </div>
          <Link 
            to="/booking" 
            className="flex items-center mt-4 text-purple-100 hover:text-white transition-colors"
          >
            <span className="text-sm">Записаться на услугу</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Последние операции</h3>
            <Link 
              to="/transactions"
              className="text-primary-600 hover:text-primary-700 font-medium text-sm"
            >
              Все операции
            </Link>
          </div>

          {data.recentTransactions.length > 0 ? (
            <div className="space-y-4">
              {data.recentTransactions.map((transaction, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      transaction.transaction_type === 'accrual' 
                        ? 'bg-green-100 text-green-600' 
                        : 'bg-red-100 text-red-600'
                    }`}>
                      {transaction.transaction_type === 'accrual' ? '+' : '-'}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {transaction.description || 'Операция с бонусами'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatRelativeDate(transaction.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-semibold ${
                      transaction.transaction_type === 'accrual' 
                        ? 'text-green-600' 
                        : 'text-red-600'
                    }`}>
                      {transaction.transaction_type === 'accrual' ? '+' : '-'}
                      {formatBonuses(transaction.amount)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <CreditCard className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500">У вас пока нет операций с бонусами</p>
            </div>
          )}
        </div>

        {/* Loyalty Program Info */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Программа лояльности</h3>
          
          <div className="space-y-4">
            {/* Current Level */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 bg-${levelColor}-500 rounded-full flex items-center justify-center`}>
                  <Star className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Ваш уровень</p>
                  <p className="text-sm text-gray-600">{getLevelName(data.level)}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-primary-600">{data.level}</p>
                <p className="text-xs text-gray-500">из 5</p>
              </div>
            </div>

            {/* Benefits */}
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Gift className="w-5 h-5 text-green-500" />
                <span className="text-sm text-gray-600">Кэшбек до {data.level * 2}% с покупок</span>
              </div>
              <div className="flex items-center space-x-3">
                <Calendar className="w-5 h-5 text-blue-500" />
                <span className="text-sm text-gray-600">Приоритетная запись на услуги</span>
              </div>
              <div className="flex items-center space-x-3">
                <Award className="w-5 h-5 text-purple-500" />
                <span className="text-sm text-gray-600">Персональные предложения</span>
              </div>
            </div>

            <Link 
              to="/profile"
              className="btn-primary w-full"
            >
              Узнать больше о программе
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
