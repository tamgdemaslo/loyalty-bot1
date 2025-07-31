#!/usr/bin/env python3
"""
Система сегментации клиентов
RFM-анализ + дополнительные метрики для системы лояльности
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CustomerSegmentation:
    def __init__(self, db_path='loyalty.db'):
        """
        Инициализация системы сегментации
        """
        self.db_path = db_path
        self.segments_config = {
            # RFM сегменты
            'Champions': {'R': [4, 5], 'F': [4, 5], 'M': [4, 5]},
            'Loyal Customers': {'R': [2, 5], 'F': [3, 5], 'M': [3, 5]},
            'Potential Loyalists': {'R': [3, 5], 'F': [1, 3], 'M': [1, 3]},
            'New Customers': {'R': [4, 5], 'F': [1, 1], 'M': [1, 1]},
            'Promising': {'R': [3, 4], 'F': [1, 1], 'M': [1, 1]},
            'Need Attention': {'R': [2, 3], 'F': [2, 3], 'M': [2, 3]},
            'About to Sleep': {'R': [2, 3], 'F': [1, 2], 'M': [1, 2]},
            'At Risk': {'R': [1, 2], 'F': [2, 5], 'M': [2, 5]},
            'Cannot Lose Them': {'R': [1, 2], 'F': [4, 5], 'M': [4, 5]},
            'Hibernating': {'R': [1, 2], 'F': [1, 2], 'M': [1, 2]}
        }
        
    def get_rfm_data(self):
        """
        Получение данных для RFM-анализа
        """
        logger.info("Получение данных для RFM-анализа...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Основной запрос для RFM-данных
        query = """
        WITH rfm_base AS (
            SELECT 
                c.agent_id,
                c.name as customer_name,
                c.phone,
                c.email,
                COALESCE(b.balance, 0) as bonus_balance,
                COALESCE(l.level_id, 1) as loyalty_level,
                CASE WHEN u.agent_id IS NOT NULL THEN 1 ELSE 0 END as is_registered,
                
                -- Recency: дни с последней покупки
                COALESCE(
                    CAST(
                        (julianday('now') - julianday(MAX(s.moment))) 
                        AS INTEGER
                    ), 999
                ) as recency_days,
                
                -- Frequency: количество покупок
                COALESCE(COUNT(s.demand_id), 0) as frequency,
                
                -- Monetary: общая потраченная сумма (в копейках)
                COALESCE(SUM(CAST(s.sum AS INTEGER)), 0) as monetary_total,
                
                -- Дополнительные метрики
                AVG(CAST(s.sum AS INTEGER)) as avg_order_value,
                MIN(s.moment) as first_purchase_date,
                MAX(s.moment) as last_purchase_date,
                COUNT(DISTINCT DATE(s.moment)) as purchase_days_count
                
            FROM contractors_data c
            LEFT JOIN contractor_shipments s ON c.agent_id = s.agent_id 
                AND s.state_name = 'Оплачено'
            LEFT JOIN bonuses b ON c.agent_id = b.agent_id
            LEFT JOIN loyalty_levels l ON c.agent_id = l.agent_id
            LEFT JOIN user_map u ON c.agent_id = u.agent_id
            GROUP BY c.agent_id, c.name, c.phone, c.email, b.balance, l.level_id, u.agent_id
        )
        SELECT * FROM rfm_base
        ORDER BY monetary_total DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        logger.info(f"Загружено {len(df)} записей клиентов")
        return df
    
    def calculate_rfm_scores(self, df):
        """
        Расчет RFM-скоров (1-5 для каждой метрики)
        """
        logger.info("Расчет RFM-скоров...")
        
        # Создаем копию для избежания предупреждений
        df_rfm = df.copy()
        
        # Фильтруем только клиентов с покупками
        df_customers = df_rfm[df_rfm['frequency'] > 0].copy()
        
        if len(df_customers) == 0:
            logger.warning("Нет клиентов с покупками для RFM-анализа")
            return df_rfm
        
        # Для Recency: меньше дней = выше скор (инвертируем)
        df_customers['R_score'] = pd.qcut(
            df_customers['recency_days'], 
            q=5, labels=[5, 4, 3, 2, 1]
        ).astype(int)
        
        # Для Frequency: больше покупок = выше скор
        df_customers['F_score'] = pd.qcut(
            df_customers['frequency'].rank(method='first'), 
            q=5, labels=[1, 2, 3, 4, 5]
        ).astype(int)
        
        # Для Monetary: больше потрачено = выше скор
        df_customers['M_score'] = pd.qcut(
            df_customers['monetary_total'].rank(method='first'), 
            q=5, labels=[1, 2, 3, 4, 5]
        ).astype(int)
        
        # Объединяем обратно с полным датасетом
        df_rfm = df_rfm.merge(
            df_customers[['agent_id', 'R_score', 'F_score', 'M_score']], 
            on='agent_id', 
            how='left'
        )
        
        # Для клиентов без покупок устанавливаем минимальные скоры
        df_rfm[['R_score', 'F_score', 'M_score']] = df_rfm[['R_score', 'F_score', 'M_score']].fillna(1)
        
        # Создаем RFM-код
        df_rfm['RFM_code'] = (
            df_rfm['R_score'].astype(str) + 
            df_rfm['F_score'].astype(str) + 
            df_rfm['M_score'].astype(str)
        )
        
        logger.info("RFM-скоры рассчитаны")
        return df_rfm
    
    def assign_segments(self, df):
        """
        Присвоение сегментов на основе RFM-скоров
        """
        logger.info("Присвоение сегментов...")
        
        def get_segment(r, f, m):
            for segment, criteria in self.segments_config.items():
                if (criteria['R'][0] <= r <= criteria['R'][1] and
                    criteria['F'][0] <= f <= criteria['F'][1] and
                    criteria['M'][0] <= m <= criteria['M'][1]):
                    return segment
            return 'Other'
        
        df['segment'] = df.apply(
            lambda row: get_segment(row['R_score'], row['F_score'], row['M_score']), 
            axis=1
        )
        
        logger.info("Сегменты присвоены")
        return df
    
    def calculate_additional_metrics(self, df):
        """
        Расчет дополнительных метрик для сегментации
        """
        logger.info("Расчет дополнительных метрик...")
        
        # Customer Lifetime Value (примерная оценка)
        df['clv_estimate'] = df['avg_order_value'] * df['frequency'] * 2  # умножаем на 2 как прогноз
        
        # Активность (покупок в месяц)
        df['purchase_frequency_monthly'] = df.apply(
            lambda row: self._calculate_monthly_frequency(row), axis=1
        )
        
        # Статус активности
        df['activity_status'] = df['recency_days'].apply(
            lambda x: 'Active' if x <= 30 else 
                     'Declining' if x <= 90 else 
                     'Inactive' if x <= 365 else 'Lost'
        )
        
        # Потенциал роста
        df['growth_potential'] = df.apply(
            lambda row: self._calculate_growth_potential(row), axis=1
        )
        
        return df
    
    def _calculate_monthly_frequency(self, row):
        """Расчет частоты покупок в месяц"""
        if row['frequency'] == 0 or pd.isna(row['first_purchase_date']):
            return 0
        
        try:
            first_date = datetime.strptime(row['first_purchase_date'], '%Y-%m-%d %H:%M:%S.%f')
            months_active = max(1, (datetime.now() - first_date).days / 30.44)  # среднее дней в месяце
            return round(row['frequency'] / months_active, 2)
        except:
            return 0
    
    def _calculate_growth_potential(self, row):
        """Расчет потенциала роста клиента"""
        if row['frequency'] == 0:
            return 'Unknown'
        
        if row['R_score'] >= 4 and row['F_score'] <= 2:
            return 'High'  # недавно покупал, но редко
        elif row['R_score'] >= 3 and row['M_score'] <= 2:
            return 'Medium'  # относительно недавно, но мало тратит
        elif row['R_score'] <= 2 and row['F_score'] >= 3:
            return 'Low'   # давно не покупал, но раньше был активен
        else:
            return 'Stable'
    
    def save_segmentation_results(self, df):
        """
        Сохранение результатов сегментации в базу данных
        """
        logger.info("Сохранение результатов сегментации...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Создаем таблицу для сегментации
        conn.execute("""
        CREATE TABLE IF NOT EXISTS customer_segments (
            agent_id TEXT PRIMARY KEY,
            customer_name TEXT,
            phone TEXT,
            email TEXT,
            bonus_balance INTEGER DEFAULT 0,
            loyalty_level INTEGER DEFAULT 1,
            is_registered INTEGER DEFAULT 0,
            
            -- RFM метрики
            recency_days INTEGER,
            frequency INTEGER,
            monetary_total INTEGER,
            R_score INTEGER,
            F_score INTEGER,
            M_score INTEGER,
            RFM_code TEXT,
            segment TEXT,
            
            -- Дополнительные метрики
            avg_order_value REAL,
            clv_estimate REAL,
            purchase_frequency_monthly REAL,
            activity_status TEXT,
            growth_potential TEXT,
            first_purchase_date TEXT,
            last_purchase_date TEXT,
            purchase_days_count INTEGER,
            
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Очищаем старые данные
        conn.execute("DELETE FROM customer_segments")
        
        # Сохраняем новые данные
        df.to_sql('customer_segments', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Сохранено {len(df)} записей сегментации")
    
    def generate_segment_report(self, df):
        """
        Генерация отчета по сегментам
        """
        logger.info("Генерация отчета по сегментам...")
        
        # Общая статистика
        total_customers = len(df)
        active_customers = len(df[df['frequency'] > 0])
        total_revenue = df['monetary_total'].sum()
        
        # Статистика по сегментам
        segment_stats = df.groupby('segment').agg({
            'agent_id': 'count',
            'monetary_total': ['sum', 'mean'],
            'frequency': 'mean',
            'recency_days': 'mean',
            'bonus_balance': 'sum',
            'is_registered': 'sum'
        }).round(2)
        
        segment_stats.columns = [
            'customers_count', 'total_revenue', 'avg_revenue', 
            'avg_frequency', 'avg_recency', 'total_bonuses', 'registered_count'
        ]
        
        # Добавляем процент от общего числа клиентов
        segment_stats['percentage'] = (segment_stats['customers_count'] / total_customers * 100).round(1)
        
        # Статистика по активности
        activity_stats = df['activity_status'].value_counts()
        
        # Статистика по потенциалу роста
        growth_stats = df['growth_potential'].value_counts()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_customers': total_customers,
            'active_customers': active_customers,
            'total_revenue_kopecks': int(total_revenue),
            'total_revenue_rubles': total_revenue / 100,
            'segments': segment_stats.to_dict('index'),
            'activity_distribution': activity_stats.to_dict(),
            'growth_potential_distribution': growth_stats.to_dict()
        }
        
        # Сохраняем отчет в файл
        report_path = f"segmentation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Отчет сохранен в {report_path}")
        
        # Выводим краткую сводку
        print("\n" + "="*80)
        print("📊 ОТЧЕТ ПО СЕГМЕНТАЦИИ КЛИЕНТОВ")
        print("="*80)
        print(f"Всего клиентов: {total_customers:,}")
        print(f"Активных клиентов: {active_customers:,}")
        print(f"Общая выручка: {total_revenue/100:,.2f} ₽")
        print("\n🎯 РАСПРЕДЕЛЕНИЕ ПО СЕГМЕНТАМ:")
        print("-"*60)
        
        for segment, stats in segment_stats.iterrows():
            print(f"{segment:20} | {int(stats['customers_count']):4d} ({stats['percentage']:5.1f}%) | "
                  f"{stats['total_revenue']/100:10,.0f} ₽")
        
        print("\n⚡ СТАТУС АКТИВНОСТИ:")
        print("-"*40)
        for status, count in activity_stats.items():
            print(f"{status:15} | {count:4d} ({count/total_customers*100:5.1f}%)")
        
        return report
    
    def run_full_segmentation(self):
        """
        Запуск полной сегментации
        """
        logger.info("🚀 Запуск полной сегментации клиентов...")
        
        try:
            # 1. Получение данных
            df = self.get_rfm_data()
            
            # 2. Расчет RFM-скоров
            df = self.calculate_rfm_scores(df)
            
            # 3. Присвоение сегментов
            df = self.assign_segments(df)
            
            # 4. Дополнительные метрики
            df = self.calculate_additional_metrics(df)
            
            # 5. Сохранение результатов
            self.save_segmentation_results(df)
            
            # 6. Генерация отчета
            report = self.generate_segment_report(df)
            
            logger.info("✅ Сегментация завершена успешно!")
            return df, report
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сегментации: {e}")
            raise

def main():
    """
    Главная функция
    """
    print("🔄 Система сегментации клиентов")
    print("="*50)
    
    segmentator = CustomerSegmentation()
    df, report = segmentator.run_full_segmentation()
    
    print("\n🎉 Сегментация завершена!")
    print(f"📁 Результаты сохранены в базу данных")
    print(f"📊 Создан отчет: segmentation_report_*.json")

if __name__ == "__main__":
    main()
