import React, { useState } from 'react';
import { Phone, User, Loader2 } from 'lucide-react';
import InputMask from 'react-input-mask';
import { authService } from '../services/api';

const LoginPage = ({ onLogin }) => {
  const [step, setStep] = useState('phone'); // 'phone' или 'register'
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Очищаем номер от маски
      const cleanPhone = phone.replace(/\D/g, '');
      
      if (cleanPhone.length !== 11) {
        setError('Неверный формат номера телефона');
        setLoading(false);
        return;
      }

      // Пытаемся авторизоваться
      const result = await authService.loginWithPhone(cleanPhone);
      
      if (result.success && result.user) {
        // Пользователь найден
        onLogin(result.user);
      } else {
        // Пользователь не найден, переходим к регистрации
        setStep('register');
      }
    } catch (error) {
      // Если пользователь не найден, переходим к регистрации
      if (error.message.includes('не найден') || error.message.includes('not found')) {
        setStep('register');
      } else {
        setError(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const cleanPhone = phone.replace(/\D/g, '');
      
      if (!name.trim()) {
        setError('Введите ваше имя');
        setLoading(false);
        return;
      }

      const result = await authService.register({
        phone: cleanPhone,
        fullname: name.trim()
      });

      if (result.success && result.user) {
        onLogin(result.user);
      } else {
        setError('Ошибка регистрации. Попробуйте еще раз.');
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToPhone = () => {
    setStep('phone');
    setName('');
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto w-20 h-20 bg-primary-600 rounded-2xl flex items-center justify-center mb-6">
            <span className="text-white text-3xl">🎯</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">
            Система лояльности
          </h2>
          <p className="text-gray-200">
            {step === 'phone' 
              ? 'Войдите с помощью номера телефона' 
              : 'Расскажите немного о себе'
            }
          </p>
        </div>

        {/* Phone Form */}
        {step === 'phone' && (
          <form onSubmit={handlePhoneSubmit} className="card space-y-6">
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                Номер телефона
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone className="h-5 w-5 text-gray-400" />
                </div>
                <InputMask
                  mask="+7 (999) 999-99-99"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  disabled={loading}
                  className="input pl-10"
                  placeholder="+7 (___) ___-__-__"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !phone}
              className="btn-primary w-full flex items-center justify-center"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Проверяем...
                </>
              ) : (
                'Продолжить'
              )}
            </button>

            <div className="text-center">
              <p className="text-xs text-gray-500">
                Продолжая, вы соглашаетесь с условиями использования
              </p>
            </div>
          </form>
        )}

        {/* Registration Form */}
        {step === 'register' && (
          <form onSubmit={handleRegister} className="card space-y-6">
            <div className="text-center mb-4">
              <p className="text-sm text-gray-600">
                Телефон: <span className="font-medium">{phone}</span>
              </p>
            </div>

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Ваше имя
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={loading}
                  className="input pl-10"
                  placeholder="Введите ваше имя"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div className="space-y-3">
              <button
                type="submit"
                disabled={loading || !name.trim()}
                className="btn-primary w-full flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Создаем аккаунт...
                  </>
                ) : (
                  'Зарегистрироваться'
                )}
              </button>

              <button
                type="button"
                onClick={handleBackToPhone}
                disabled={loading}
                className="btn-secondary w-full"
              >
                Изменить номер
              </button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-600">
                🎁 При регистрации вы получите <span className="font-medium">100 приветственных бонусов!</span>
              </p>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default LoginPage;
