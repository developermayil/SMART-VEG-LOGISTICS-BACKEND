const { getPool } = require('../db/database');

const getDashboardStats = async (req, res) => {
  try {
    const pool = await getPool();

    const [stocks, farmers, vehicles, deliveries] = await Promise.all([
      pool.request().query(`
        SELECT COUNT(*) AS total_items, COALESCE(SUM(quantity), 0) AS total_quantity,
               COALESCE(SUM(quantity * price_per_unit), 0) AS total_stock_value
        FROM Stocks
      `),
      pool.request().query('SELECT COUNT(*) AS total_farmers FROM Farmers'),
      pool.request().query(`
        SELECT COUNT(*) AS total_vehicles,
               SUM(CASE WHEN status='available' THEN 1 ELSE 0 END) AS available,
               SUM(CASE WHEN status='in-transit' THEN 1 ELSE 0 END) AS in_transit
        FROM Vehicles
      `),
      pool.request().query(`
        SELECT COUNT(*) AS total_deliveries,
               SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN status='in-transit' THEN 1 ELSE 0 END) AS active,
               COALESCE(SUM(CASE WHEN status='delivered' THEN total_value ELSE 0 END), 0) AS revenue
        FROM Deliveries
      `)
    ]);

    // Recent deliveries
    const recentDeliveries = await pool.request().query(`
      SELECT TOP 5 d.delivery_number, d.destination, d.status, d.total_value, d.scheduled_date,
             v.vehicle_number, v.driver_name
      FROM Deliveries d
      LEFT JOIN Vehicles v ON d.vehicle_id = v.id
      ORDER BY d.created_at DESC
    `);

    // Stock by vegetable
    const stockByVeg = await pool.request().query(`
      SELECT vegetable, SUM(quantity) AS total_quantity, AVG(price_per_unit) AS avg_price
      FROM Stocks
      GROUP BY vegetable
      ORDER BY total_quantity DESC
    `);

    res.json({
      success: true,
      data: {
        stocks: stocks.recordset[0],
        farmers: farmers.recordset[0],
        vehicles: vehicles.recordset[0],
        deliveries: deliveries.recordset[0],
        recent_deliveries: recentDeliveries.recordset,
        stock_by_vegetable: stockByVeg.recordset
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getDashboardStats };
