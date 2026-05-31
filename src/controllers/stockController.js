const { getPool, sql } = require('../db/database');

const getAllStocks = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query(`
      SELECT s.*, f.name AS farmer_name, f.village AS farmer_village
      FROM Stocks s
      LEFT JOIN Farmers f ON s.farmer_id = f.id
      ORDER BY s.created_at DESC
    `);
    res.json({ success: true, data: result.recordset, count: result.recordset.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getStockById = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query(`
        SELECT s.*, f.name AS farmer_name, f.village AS farmer_village
        FROM Stocks s
        LEFT JOIN Farmers f ON s.farmer_id = f.id
        WHERE s.id = @id
      `);
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Stock not found' });
    }
    res.json({ success: true, data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const createStock = async (req, res) => {
  try {
    const { vegetable, quantity, unit, price_per_unit, farmer_id, purchase_date, notes } = req.body;
    if (!vegetable || !quantity || !price_per_unit) {
      return res.status(400).json({ success: false, message: 'Vegetable, quantity, and price are required' });
    }
    const pool = await getPool();
    const result = await pool.request()
      .input('vegetable', sql.NVarChar, vegetable)
      .input('quantity', sql.Decimal(10, 2), quantity)
      .input('unit', sql.NVarChar, unit || 'kg')
      .input('price_per_unit', sql.Decimal(10, 2), price_per_unit)
      .input('farmer_id', sql.Int, farmer_id || null)
      .input('purchase_date', sql.Date, purchase_date || new Date())
      .input('notes', sql.NVarChar, notes || '')
      .query(`
        INSERT INTO Stocks (vegetable, quantity, unit, price_per_unit, farmer_id, purchase_date, notes)
        OUTPUT INSERTED.*
        VALUES (@vegetable, @quantity, @unit, @price_per_unit, @farmer_id, @purchase_date, @notes)
      `);
    res.status(201).json({ success: true, message: 'Stock added successfully', data: result.recordset[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const updateStock = async (req, res) => {
  try {
    const { vegetable, quantity, unit, price_per_unit, farmer_id, purchase_date, notes } = req.body;
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .input('vegetable', sql.NVarChar, vegetable)
      .input('quantity', sql.Decimal(10, 2), quantity)
      .input('unit', sql.NVarChar, unit)
      .input('price_per_unit', sql.Decimal(10, 2), price_per_unit)
      .input('farmer_id', sql.Int, farmer_id || null)
      .input('purchase_date', sql.Date, purchase_date)
      .input('notes', sql.NVarChar, notes)
      .query(`
        UPDATE Stocks
        SET vegetable=@vegetable, quantity=@quantity, unit=@unit,
            price_per_unit=@price_per_unit, farmer_id=@farmer_id,
            purchase_date=@purchase_date, notes=@notes, updated_at=GETDATE()
        OUTPUT INSERTED.*
        WHERE id = @id
      `);
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Stock not found' });
    }
    res.json({ success: true, message: 'Stock updated successfully', data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const deleteStock = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request()
      .input('id', sql.Int, req.params.id)
      .query('DELETE FROM Stocks OUTPUT DELETED.id WHERE id = @id');
    if (result.recordset.length === 0) {
      return res.status(404).json({ success: false, message: 'Stock not found' });
    }
    res.json({ success: true, message: 'Stock deleted successfully' });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

const getStockSummary = async (req, res) => {
  try {
    const pool = await getPool();
    const result = await pool.request().query(`
      SELECT 
        COUNT(*) AS total_items,
        SUM(quantity) AS total_quantity,
        SUM(quantity * price_per_unit) AS total_value,
        COUNT(DISTINCT vegetable) AS unique_vegetables
      FROM Stocks
    `);
    res.json({ success: true, data: result.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, message: 'Server error' });
  }
};

module.exports = { getAllStocks, getStockById, createStock, updateStock, deleteStock, getStockSummary };
