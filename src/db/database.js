const sql = require('mssql');

const config = {
  server: process.env.DB_SERVER || 'localhost',
  port: parseInt(process.env.DB_PORT) || 1433,
  database: process.env.DB_DATABASE || 'SmartVegLogistics',
  user: process.env.DB_USER || 'sa',
  password: process.env.DB_PASSWORD || '',
  options: {
    encrypt: process.env.DB_ENCRYPT === 'true',
    trustServerCertificate: process.env.DB_TRUST_SERVER_CERTIFICATE !== 'false',
    enableArithAbort: true,
  },
  pool: {
    max: 10,
    min: 0,
    idleTimeoutMillis: 30000,
  },
};

let pool = null;

const getPool = async () => {
  if (!pool) {
    pool = await sql.connect(config);
    console.log('✅ SQL Server connected successfully');
  }
  return pool;
};

const initializeDatabase = async () => {
  const pool = await getPool();

  // Users table
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
    CREATE TABLE Users (
      id INT IDENTITY(1,1) PRIMARY KEY,
      username NVARCHAR(100) NOT NULL UNIQUE,
      email NVARCHAR(255) NOT NULL UNIQUE,
      password NVARCHAR(255) NOT NULL,
      role NVARCHAR(50) DEFAULT 'admin',
      created_at DATETIME DEFAULT GETDATE()
    )
  `);

  // Farmers table
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Farmers' AND xtype='U')
    CREATE TABLE Farmers (
      id INT IDENTITY(1,1) PRIMARY KEY,
      name NVARCHAR(200) NOT NULL,
      village NVARCHAR(200) NOT NULL,
      district NVARCHAR(200) DEFAULT 'Tamil Nadu',
      phone NVARCHAR(20) NOT NULL,
      alternate_phone NVARCHAR(20),
      email NVARCHAR(255),
      bank_account NVARCHAR(50),
      ifsc_code NVARCHAR(20),
      created_at DATETIME DEFAULT GETDATE(),
      updated_at DATETIME DEFAULT GETDATE()
    )
  `);

  // Vehicles table
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Vehicles' AND xtype='U')
    CREATE TABLE Vehicles (
      id INT IDENTITY(1,1) PRIMARY KEY,
      vehicle_number NVARCHAR(50) NOT NULL UNIQUE,
      vehicle_type NVARCHAR(100) DEFAULT 'Truck',
      driver_name NVARCHAR(200) NOT NULL,
      driver_phone NVARCHAR(20) NOT NULL,
      driver_license NVARCHAR(50),
      capacity DECIMAL(10,2) NOT NULL,
      status NVARCHAR(50) DEFAULT 'available',
      created_at DATETIME DEFAULT GETDATE(),
      updated_at DATETIME DEFAULT GETDATE()
    )
  `);

  // Stocks table
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Stocks' AND xtype='U')
    CREATE TABLE Stocks (
      id INT IDENTITY(1,1) PRIMARY KEY,
      vegetable NVARCHAR(200) NOT NULL,
      quantity DECIMAL(10,2) NOT NULL,
      unit NVARCHAR(20) DEFAULT 'kg',
      price_per_unit DECIMAL(10,2) NOT NULL,
      farmer_id INT FOREIGN KEY REFERENCES Farmers(id),
      purchase_date DATE DEFAULT GETDATE(),
      notes NVARCHAR(500),
      created_at DATETIME DEFAULT GETDATE(),
      updated_at DATETIME DEFAULT GETDATE()
    )
  `);

  // Deliveries table
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Deliveries' AND xtype='U')
    CREATE TABLE Deliveries (
      id INT IDENTITY(1,1) PRIMARY KEY,
      delivery_number NVARCHAR(50) NOT NULL UNIQUE,
      vehicle_id INT FOREIGN KEY REFERENCES Vehicles(id),
      destination NVARCHAR(300) NOT NULL,
      destination_market NVARCHAR(200),
      total_quantity DECIMAL(10,2),
      total_value DECIMAL(12,2),
      status NVARCHAR(50) DEFAULT 'pending',
      scheduled_date DATETIME,
      delivered_date DATETIME,
      driver_notes NVARCHAR(500),
      created_at DATETIME DEFAULT GETDATE(),
      updated_at DATETIME DEFAULT GETDATE()
    )
  `);

  // Delivery Items table (stocks in a delivery)
  await pool.request().query(`
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DeliveryItems' AND xtype='U')
    CREATE TABLE DeliveryItems (
      id INT IDENTITY(1,1) PRIMARY KEY,
      delivery_id INT FOREIGN KEY REFERENCES Deliveries(id),
      stock_id INT FOREIGN KEY REFERENCES Stocks(id),
      quantity DECIMAL(10,2) NOT NULL,
      price_per_unit DECIMAL(10,2) NOT NULL,
      selling_price DECIMAL(10,2),
      created_at DATETIME DEFAULT GETDATE()
    )
  `);

  console.log('✅ Database tables initialized');
};

module.exports = { getPool, initializeDatabase, sql };
