import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, BarChart, Bar } from 'recharts';

const AutoServiceApp = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [user, setUser] = useState({
    name: 'Александр Петров',
    phone: '+7 (925) 123-45-67',
    bonusBalance: 2580,
    loyaltyLevel: 'gold',
    totalSpent: 87450,
    visits: 23,
    nextService: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000)
  });

  const [vehicles, setVehicles] = useState([
    {
      id: 1,
      brand: 'BMW',
      model: 'X5',
      year: 2020,
      vin: 'WBAFR9C50ED123456',
      mileage: 45600,
      nextService: 50000,
      color: '#1e40af',
      isActive: true
    },
    {
      id: 2,
      brand: 'Mercedes',
      model: 'E-Class',
      year: 2019,
      vin: 'WDDGF8BB9KA123456',
      mileage: 62300,
      nextService: 65000,
      color: '#7c2d12',
      isActive: false
    }
  ]);

  const [services, setServices] = useState([
    { id: 1, name: 'Замена масла', price: 3500, duration: '30 мин', category: 'maintenance' },
    { id: 2, name: 'Диагностика', price: 2500, duration: '45 мин', category: 'diagnostic' },
    { id: 3, name: 'Шиномонтаж', price: 4000, duration: '60 мин', category: 'wheels' },
    { id: 4, name: 'Промывка системы', price: 6500, duration: '120 мин', category: 'maintenance' },
    { id: 5, name: 'Замена тормозных колодок', price: 8500, duration: '90 мин', category: 'brakes' }
  ]);

  const maintenanceData = [
    { name: 'Замена масла', lastService: 42000, nextService: 50000, status: 'warning', urgency: 85 },
    { name: 'Тормозная жидкость', lastService: 35000, nextService: 60000, status: 'good', urgency: 20 },
    { name: 'Воздушный фильтр', lastService: 38000, nextService: 45000, status: 'critical', urgency: 95 },
    { name: 'Свечи зажигания', lastService: 20000, nextService: 80000, status: 'good', urgency: 5 },
    { name: 'Ремень ГРМ', lastService: 0, nextService: 100000, status: 'good', urgency: 10 }
  ];

  const analyticsData = [
    { month: 'Янв', spent: 12500, visits: 2, bonus: 875 },
    { month: 'Фев', spent: 8300, visits: 1, bonus: 581 },
    { month: 'Мар', spent: 15600, visits: 3, bonus: 1092 },
    { month: 'Апр', spent: 11200, visits: 2, bonus: 784 },
    { month: 'Май', spent: 18900, visits: 4, bonus: 1323 },
    { month: 'Июн', spent: 9800, visits: 1, bonus: 686 }
  ];

  const loyaltyLevels = {
    bronze: { name: 'Бронза', bonus: 5, discount: 30, color: '#cd7f32', min: 0 },
    silver: { name: 'Серебро', bonus: 7, discount: 35, color: '#c0c0c0', min: 15000 },
    gold: { name: 'Золото', bonus: 10, discount: 40, color: '#ffd700', min: 40000 },
    platinum: { name: 'Платина', bonus: 15, discount: 50, color: '#e5e4e2', min: 100000 }
  };

  const getLoyaltyProgress = () => {
    const current = loyaltyLevels[user.loyaltyLevel];
    const levels = Object.keys(loyaltyLevels);
    const currentIndex = levels.indexOf(user.loyaltyLevel);
    const nextLevel = levels[currentIndex + 1];
    
    if (!nextLevel) return { progress: 100, nextLevel: null, needed: 0 };
    
    const nextMin = loyaltyLevels[nextLevel].min;
    const currentMin = current.min;
    const progress = ((user.totalSpent - currentMin) / (nextMin - currentMin)) * 100;
    
    return { 
      progress: Math.min(progress, 100), 
      nextLevel: loyaltyLevels[nextLevel].name,
      needed: Math.max(0, nextMin - user.totalSpent)
    };
  };

  const categoryColors = {
    maintenance: '#f59e0b',
    diagnostic: '#3b82f6',
    wheels: '#10b981',
    brakes: '#ef4444'
  };

  const pages = {
    dashboard: 'Главная',
    vehicles: 'Автомобили',
    services: 'Услуги',
    maintenance: 'ТО',
    analytics: 'Аналитика',
    booking: 'Запись',
    profile: 'Профиль'
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'critical': return 'text-red-400 bg-red-900/20';
      case 'warning': return 'text-yellow-400 bg-yellow-900/20';
      case 'good': return 'text-green-400 bg-green-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const formatMoney = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const renderDashboard = () => (
    <div className="space-y-4 md:space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-xl md:rounded-2xl bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-700 p-4 md:p-8 shadow-lg">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-xl md:text-3xl font-bold text-white mb-2">
                Илья! {/* Используем имя из скриншота */}
                <span className="ml-2 text-xl">👋</span>
              </h1>
              <p className="text-blue-100 text-sm md:text-lg">
                Ваш премиум автосервис всегда готов помочь
              </p>
            </div>
            <div className="text-left md:text-right">
              <div className="text-2xl md:text-4xl font-bold text-white">
                {formatMoney(100)} {/* Используем значение из скриншота */}
              </div>
              <div className="text-blue-100 text-sm md:text-base">Бонусы</div>
            </div>
          </div>
        </div>
        <div className="absolute top-0 right-0 w-32 h-32 md:w-64 md:h-64 opacity-10">
          <div className="w-full h-full rounded-full bg-white blur-3xl"></div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg md:rounded-xl p-3 md:p-6 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-xs md:text-sm">Уровень лояльности</p>
              <p className="text-lg md:text-2xl font-bold text-white capitalize">
                {loyaltyLevels[user.loyaltyLevel].name}
              </p>
            </div>
            <div className="w-8 h-8 md:w-12 md:h-12 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center">
              <span className="text-lg md:text-2xl">👑</span>
            </div>
          </div>
          <div className="mt-4">
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${getLoyaltyProgress().progress}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-400 mt-2 hidden md:block">
              До следующего уровня: {formatMoney(getLoyaltyProgress().needed)}
            </p>
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg md:rounded-xl p-3 md:p-6 border border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-xs md:text-sm">Посещений</p>
              <p className="text-lg md:text-2xl font-bold text-white">{user.visits}</p>
            </div>
            <div className="w-8 h-8 md:w-12 md:h-12 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center">
              <span className="text-lg md:text-2xl">🔧</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg md:rounded-xl p-3 md:p-6 border border-gray-700/50 col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-xs md:text-sm">Потрачено всего</p>
              <p className="text-lg md:text-2xl font-bold text-white">{formatMoney(user.totalSpent)}</p>
            </div>
            <div className="w-8 h-8 md:w-12 md:h-12 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 flex items-center justify-center">
              <span className="text-lg md:text-2xl">💰</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg md:rounded-xl p-3 md:p-6 border border-gray-700/50 col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-xs md:text-sm">Следующее ТО</p>
              <p className="text-lg md:text-2xl font-bold text-white">
                {Math.ceil((user.nextService - new Date()) / (1000 * 60 * 60 * 24))} дней
              </p>
            </div>
            <div className="w-8 h-8 md:w-12 md:h-12 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center">
              <span className="text-lg md:text-2xl">⏰</span>
            </div>
          </div>
        </div>
      </div>

      {/* Active Vehicle */}
      {vehicles.filter(v => v.isActive).map(vehicle => (
        <div key={vehicle.id} className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-4">Активный автомобиль</h3>
          <div className="flex items-center space-x-6">
            <div className="w-20 h-20 rounded-xl flex items-center justify-center text-4xl"
                 style={{ backgroundColor: vehicle.color + '20', color: vehicle.color }}>
              🚗
            </div>
            <div className="flex-1">
              <h4 className="text-lg font-semibold text-white">
                {vehicle.brand} {vehicle.model} {vehicle.year}
              </h4>
              <p className="text-gray-400">VIN: {vehicle.vin}</p>
              <div className="flex items-center space-x-4 mt-2">
                <span className="text-sm text-gray-300">
                  Пробег: {vehicle.mileage.toLocaleString()} км
                </span>
                <span className="text-sm text-gray-300">
                  До ТО: {(vehicle.nextService - vehicle.mileage).toLocaleString()} км
                </span>
              </div>
            </div>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
              Записаться на ТО
            </button>
          </div>
        </div>
      ))}

      {/* Recent Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-4">Динамика трат</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={analyticsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Line type="monotone" dataKey="spent" stroke="#3B82F6" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-4">Критичные работы ТО</h3>
          <div className="space-y-3">
            {maintenanceData.filter(item => item.urgency > 80).map((item, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-red-900/20 rounded-lg border border-red-700/30">
                <div>
                  <p className="text-white font-medium">{item.name}</p>
                  <p className="text-red-400 text-sm">Требует внимания</p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-red-400 text-sm">{item.urgency}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderVehicles = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Мои автомобили</h2>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
          + Добавить автомобиль
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {vehicles.map(vehicle => (
          <div key={vehicle.id} className={`bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border transition-all duration-300 hover:scale-105 ${
            vehicle.isActive ? 'border-blue-500/50 ring-2 ring-blue-500/20' : 'border-gray-700/50'
          }`}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl"
                     style={{ backgroundColor: vehicle.color + '20', color: vehicle.color }}>
                  🚗
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">
                    {vehicle.brand} {vehicle.model}
                  </h3>
                  <p className="text-gray-400">{vehicle.year} год</p>
                  {vehicle.isActive && (
                    <span className="inline-block px-2 py-1 bg-green-600/20 text-green-400 text-xs rounded-full mt-1">
                      Активный
                    </span>
                  )}
                </div>
              </div>
              <button className="text-gray-400 hover:text-white">⚙️</button>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">VIN:</span>
                <span className="text-white font-mono text-sm">{vehicle.vin}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Пробег:</span>
                <span className="text-white">{vehicle.mileage.toLocaleString()} км</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">До ТО:</span>
                <span className={`font-medium ${
                  vehicle.nextService - vehicle.mileage < 5000 ? 'text-red-400' : 'text-green-400'
                }`}>
                  {(vehicle.nextService - vehicle.mileage).toLocaleString()} км
                </span>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-700/50">
              <div className="flex space-x-2">
                <button className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">
                  Записаться на ТО
                </button>
                <button className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors">
                  История
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderServices = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <h2 className="text-2xl font-bold text-white">Каталог услуг</h2>
      
      <div className="flex flex-wrap gap-2 mb-6">
        {['Все', 'Техобслуживание', 'Диагностика', 'Шиномонтаж', 'Тормоза'].map(category => (
          <button key={category} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
            {category}
          </button>
        ))}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {services.map(service => (
          <div key={service.id} className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                   style={{ backgroundColor: categoryColors[service.category] + '20', color: categoryColors[service.category] }}>
                {service.category === 'maintenance' ? '🔧' : 
                 service.category === 'diagnostic' ? '🔍' :
                 service.category === 'wheels' ? '🛞' :
                 service.category === 'brakes' ? '🛑' : '⚙️'}
              </div>
              <span className="text-2xl font-bold text-white">{formatMoney(service.price)}</span>
            </div>
            
            <h3 className="text-lg font-semibold text-white mb-2">{service.name}</h3>
            <p className="text-gray-400 mb-4">Время выполнения: {service.duration}</p>
            
            <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
              Записаться
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMaintenance = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <h2 className="text-2xl font-bold text-white">Техническое обслуживание</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {maintenanceData.map((item, index) => (
            <div key={index} className={`bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border ${
              item.status === 'critical' ? 'border-red-500/50' :
              item.status === 'warning' ? 'border-yellow-500/50' : 'border-gray-700/50'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">{item.name}</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                  {item.status === 'critical' ? 'Критично' :
                   item.status === 'warning' ? 'Скоро' : 'В порядке'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-gray-400 text-sm">Последнее ТО</p>
                  <p className="text-white font-medium">
                    {item.lastService === 0 ? 'Не выполнялось' : `${item.lastService.toLocaleString()} км`}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Следующее ТО</p>
                  <p className="text-white font-medium">{item.nextService.toLocaleString()} км</p>
                </div>
              </div>
              
              <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-500 ${
                    item.urgency > 80 ? 'bg-red-500' :
                    item.urgency > 50 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${item.urgency}%` }}
                ></div>
              </div>
              <p className="text-gray-400 text-xs">Срочность: {item.urgency}%</p>
            </div>
          ))}
        </div>
        
        <div className="space-y-6">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Статистика ТО</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Выполнено', value: 65, fill: '#10B981' },
                    { name: 'Требует внимания', value: 25, fill: '#F59E0B' },
                    { name: 'Критично', value: 10, fill: '#EF4444' }
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  dataKey="value"
                >
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Быстрые действия</h3>
            <div className="space-y-3">
              <button className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                📅 Записаться на ТО
              </button>
              <button className="w-full px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
                📝 Добавить запись
              </button>
              <button className="w-full px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
                📊 Полный отчет
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <h2 className="text-2xl font-bold text-white">Аналитика и статистика</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Траты по месяцам</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Bar dataKey="spent" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Накопление бонусов</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }}
                labelStyle={{ color: '#F3F4F6' }}
              />
              <Line type="monotone" dataKey="bonus" stroke="#10B981" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-2xl font-bold text-white">{formatMoney(analyticsData.reduce((sum, item) => sum + item.spent, 0))}</div>
          <div className="text-gray-400">Общие траты за полгода</div>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">🎁</div>
          <div className="text-2xl font-bold text-white">{analyticsData.reduce((sum, item) => sum + item.bonus, 0)}</div>
          <div className="text-gray-400">Бонусов накоплено</div>
        </div>
        
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50 text-center">
          <div className="text-3xl mb-2">⚡</div>
          <div className="text-2xl font-bold text-white">{(analyticsData.reduce((sum, item) => sum + item.spent, 0) / analyticsData.reduce((sum, item) => sum + item.visits, 0)).toFixed(0)}</div>
          <div className="text-gray-400">Средний чек (₽)</div>
        </div>
      </div>
    </div>
  );

  const renderBooking = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <h2 className="text-2xl font-bold text-white">Онлайн-запись</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {/* Service Selection */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">1. Выберите услугу</h3>
            <div className="space-y-3">
              {services.slice(0, 3).map(service => (
                <div key={service.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 cursor-pointer transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center text-lg"
                         style={{ backgroundColor: categoryColors[service.category] + '20', color: categoryColors[service.category] }}>
                      {service.category === 'maintenance' ? '🔧' : 
                       service.category === 'diagnostic' ? '🔍' : '⚙️'}
                    </div>
                    <div>
                      <p className="text-white font-medium">{service.name}</p>
                      <p className="text-gray-400 text-sm">{service.duration}</p>
                    </div>
                  </div>
                  <span className="text-white font-bold">{formatMoney(service.price)}</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Date Selection */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">2. Выберите дату</h3>
            <div className="grid grid-cols-7 gap-2">
              {Array.from({length: 14}, (_, i) => {
                const date = new Date();
                date.setDate(date.getDate() + i);
                return (
                  <button key={i} className="p-2 text-center bg-gray-700/30 hover:bg-blue-600 text-white rounded-lg transition-colors">
                    <div className="text-xs">{date.toLocaleDateString('ru-RU', { weekday: 'short' })}</div>
                    <div className="font-bold">{date.getDate()}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          {/* Time Selection */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">3. Выберите время</h3>
            <div className="grid grid-cols-3 gap-2">
              {['09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00', '17:00', '18:00'].map(time => (
                <button key={time} className="p-3 bg-gray-700/30 hover:bg-blue-600 text-white rounded-lg transition-colors">
                  {time}
                </button>
              ))}
            </div>
          </div>
          
          {/* Booking Summary */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Детали записи</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Услуга:</span>
                <span className="text-white">Замена масла</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Дата:</span>
                <span className="text-white">Сегодня</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Время:</span>
                <span className="text-white">10:00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Автомобиль:</span>
                <span className="text-white">BMW X5</span>
              </div>
              <div className="border-t border-gray-700 pt-3 flex justify-between">
                <span className="text-gray-400">Стоимость:</span>
                <span className="text-white font-bold">3 500 ₽</span>
              </div>
            </div>
            
            <button className="w-full mt-6 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
              Подтвердить запись
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderProfile = () => (
    <div className="space-y-6 pb-16 md:pb-0">  {/* Добавляем отступ снизу для мобильной навигации */}
      <h2 className="text-2xl font-bold text-white">Профиль пользователя</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Info */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Личная информация</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Имя</label>
                  <input type="text" value={user.name} className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none" />
                </div>
                <div>
                  <label className="block text-gray-400 text-sm mb-2">Телефон</label>
                  <input type="text" value={user.phone} className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none" />
                </div>
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-2">Email</label>
                <input type="email" placeholder="example@email.com" className="w-full p-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none" />
              </div>
            </div>
          </div>
          
          {/* Notification Settings */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Уведомления</h3>
            <div className="space-y-4">
              {[
                { name: 'Напоминания о ТО', enabled: true },
                { name: 'Специальные предложения', enabled: true },
                { name: 'Статус записи', enabled: true },
                { name: 'Начисление бонусов', enabled: false }
              ].map((setting, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-white">{setting.name}</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked={setting.enabled} />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          {/* Loyalty Status */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Статус лояльности</h3>
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center text-3xl">
                👑
              </div>
              <h4 className="text-xl font-bold text-white capitalize mb-2">
                {loyaltyLevels[user.loyaltyLevel].name}
              </h4>
              <p className="text-gray-400 mb-4">
                {loyaltyLevels[user.loyaltyLevel].bonus}% бонусов • до {loyaltyLevels[user.loyaltyLevel].discount}% скидка
              </p>
              <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div 
                  className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${getLoyaltyProgress().progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-400">
                {getLoyaltyProgress().nextLevel ? 
                  `До ${getLoyaltyProgress().nextLevel}: ${formatMoney(getLoyaltyProgress().needed)}` :
                  'Максимальный уровень достигнут!'
                }
              </p>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">Быстрые действия</h3>
            <div className="space-y-3">
              <button className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                📱 Скачать QR-код
              </button>
              <button className="w-full px-4 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors">
                📊 Экспорт данных
              </button>
              <button className="w-full px-4 py-3 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors">
                🚪 Выйти из аккаунта
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPage = () => {
    switch(currentPage) {
      case 'dashboard': return renderDashboard();
      case 'vehicles': return renderVehicles();
      case 'services': return renderServices();
      case 'maintenance': return renderMaintenance();
      case 'analytics': return renderAnalytics();
      case 'booking': return renderBooking();
      case 'profile': return renderProfile();
      default: return renderDashboard();
    }
  };

  // Добавляем эффект для управления отображением боковой панели на мобильных устройствах
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsMobileMenuOpen(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Функция для мобильного меню
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button 
                onClick={toggleMobileMenu}
                className="md:hidden p-1 rounded-md text-gray-400 hover:text-white focus:outline-none"
              >
                {isMobileMenuOpen ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                )}
              </button>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
                🚗
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">AutoService</h1>
                <p className="text-xs text-gray-400">Премиум-сервис</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-2 bg-gray-800/50 rounded-lg px-3 py-2">
                <span className="text-2xl">💰</span>
                <span className="text-white font-bold">{formatMoney(user.bonusBalance)}</span>
              </div>
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                {user.name.split(' ').map(n => n[0]).join('')}
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 relative overflow-hidden">
        {/* Sidebar для мобильных устройств (выдвигается) */}
        <aside 
          className={`absolute md:relative md:translate-x-0 w-64 bg-gray-900/95 md:bg-gray-900/50 backdrop-blur-sm border-r border-gray-700/50 p-4 h-full z-40 transition-transform duration-300 ease-in-out ${
            isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <nav className="space-y-2">
            {Object.entries(pages).map(([key, label]) => (
              <button
                key={key}
                onClick={() => {
                  setCurrentPage(key);
                  if (window.innerWidth < 768) {
                    setIsMobileMenuOpen(false);
                  }
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  currentPage === key
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800/50 hover:text-white'
                }`}
              >
                <span className="text-xl">
                  {key === 'dashboard' ? '🏠' :
                   key === 'vehicles' ? '🚗' :
                   key === 'services' ? '🛠️' :
                   key === 'maintenance' ? '🔧' :
                   key === 'analytics' ? '📊' :
                   key === 'booking' ? '📅' :
                   key === 'profile' ? '👤' : '📋'}
                </span>
                <span className="font-medium">{label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Затемнение фона при открытом мобильном меню */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-30 md:hidden"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">
          {renderPage()}
        </main>
      </div>

      {/* Мобильная нижняя навигация */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-700/50 p-2 z-50">
        <div className="flex justify-around">
          {Object.entries(pages).slice(0, 5).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setCurrentPage(key)}
              className={`flex flex-col items-center justify-center p-2 rounded-lg ${
                currentPage === key ? 'text-blue-500' : 'text-gray-400 hover:text-white'
              }`}
            >
              <span className="text-xl">
                {key === 'dashboard' ? '🏠' :
                 key === 'vehicles' ? '🚗' :
                 key === 'services' ? '🛠️' :
                 key === 'maintenance' ? '🔧' :
                 key === 'analytics' ? '📊' :
                 key === 'booking' ? '📅' :
                 key === 'profile' ? '👤' : '📋'}
              </span>
              <span className="text-xs mt-1">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AutoServiceApp;
