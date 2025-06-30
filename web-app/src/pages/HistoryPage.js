import React from 'react';
import { ShoppingBag, Calendar, Package } from 'lucide-react';

const HistoryPage = ({ user }) => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">История покупок</h1>
      
      {/* Empty State */}
      <div className="card text-center py-12">
        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <ShoppingBag className="w-10 h-10 text-gray-400" />
        </div>
        
        <h2 className="text-xl font-semibold text-gray-900 mb-3">
          История покупок пуста
        </h2>
        
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          Здесь будет отображаться история ваших покупок и услуг в нашем автосервисе.
        </p>
      </div>
      
      {/* Info Card */}
      <div className="card bg-green-50 border border-green-200">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center flex-shrink-0">
            <Package className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-medium text-green-900 mb-2">Что отображается в истории?</h3>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• Все ваши покупки запчастей и расходников</li>
              <li>• Услуги технического обслуживания</li>
              <li>• Детальная информация о каждой операции</li>
              <li>• Начисленные за покупки бонусы</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoryPage;
