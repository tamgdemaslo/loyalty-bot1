import React from 'react';
import { User, Phone, Award, Star } from 'lucide-react';
import { formatPhone, getLevelName, getLevelColor } from '../utils/formatters';

const ProfilePage = ({ user }) => {
  const levelColor = getLevelColor(user?.level_id || 1);
  
  return (
    <div className="space-y-6">
      <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">Профиль</h1>
      
      {/* User Info Card */}
      <div className="card">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-primary-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{user?.fullname}</h2>
            <p className="text-gray-600">{formatPhone(user?.phone)}</p>
          </div>
        </div>
        
        {/* Level Info */}
        <div className={`bg-gradient-to-r from-${levelColor}-50 to-${levelColor}-100 rounded-lg p-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className={`w-12 h-12 bg-${levelColor}-500 rounded-full flex items-center justify-center`}>
                <Award className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Уровень лояльности</p>
                <p className="text-2xl font-bold text-gray-900">{getLevelName(user?.level_id || 1)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-3xl font-bold text-primary-600">{user?.level_id || 1}</p>
              <p className="text-sm text-gray-500">из 5</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Program Benefits */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Преимущества программы</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4, 5].map(level => (
            <div 
              key={level}
              className={`p-4 rounded-lg border-2 ${
                level === (user?.level_id || 1) 
                  ? 'border-primary-500 bg-primary-50' 
                  : 'border-gray-200 bg-gray-50'
              }`}
            >
              <div className="flex items-center space-x-3 mb-2">
                <Star className={`w-5 h-5 ${level === (user?.level_id || 1) ? 'text-primary-600' : 'text-gray-400'}`} />
                <span className="font-medium">{getLevelName(level)}</span>
              </div>
              <p className="text-sm text-gray-600">Кэшбек {level * 2}% с каждой покупки</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
