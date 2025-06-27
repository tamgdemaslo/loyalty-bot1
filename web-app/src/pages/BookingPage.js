import React from 'react';
import { Calendar, Clock, Phone } from 'lucide-react';

const BookingPage = ({ user }) => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Запись на услуги</h1>
      
      {/* Coming Soon Card */}
      <div className="card text-center py-12">
        <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <Calendar className="w-10 h-10 text-primary-600" />
        </div>
        
        <h2 className="text-xl font-semibold text-gray-900 mb-3">
          Онлайн запись скоро будет доступна
        </h2>
        
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          Мы работаем над удобной системой онлайн записи. 
          Пока что вы можете записаться по телефону.
        </p>
        
        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 max-w-sm mx-auto">
          <div className="flex items-center space-x-3 justify-center">
            <Phone className="w-5 h-5 text-primary-600" />
            <div>
              <p className="font-medium text-primary-900">Записаться по телефону</p>
              <p className="text-primary-700">+7 (xxx) xxx-xx-xx</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Services Preview */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Наши услуги</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: 'Диагностика автомобиля', duration: '30-60 мин', icon: '🔧' },
            { name: 'Замена масла', duration: '20-30 мин', icon: '🛢️' },
            { name: 'Шиномонтаж', duration: '30-45 мин', icon: '🚗' },
            { name: 'Техническое обслуживание', duration: '60-120 мин', icon: '⚙️' },
          ].map((service, index) => (
            <div key={index} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{service.icon}</span>
                <div>
                  <h4 className="font-medium text-gray-900">{service.name}</h4>
                  <div className="flex items-center space-x-1 mt-1">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">{service.duration}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BookingPage;
