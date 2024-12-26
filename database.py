import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Создаем таблицу пользователей
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0
            )
        ''')
        
        # Проверяем существование таблицы products
        table_exists = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products'"
        ).fetchone() is not None
        
        if not table_exists:
            # Если таблицы нет, создаем её со всеми колонками
            self.cursor.execute('''
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    price REAL,
                    city TEXT,
                    district TEXT,
                    pickup_point TEXT
                )
            ''')
        
        # Создаем таблицу заказов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE,
                user_id INTEGER,
                product_id INTEGER,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )
        ''')
        
        # Добавим таблицу для отслеживания созданных ботов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS created_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                bot_username TEXT,
                token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()
    
    def add_user(self, user_id, username):
        self.cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        self.connection.commit()
    
    def get_user(self, user_id):
        return self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    def add_product(self, name, description, price, city, district, pickup_point):
        self.cursor.execute(
            'INSERT INTO products (name, description, price, city, district, pickup_point) VALUES (?, ?, ?, ?, ?, ?)',
            (name, description, price, city, district, pickup_point)
        )
        self.connection.commit()
    
    def get_all_products(self, city=None):
        if city:
            return self.cursor.execute('SELECT * FROM products WHERE city = ?', (city,)).fetchall()
        return self.cursor.execute('SELECT * FROM products').fetchall()
    
    def get_product(self, product_id):
        return self.cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    def add_order(self, order_id, user_id, product_id):
        self.cursor.execute(
            'INSERT INTO orders (order_id, user_id, product_id, status) VALUES (?, ?, ?, ?)',
            (order_id, user_id, product_id, 'pending')
        )
        self.connection.commit()
    
    def update_balance(self, user_id, amount):
        self.cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        self.connection.commit() 
    
    def get_stats(self):
        # Общее количество пользователей
        total_users = self.cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        
        # Общее количество товаров
        total_products = self.cursor.execute('SELECT COUNT(*) FROM products').fetchall()[0][0]
        
        # Количество заказов
        total_orders = self.cursor.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        
        # Сумма всех заказов
        total_sum = self.cursor.execute('''
            SELECT SUM(products.price) 
            FROM orders 
            JOIN products ON orders.product_id = products.id
        ''').fetchone()[0] or 0
        
        # Статистика по городам
        city_stats = self.cursor.execute('''
            SELECT city, COUNT(*) as count 
            FROM products 
            GROUP BY city
        ''').fetchall()
        
        # Добавляем статистику по созданным ботам
        total_bots = self.cursor.execute('SELECT COUNT(*) FROM created_bots').fetchone()[0]
        top_creators = self.cursor.execute('''
            SELECT users.username, COUNT(*) as bot_count
            FROM created_bots
            JOIN users ON created_bots.creator_id = users.user_id
            GROUP BY creator_id
            ORDER BY bot_count DESC
            LIMIT 5
        ''').fetchall()
        
        return {
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'total_sum': total_sum,
            'city_stats': city_stats,
            'total_bots': total_bots,
            'top_creators': top_creators
        }
    
    def delete_product(self, product_id):
        self.cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.connection.commit()
    
    def get_user_orders(self, user_id):
        return self.cursor.execute('''
            SELECT orders.order_id, products.name, products.price, orders.date, orders.status
            FROM orders
            JOIN products ON orders.product_id = products.id
            WHERE orders.user_id = ?
            ORDER BY orders.date DESC
        ''', (user_id,)).fetchall() 
    
    def add_created_bot(self, creator_id, bot_username, token):
        self.cursor.execute(
            'INSERT INTO created_bots (creator_id, bot_username, token) VALUES (?, ?, ?)',
            (creator_id, bot_username, token)
        )
        self.connection.commit() 