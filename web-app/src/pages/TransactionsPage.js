import React, { useState, useEffect } from 'react';
import { CreditCard, Plus, Minus, Calendar } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { transactionService } from '../services/api';
import { formatBonuses, formatRelativeDate, formatTransactionType, getTransactionIcon } from '../utils/formatters';

const TransactionsPage = ({ user }) => {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState([]);
  const [balance, setBalance] = useState(0);
  const [pagination, setPagination] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadTransactions();
  }, [user]);

  const loadTransactions = async () => {
    if (!user?.agent_id) return;

    try {
      setLoading(true);
      setError('');
      
      const response = await transactionService.getTransactions(user.agent_id, { limit: 20 });
      
      setTransactions(response.transactions || []);
      setPagination(response.pagination);
      
      // Подсчитываем текущий баланс из транзакций
      const currentBalance = response.transactions?.reduce((sum, t) => {
        return sum + (t.transaction_type === 'accrual' ? t.amount : -t.amount);
      }, 0) || 0;
      setBalance(currentBalance);
      
    } catch (error) {
      console.error('Error loading transactions:', error);
      setError('Ошибка загрузки транзакций');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="large" text="Загружаем транзакции..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Бонусы и транзакции</h1>
      </div>

      {/* Balance Card */}
      <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-primary-100 text-sm font-medium">Текущий баланс</p>
            <p className="text-4xl font-bold">{formatBonuses(balance)}</p>
            <p className="text-primary-100 text-sm mt-1">бонусных рублей</p>
          </div>
          <div className="w-16 h-16 bg-white bg-opacity-20 rounded-xl flex items-center justify-center">
            <CreditCard className="w-8 h-8" />
          </div>
        </div>
      </div>

      {/* Transactions List */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900">История операций</h3>
          {pagination && (
            <p className="text-sm text-gray-500">
              Показано {transactions.length} из {pagination.total}
            </p>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600">{error}</p>
            <button onClick={loadTransactions} className="btn-primary mt-2">
              Попробовать еще раз
            </button>
          </div>
        )}

        {transactions.length > 0 ? (
          <div className="space-y-4">
            {transactions.map((transaction, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    transaction.transaction_type === 'accrual' 
                      ? 'bg-green-100 text-green-600' 
                      : 'bg-red-100 text-red-600'
                  }`}>
                    {transaction.transaction_type === 'accrual' ? (
                      <Plus className="w-5 h-5" />
                    ) : (
                      <Minus className="w-5 h-5" />
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">
                        {formatTransactionType(transaction.transaction_type)}
                      </h4>
                      <span className="text-xs text-gray-500">
                        {getTransactionIcon(transaction.transaction_type)}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1">
                      {transaction.description || 'Операция с бонусами'}
                    </p>
                    
                    <div className="flex items-center space-x-2 mt-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-xs text-gray-500">
                        {formatRelativeDate(transaction.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <p className={`text-lg font-semibold ${
                    transaction.transaction_type === 'accrual' 
                      ? 'text-green-600' 
                      : 'text-red-600'
                  }`}>
                    {transaction.transaction_type === 'accrual' ? '+' : '-'}
                    {formatBonuses(transaction.amount)}
                  </p>
                  <p className="text-xs text-gray-500">
                    {transaction.transaction_type === 'accrual' ? 'начислено' : 'списано'}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <CreditCard className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Пока нет транзакций
            </h3>
            <p className="text-gray-600">
              Здесь будет отображаться история ваших бонусных операций
            </p>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="card bg-blue-50 border border-blue-200">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <span className="text-white text-sm">💡</span>
          </div>
          <div>
            <h3 className="font-medium text-blue-900 mb-2">Как получать бонусы?</h3>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• Совершайте покупки и получайте до {(user?.level_id || 1) * 2}% кэшбек</li>
              <li>• Посещайте наш автосервис регулярно</li>
              <li>• Участвуйте в акциях и получайте дополнительные бонусы</li>
              <li>• Приглашайте друзей и получайте вознаграждения</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionsPage;
